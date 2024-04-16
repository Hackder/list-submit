use args::ListSubmitArgs;
use clap::Parser;
use list_api::api::ListApiClient;

mod args;
mod list_api;

fn main() {
    // let args = ListSubmitArgs::parse();

    let client = ListApiClient::new_with_credentials("", "").unwrap();

    let courses = client.get_all_course().unwrap();
    println!("{:#?}", courses);

    let problems = client.get_problems_for_course(courses.get(2).unwrap().id).unwrap();
    println!("{:#?}", problems);

    // client.run_test_for_submit(5374, 10).unwrap();

    let submit_form = client.get_submit_form(5374).unwrap();
    let queue = client.get_student_test_queue(5374, submit_form.student_id).unwrap();

    println!("{:#?}", queue);

    client.run_test_for_submit(5374, 10).unwrap();
    let result = client.get_test_result(queue.get(0).unwrap().id).unwrap();

    println!("{:#?}", result);
}
