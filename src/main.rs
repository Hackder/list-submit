use std::path::{Path, PathBuf};

use args::ListSubmitArgs;
use clap::Parser;
use colored::Colorize;
use config::GlobalConfig;
use inquire::{Confirm, MultiSelect, Password, Select, Text};
use list_api::api::{ListApiClient, ListApiError};
use self_update::cargo_crate_version;

use crate::{
    args::ListSubmitCommand,
    config::{AuthConfig, ProjectConfig},
};

mod args;
mod config;
mod detectors;
mod list_api;
mod ui;

fn main() -> eyre::Result<()> {
    color_eyre::install()?;
    let args = ListSubmitArgs::parse();

    eprintln!(
        "{} {}",
        "List Submit CLI".green(),
        env!("CARGO_PKG_VERSION").bold()
    );

    let config = match GlobalConfig::load()? {
        Some(config) => config,
        None => {
            let cfg = GlobalConfig::default();
            cfg.save()?;
            cfg
        }
    };

    if let Some(ListSubmitCommand::Update) = &args.subcommand {
        let status = self_update::backends::github::Update::configure()
            .repo_owner("Hackder")
            .repo_name("list-submit")
            .bin_name("list-submit")
            .current_version(cargo_crate_version!())
            .show_download_progress(true)
            .build()?
            .update()?;

        if status.updated() {
            eprintln!("{} {}", "Updated to version: ".green(), status.version());
        } else {
            eprintln!("{}", "No update available".yellow());
        }
        std::process::exit(0);
    }

    let cwd = std::env::current_dir()?;
    let project_config_path = match &args.project {
        Some(project) => ProjectConfig::find_project_config_down(cwd.as_path(), project)?,
        None => ProjectConfig::find_project_config_up(cwd.as_path())?,
    };

    let project_config_dir = project_config_path
        .clone()
        .unwrap_or_else(|| cwd.join("list-submit.toml"));
    let project_config_dir = project_config_dir.parent().unwrap();

    let mut client = None;
    let (mut project_config, real_project_config_path) = match &project_config_path {
        Some(path) => (ProjectConfig::load(path)?, path.clone()),
        None => {
            eprintln!(
                "{}",
                "No project found, creating new one in this directory".yellow()
            );
            client = Some(create_client(&config, &args)?);

            create_project_config(client.as_ref().expect("client must exist"), &cwd)?
        }
    };

    match &args.subcommand {
        Some(ListSubmitCommand::Add(add)) => {
            match add.files.as_slice() {
                [] => {
                    project_config.add_files_from(cwd.as_path(), project_config_dir)?;
                }
                [dir] if Path::new(&dir).is_dir() => {
                    let dir = cwd.join(dir).canonicalize()?;
                    project_config.add_files_from(Path::new(&dir), project_config_dir)?;
                }
                files => {
                    let real_files = files
                        .iter()
                        .filter(|file| cwd.join(file).is_file())
                        .cloned();

                    project_config.add_files(real_files);
                }
            }

            project_config.save(real_project_config_path.as_path())?;
            std::process::exit(0);
        }
        Some(ListSubmitCommand::Files) => {
            if project_config.problem.files.is_empty() {
                eprintln!("{}", "No files present in the project configuration".red());
                std::process::exit(1);
            }
            project_config.files_menu_interactive()?;
            project_config.save(real_project_config_path.as_path())?;
            std::process::exit(0);
        }
        Some(ListSubmitCommand::Clean) => {
            let cleaned = project_config.clean_files(project_config_dir)?;
            eprintln!("{} {} files", "Cleaned".green(), cleaned.to_string().bold());
            project_config.save(real_project_config_path.as_path())?;
            std::process::exit(0);
        }
        Some(ListSubmitCommand::Auth) | Some(ListSubmitCommand::Update) => {
            return Err(eyre::eyre!("Auth command should not be called here"));
        }
        Some(ListSubmitCommand::Submit) | None => {}
    }

    if project_config_path.is_none() {
        if project_config.problem.files.is_empty() {
            std::process::exit(0);
        }

        let submit_now = Confirm::new("Do you want to submit the project now?")
            .with_default(true)
            .prompt()?;

        if !submit_now {
            std::process::exit(0);
        }
    }

    if project_config.problem.files.is_empty() {
        eprintln!("{}", "No files present in the project configuration".red());
        std::process::exit(1);
    }

    let client = match client {
        Some(client) => client,
        None => create_client(&config, &args)?,
    };

    let mut buf = Vec::new();
    {
        let mut zip = zip::ZipWriter::new(std::io::Cursor::new(&mut buf));
        let options =
            zip::write::FileOptions::default().compression_method(zip::CompressionMethod::Stored);
        for file in project_config.problem.files {
            eprintln!("Adding file: {}", file);
            let path = project_config_dir.join(file);
            let file_name = path.file_name().unwrap().to_str().unwrap();
            zip.start_file(file_name, options)?;

            let mut file = std::fs::File::open(path)?;
            std::io::copy(&mut file, &mut zip)?;
        }
        zip.finish()?;
    }

    let submit = ui::show_request("submit", || {
        client.submit_solution(project_config.problem.problem_id, buf)
    })?;

    let run_tests_result = ui::show_request("run tests", || {
        let res = client.run_test_for_submit(project_config.problem.problem_id, submit.version);
        match res {
            Ok(_) => Ok(Some(())),
            Err(ListApiError::TestNotSupported) => Ok(None),
            Err(err) => Err(err),
        }
    })?;

    if let None = run_tests_result {
        eprintln!("{}", "Tests are not supported for this problem".yellow());
        return Ok(());
    }

    let result_id = ui::show_request("results", || -> eyre::Result<u32> {
        let now = chrono::Utc::now().naive_local();
        let form = client.get_submit_form(project_config.problem.problem_id)?;

        let form = match form {
            Some(form) => form,
            None => return Err(eyre::eyre!("Tests are not supported for this problem")),
        };

        loop {
            let queue = client
                .get_student_test_queue(project_config.problem.problem_id, form.student_id)?;

            let new = queue
                .iter()
                .filter(|test| test.start_time > now)
                .max_by_key(|test| test.start_time);
            let new = match new {
                Some(new) => new,
                None => {
                    std::thread::sleep(std::time::Duration::from_millis(500));
                    continue;
                }
            };

            if new.end_time.is_some() {
                break Ok(new.id);
            }
        }
    })?;

    let result = ui::show_request("result", || client.get_test_result(result_id))?;

    for problem in result.problems.iter() {
        if problem.percentage >= 100.0 {
            eprintln!(
                "{} {}",
                problem.name.truecolor(128, 128, 128),
                "ran successfully".truecolor(128, 128, 128).bold()
            );
            continue;
        }
        eprintln!("{} {}", problem.name.red().bold(), "failed".red());
        eprintln!("{}", problem.output.red());
    }

    eprintln!();
    let max_len = result
        .problems
        .iter()
        .map(|p| p.name.len() + 5)
        .max()
        .unwrap_or(0);

    for problem in result.problems.iter() {
        eprintln!(
            "{: <width$} => points: {},  {}%",
            problem.name.bold(),
            problem.points.to_string().bold(),
            problem.percentage.to_string().bold(),
            width = max_len
        );
    }
    eprintln!("Total points: {}", result.total_points().to_string().bold());

    Ok(())
}

pub fn create_client(config: &GlobalConfig, args: &ListSubmitArgs) -> eyre::Result<ListApiClient> {
    let mut failed = false;

    loop {
        let auth = match (config.auth.clone(), args.subcommand.clone(), failed) {
            (None, _, _) | (_, Some(ListSubmitCommand::Auth), _) | (_, _, true) => {
                let email = Text::new("Enter your email").prompt()?;
                let password = Password::new("Enter your password")
                    .without_confirmation()
                    .prompt()?;

                AuthConfig { email, password }
            }
            (Some(auth), _, _) => auth,
        };

        let client = ui::show_request("login", || {
            ListApiClient::new_with_credentials(&auth.email, &auth.password)
        });

        match client {
            Ok(client) => {
                let new_config = GlobalConfig {
                    auth: Some(auth),
                    ..config.clone()
                };

                if let Some(ListSubmitCommand::Auth) = args.subcommand {
                    new_config.save()?;
                } else if config.auth.is_none() {
                    let save_password = Confirm::new("Do you want to save your password?")
                        .with_default(true)
                        .prompt()?;

                    if save_password {
                        new_config.save()?;
                    }
                }

                return Ok(client);
            }
            Err(ListApiError::InvalidCredentials) => {
                eprintln!("{}", "Invalid credentials! Please try again".red());
                failed = true;
                continue;
            }
            Err(err) => return Err(err.into()),
        }
    }
}

pub fn create_project_config(
    client: &ListApiClient,
    cwd: &Path,
) -> eyre::Result<(ProjectConfig, PathBuf)> {
    let courses = ui::show_request("courses", || client.get_all_course())?;

    let course = Select::new("Select a course", courses).prompt()?;

    let problems = ui::show_request("problems", || client.get_problems_for_course(course.id))?;

    let problem = Select::new("Select a problem", problems).prompt()?;

    let detectors = detectors::get_detectors();

    let result = detectors
        .into_iter()
        .filter_map(|detector| {
            let res = match detector.detect(cwd) {
                Ok(res) => res,
                Err(err) => {
                    log::error!("Error while detecting: {}", err);
                    return None;
                }
            };

            Some((res, detector))
        })
        .filter(|(res, _)| res.probability > 0.0)
        .max_by_key(|(res, _)| (res.probability * 1000.0) as i32);

    let files = match result {
        Some((res, detector)) => {
            eprintln!();
            eprintln!(
                "{} {} {}",
                "Detected".green(),
                detector.name().bold(),
                format!("with probability: {:.0}%", res.probability * 100.0).bold()
            );

            for recom in res.recommendations {
                eprintln!("{}: {}", "Recommendation:".yellow(), recom);
            }

            res.files
        }
        None => {
            eprintln!("{}", "Could not detect project automatically.".yellow());
            eprintln!("{}", "Add files using the `add` subcommand!".yellow());
            vec![]
        }
    };

    let files = files
        .into_iter()
        .map(|p| p.to_string_lossy().to_string())
        .collect::<Vec<_>>();

    let files = if !files.is_empty() {
        MultiSelect::new("Select autodetected files to keep", files)
            .with_all_selected_by_default()
            .prompt()?
    } else {
        files
    };

    let (project_config, path) = ProjectConfig::create(
        std::env::current_dir()?.as_path(),
        course.id,
        problem.id,
        &problem.name,
        &files,
    )?;

    Ok((project_config, path))
}
