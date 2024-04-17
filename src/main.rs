use args::ListSubmitArgs;
use clap::Parser;
use colored::Colorize;
use config::GlobalConfig;
use inquire::{Confirm, Password, Text};
use list_api::api::{ListApiClient, ListApiError};

use crate::{args::ListSubmitCommand, config::AuthConfig};

mod args;
mod config;
mod list_api;

fn main() -> eyre::Result<()> {
    color_eyre::install()?;
    let args = ListSubmitArgs::parse();

    let config = match GlobalConfig::load()? {
        Some(config) => config,
        None => GlobalConfig::default(),
    };

    config.save()?;

    let mut failed = false;

    let (_config, client) = loop {
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
                    ..config
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

                break (new_config, client);
            }
            Err(ListApiError::InvalidCredentials) => {
                eprintln!("{}", "Invalid credentials! Please try again".red());
                failed = true;
                continue;
            }
            Err(err) => return Err(err.into()),
        }
    };

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
