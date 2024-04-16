use scraper::Selector;

use super::models::{Course, Problem, Submit, SubmitForm, Test, TestResult, TestResultProblem};

#[derive(Debug)]
pub enum ListParserError {
    ParseError(String),
}

pub fn parse_all_courses(html: &str) -> Result<Vec<Course>, ListParserError> {
    let document = scraper::Html::parse_document(html);

    let courses_selector = Selector::parse("div.period_course").expect("valid selector");
    let course_elements = document.select(&courses_selector);

    let mut courses = Vec::new();
    for element in course_elements {
        let name_h4 = element
            .select(&Selector::parse("h4").expect("valid selector"))
            .next();

        let name = match name_h4 {
            Some(name_h4) => name_h4.text().collect::<String>(),
            None => {
                log::debug!("Failed to parse course name. No h4 found. Skipping course.");
                continue;
            }
        };

        let anchors = element
            .select(&Selector::parse("a").expect("valid selector"))
            .collect::<Vec<_>>();

        if anchors.is_empty() {
            log::debug!(
                "Failed to parse course id: {}. No anchors found. Skipping course.",
                name
            );
            continue;
        }

        let anchor = anchors.last().unwrap();

        if anchor.text().collect::<String>() != "Zobraz detaily" {
            log::debug!(
                "Failed to parse course id: {}. 'Zobraz detaily' is not present in the anchor text: '{}'",
                name,
                anchor.text().collect::<String>()
            );

            return Err(ListParserError::ParseError(
                "'Zobraz detaily' missing in course element".to_owned(),
            ));
        }

        let href = anchor.value().attr("href").unwrap();

        // TODO: Handle errors
        let id = href
            .split('/')
            .last()
            .unwrap()
            .split('.')
            .next()
            .unwrap()
            .parse()
            .unwrap();

        courses.push(Course { id, name });
    }

    Ok(courses)
}

pub fn parse_problems(html: &str) -> Result<Vec<Problem>, ListParserError> {
    let document = scraper::Html::parse_document(html);

    let problem_elements = document
        .select(&Selector::parse("td.td_name").expect("valid selector"))
        .collect::<Vec<_>>();

    let problems = problem_elements
        .iter()
        .map(|element| {
            let anchor = element
                .select(&Selector::parse("a").expect("valid selector"))
                .next()
                .unwrap();

            // TODO: Handle errors
            let href = anchor.value().attr("href").unwrap();
            let full_id = href.split('/').last().unwrap().split('.').next().unwrap();
            let id: u32 = full_id.split('_').next().unwrap().parse().unwrap();

            let name = anchor.text().collect::<String>();

            Problem {
                id,
                full_id: full_id.to_owned(),
                name,
            }
        })
        .collect::<Vec<_>>();

    log::debug!(
        "Attempted to parse {}. {} problems parsed.",
        problem_elements.len(),
        problems.len()
    );

    Ok(problems)
}

pub fn parse_submits(html: &str, problem_id: u32) -> Result<Vec<Submit>, ListParserError> {
    let document = scraper::Html::parse_document(html);

    let submit_elements = document
        .select(&Selector::parse("table.solutions_table tr").expect("valid selector"))
        .collect::<Vec<_>>();

    let submits = submit_elements
        .iter()
        .map(|element| {
            let input = element
                .select(&Selector::parse("input").expect("valid selector"))
                .next()
                .unwrap();

            let version = input.value().attr("value").unwrap().parse().unwrap();

            let td = element
                .select(&Selector::parse("td.file").expect("valid selector"))
                .next()
                .unwrap();

            let a = td
                .select(&Selector::parse("a").expect("valid selector"))
                .next()
                .unwrap();

            let href = a.value().attr("href").unwrap();
            let id = href.split('/').last().unwrap().split('.').next().unwrap();

            let name = a.text().collect::<String>();

            Submit {
                id: id.to_owned(),
                problem_id,
                version,
                name,
            }
        })
        .collect::<Vec<_>>();

    log::debug!(
        "Attempted to parse {}. {} submits parsed.",
        submit_elements.len(),
        submits.len()
    );

    Ok(submits)
}

pub fn parse_submit_form(html: &str) -> Result<SubmitForm, ListParserError> {
    let document = scraper::Html::parse_document(html);

    let tests = document
        .select(&Selector::parse("input[name=\"test[id][]\"]").expect("valid selector"))
        .filter_map(|input| input.value().attr("value"))
        .map(|value| value.to_owned())
        .collect::<Vec<_>>();

    let task_set_id = document
        .select(&Selector::parse("input[name=\"test[task_set_id]\"]").expect("valid selector"))
        .next()
        .unwrap()
        .value()
        .attr("value")
        .unwrap()
        .to_owned();

    let student_id: u32 = document
        .select(&Selector::parse("input[name=\"test[student_id]\"]").expect("valid selector"))
        .next()
        .unwrap()
        .value()
        .attr("value")
        .unwrap()
        .parse()
        .unwrap();

    let select_test_type = document
        .select(&Selector::parse("input[name=\"select_test_type\"]").expect("valid selector"))
        .next()
        .unwrap()
        .value()
        .attr("value")
        .unwrap()
        .to_owned();

    Ok(SubmitForm {
        tests,
        task_set_id,
        student_id,
        select_test_type,
    })
}

pub fn parse_test_queue(html: &str) -> Result<Vec<Test>, ListParserError> {
    let document = scraper::Html::parse_document(html);

    let test_elements = document
        .select(&Selector::parse("tbody tr").expect("valid selector"))
        .collect::<Vec<_>>();

    let tests = test_elements
        .iter()
        .map(|element| {
            let id_element = element
                .select(&Selector::parse("td > a").expect("valid selector"))
                .next()
                .unwrap();

            let href = id_element.value().attr("href").unwrap();
            let id = href.split('/').last().unwrap().split('.').next().unwrap().parse().unwrap();

            let cols = element
                .select(&Selector::parse("td").expect("valid selector"))
                .collect::<Vec<_>>();

            let start_time_el = cols.get(2).unwrap();
            let start_time = start_time_el.text().collect::<String>();

            let start_time = chrono::NaiveDateTime::parse_from_str(&start_time, "%d.%m.%Y %H:%M:%S")
                .unwrap();

            let end_time_el = cols.get(3).unwrap();
            let end_time = end_time_el.text().collect::<String>();

            let end_time = if end_time == "Ešte neukončené!" {
                None
            } else {
                Some(
                    chrono::NaiveDateTime::parse_from_str(&end_time, "%d.%m.%Y %H:%M:%S")
                        .unwrap(),
                )
            };

            Test {
                id,
                start_time,
                end_time,
            }
        })
        .collect::<Vec<_>>();

    log::debug!(
        "Attempted to parse {}. {} tests parsed.",
        test_elements.len(),
        tests.len()
    );

    Ok(tests)
}

pub fn parse_test_result(html: &str) -> Result<TestResult, ListParserError> {
    let document = scraper::Html::parse_document(html);
    let total_points = document
        .select(&Selector::parse("table.tests_result_sum_table > tbody > tr:nth-child(4) > td").unwrap())
        .next()
        .unwrap()
        .text()
        .collect::<String>()
        .trim()
        .parse()
        .unwrap();

    let problem_elements = document
        .select(&Selector::parse("table.tests_evaluation_table > tbody > tr").unwrap())
        .collect::<Vec<_>>();

    let output_elements = document
        .select(&Selector::parse("fieldset pre").unwrap())
        .collect::<Vec<_>>();

    let problems = problem_elements
        .iter()
        .zip(output_elements.iter())
        .map(|(problem_element, output_element)| {
            let items = problem_element
                .select(&Selector::parse("td").unwrap())
                .collect::<Vec<_>>();

            let name = items.get(0).unwrap().text().collect::<String>().trim().to_owned();
            let percentage = items
                .get(1)
                .unwrap()
                .text()
                .collect::<String>()
                .trim()
                .strip_suffix('%')
                .unwrap()
                .parse()
                .unwrap();
            let points = items.get(2).unwrap().text().collect::<String>().trim().parse().unwrap();

            let output = output_element.text().collect::<String>().trim().to_owned();

            TestResultProblem {
                name,
                percentage,
                points,
                output,
            }
        })
        .collect::<Vec<_>>();

    Ok(TestResult {
        total_points,
        problems,
    })
}
