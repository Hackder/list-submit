use colored::Colorize;
use spinners::Spinner;

pub fn with_spinner<T>(msg: &str, task: impl FnOnce() -> T) -> T {
    let msg = msg.to_owned();
    let mut spinner = Spinner::new(spinners::Spinners::Arc, msg.clone());
    let result = task();
    spinner.stop_with_message(msg + " => done");

    result
}

pub fn show_request<T>(msg: &str, task: impl FnOnce() -> T) -> T {
    let msg = format!("{} {}", "Requesting".green(), msg);
    with_spinner(&msg, task)
}
