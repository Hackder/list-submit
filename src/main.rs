use std::path::{Path, PathBuf};

use args::ListSubmitArgs;
use clap::Parser;
use colored::Colorize;
use config::GlobalConfig;
use inquire::{Confirm, Password, Select, Text};
use list_api::api::{ListApiClient, ListApiError};

use crate::{
    args::ListSubmitCommand,
    config::{AuthConfig, ProjectConfig},
};

mod args;
mod config;
mod list_api;

fn main() -> eyre::Result<()> {
    color_eyre::install()?;
    let args = ListSubmitArgs::parse();

    eprintln!("{} {}", "List Submit CLI".green(), env!("CARGO_PKG_VERSION").bold());

    let config = match GlobalConfig::load()? {
        Some(config) => config,
        None => {
            let cfg = GlobalConfig::default();
            cfg.save()?;
            cfg
        }
    };

    let cwd = std::env::current_dir()?;
    let project_config_path = match &args.project {
        Some(project) => ProjectConfig::find_project_config_down(cwd.as_path(), &project)?,
        None => ProjectConfig::find_project_config_up(cwd.as_path())?,
    };

    let project_config_dir = project_config_path
        .clone()
        .unwrap_or_else(|| cwd.join("list-submit.toml"));
    let project_config_dir = project_config_dir.parent().unwrap();

    let mut client = None;
    let (mut project_config, real_project_config_path) = match project_config_path {
        Some(path) => (ProjectConfig::load(&path)?, path),
        None => {
            eprintln!("{}", "No project found, creating new one in this directory".yellow());
            client = Some(create_client(&config, &args)?);
            let result = create_project_config(client.as_ref().expect("client must exist"))?;
            result
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
                        .filter(|file| Path::new(file).is_file())
                        .map(|filepath| -> eyre::Result<PathBuf> {
                            let path = cwd.join(filepath).canonicalize()?;
                            Ok(path)
                        })
                        .filter_map(|value| match value {
                            Ok(path) => Some(path),
                            Err(err) => {
                                log::warn!("Failed to add file: {}", err);
                                None
                            }
                        });

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
        Some(ListSubmitCommand::Clean) => {}
        Some(ListSubmitCommand::Submit) | None => {}
        Some(ListSubmitCommand::Auth) => {
            return Err(eyre::eyre!("Auth command should not be called here"));
        }
    }

    let client = client.unwrap_or(create_client(&config, &args)?);

    let courses = client.get_all_course().unwrap();
    println!("{:#?}", courses);
    //
    // let problems = client.get_problems_for_course(courses.get(2).unwrap().id).unwrap();
    // println!("{:#?}", problems);
    //
    // // client.run_test_for_submit(5374, 10).unwrap();
    //
    // let submit_form = client.get_submit_form(5374).unwrap();
    // let queue = client.get_student_test_queue(5374, submit_form.student_id).unwrap();
    //
    // println!("{:#?}", queue);
    //
    // client.run_test_for_submit(5374, 10).unwrap();
    // let result = client.get_test_result(queue.get(0).unwrap().id).unwrap();
    //
    // println!("{:#?}", result);

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

        let client = ListApiClient::new_with_credentials(&auth.email, &auth.password);

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

pub fn create_project_config(client: &ListApiClient) -> eyre::Result<(ProjectConfig, PathBuf)> {
    let courses = client.get_all_course()?;

    let course = Select::new("Select a course", courses).prompt()?;

    let problems = client.get_problems_for_course(course.id)?;

    let problem = Select::new("Select a problem", problems).prompt()?;

    // TODO: Run detectors

    let (project_config, path) = ProjectConfig::create(
        std::env::current_dir()?.as_path(),
        course.id,
        problem.id,
        &problem.name,
        &vec![],
    )?;

    Ok((project_config, path))
}
