use crate::list_api::parser;
use reqwest::blocking::multipart::{Form, Part};
use reqwest::blocking::Client;
use serde::Deserialize;

use super::models::{Course, Problem, Submit, SubmitForm, Test, TestResult};

const LIST_URL: &str = "https://list.fmph.uniba.sk";

pub struct ListApiClient {
    client: Client,
    base_url: String,
}

#[derive(Debug)]
pub enum ListApiError {
    HttpError(reqwest::Error),
    ParseError(parser::ListParserError),
    LoginFailed(String),
}

impl From<reqwest::Error> for ListApiError {
    fn from(error: reqwest::Error) -> Self {
        ListApiError::HttpError(error)
    }
}

impl From<parser::ListParserError> for ListApiError {
    fn from(error: parser::ListParserError) -> Self {
        ListApiError::ParseError(error)
    }
}

impl ListApiClient {
    pub fn new_with_credentials(email: &str, password: &str) -> Result<Self, ListApiError> {
        let client = Client::builder().cookie_store(true).build()?;

        let response = client
            .post(&format!("{}/students/do_login.html", LIST_URL))
            .form(&[
                ("student[email]", email),
                ("student[password]", password),
                ("button_submit", "Prihlás ma"),
            ])
            .send()?;

        let cookie = response.cookies().find(|c| c.name() == "list_session");
        if cookie.is_none() {
            return Err(ListApiError::LoginFailed(
                "Failed to obtain session cookie".to_owned(),
            ));
        }

        let logged_in = response.text()?.contains("Môj účet");
        if !logged_in {
            return Err(ListApiError::LoginFailed("Failed to log in".to_owned()));
        }

        Ok(Self {
            client,
            base_url: LIST_URL.to_owned(),
        })
    }

    pub fn get_all_course(&self) -> Result<Vec<Course>, ListApiError> {
        let response = self
            .client
            .get(&format!("{}/courses.html", self.base_url))
            .send()?;
        let text = response.text()?;
        let courses = parser::parse_all_courses(&text)?;
        Ok(courses)
    }

    pub fn mark_course_active(&self, course_id: u32) -> Result<(), ListApiError> {
        let response = self
            .client
            .get(&format!(
                "{}/courses/activate_course/{}.html",
                self.base_url, course_id
            ))
            .send()?;

        #[derive(Deserialize)]
        struct Response {
            status: bool,
        }

        let body: Response = response.json()?;

        if !body.status {
            return Err(ListApiError::LoginFailed(
                "Failed to mark course as active".to_owned(),
            ));
        }
        Ok(())
    }

    pub fn get_problems_for_course(&self, course_id: u32) -> Result<Vec<Problem>, ListApiError> {
        self.mark_course_active(course_id)?;

        let response = self
            .client
            .get(&format!("{}/tasks.html", self.base_url))
            .send()?;
        let text = response.text()?;
        let problems = parser::parse_problems(&text)?;
        Ok(problems)
    }

    pub fn submit_solution(
        &self,
        problem_id: u32,
        solution_file: Vec<u8>,
    ) -> Result<Submit, ListApiError> {
        let file =
            Part::bytes(solution_file).file_name("solution.zip");

        let form = Form::new()
            .text("submit_button", "Odovzdať riešenie")
            .part("solution", file);

        let response = self
            .client
            .post(&format!(
                "{}/tasks/upload_solution/{}.html",
                self.base_url, problem_id
            ))
            .multipart(form)
            .send()?;

        let text = response.text()?;
        let submits = parser::parse_submits(&text, problem_id)?;
        Ok(submits.last().unwrap().clone())
    }

    pub fn get_submit_form(&self, problem_id: u32) -> Result<SubmitForm, ListApiError> {
        let response = self
            .client
            .get(&format!("{}/tasks/task/{}.html", self.base_url, problem_id))
            .send()?;
        let text = response.text()?;
        let form = parser::parse_submit_form(&text)?;
        Ok(form)
    }

    pub fn run_test_for_submit(
        &self,
        problem_id: u32,
        submit_version: u32,
    ) -> Result<(), ListApiError> {
        let form = self.get_submit_form(problem_id)?;

        let mut data = vec![
            ("test[task_set_id]", form.task_set_id),
            ("test[student_id]", form.student_id.to_string()),
            ("test[version]", submit_version.to_string()),
            ("select_test_type", form.select_test_type),
        ];
        data.extend(form.tests.into_iter().map(|test| ("test[id][]", test)));

        let response = self
            .client
            .post(&format!("{}/fetests/enqueue_test", self.base_url))
            .form(&data)
            .send()?;

        #[derive(Deserialize)]
        struct Response {
            status: bool,
        }

        let body: Response = response.json()?;

        if !body.status {
            return Err(ListApiError::LoginFailed(
                "Failed to parse response".to_owned(),
            ));
        }

        Ok(())
    }

    pub fn get_student_test_queue(
        &self,
        problem_id: u32,
        student_id: u32,
    ) -> Result<Vec<Test>, ListApiError> {
        let response = self
            .client
            .get(&format!(
                "{}/fetests/get_student_test_queue/{}/{}",
                self.base_url, problem_id, student_id
            ))
            .send()?;
        let text = response.text()?;
        let tests = parser::parse_test_queue(&text)?;
        Ok(tests)
    }

    pub fn get_test_result(&self, test_id: u32) -> Result<TestResult, ListApiError> {
        let response = self
            .client
            .get(&format!("{}/tasks/test_result/{}.html", self.base_url, test_id))
            .send()?;
        let text = response.text()?;
        let result = parser::parse_test_result(&text)?;
        Ok(result)
    }
}

// def get_student_test_queue(
//     session: ListSession, problem_id: int, student_id: int
// ) -> list[Test]:
//     response = session.session.get(
//         __url(f"/index.php/fetests/get_student_test_queue/{problem_id}/{student_id}")
//     )
//     return list_parser.get_test_queue(response.text)
//
//
// def get_test_result(session: ListSession, test_id: int) -> TestResult:
//     response = session.session.get(__url(f"/tasks/test_result/{test_id}.html"))
//     return list_parser.get_test_result(response.text)
//
