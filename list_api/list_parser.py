from dataclasses import dataclass
from datetime import datetime
import logging
from bs4 import BeautifulSoup, Tag

from list_api.models import (
    Course,
    Problem,
    Submit,
    Test,
    SubmitForm,
    TestResult,
    TestResultProblem,
)

logger = logging.getLogger(__name__)


class ListParserError(Exception):
    pass


def get_all_courses(html: str) -> list[Course]:
    soup = BeautifulSoup(html, "html.parser")
    course_elements = soup.find_all("div", class_="period_course")

    def create_course(element) -> Course | None:
        name_h4 = element.find("h4")

        if name_h4 is None:
            logger.debug("Failed to parse course name. No h4 found. Skipping course.")
            return None

        name = name_h4.text or "Empty name"

        anchors = element.find_all("a")

        if len(anchors) == 0:
            logger.debug(
                f"Failed to parse course id: {name}. No anchors found. Skipping course."
            )
            return None

        anchor = anchors[-1]

        if anchor.text != "Zobraz detaily":
            raise ListParserError(
                f"Failed to parse course id: {name}. 'Zobraz detaily' is not present in the anchor text: '{anchor.text}'"
            )

        href = anchor.get("href")

        if href is None:
            logger.debug(
                f"Failed to parse course id: {name}. No href found. Skipping course."
            )
            return None

        # TODO: Handle errors
        id = href.split("/")[-1].split(".")[0]
        id = int(id)

        return Course(id=id, name=name)

    len_before = len(course_elements)
    courses = map(create_course, course_elements)
    courses = [c for c in courses if c is not None]
    len_after = len(courses)

    logger.debug(
        f"Attempted to parse {len_before} courses. {len_after} courses parsed."
    )

    return courses


def get_problems(html: str) -> list[Problem]:
    soup = BeautifulSoup(html, "html.parser")

    problem_elements = soup.find_all("td", class_="td_name")

    def parse_problem(element) -> Problem:
        anchor = element.find("a")

        href = anchor.get("href")

        # TODO: Handle errors
        full_id = href.split("/")[-1].split(".")[0]
        id = int(full_id.split("_")[0])
        name = anchor.text

        return Problem(id=id, full_id=full_id, name=name)

    len_before = len(problem_elements)
    problems = map(parse_problem, problem_elements)
    problems = list(problems)
    len_after = len(problems)

    logger.debug(
        f"Attempted to parse {len_before} problems. {len_after} problems parsed."
    )

    return problems


def get_submits(html: str, problem_id: int) -> list[Submit]:
    soup = BeautifulSoup(html, "html.parser")
    submits_elements = soup.select("table.solutions_table tr")

    def parse_submit(element: Tag) -> Submit | None:
        input = element.find("input")

        if input is None:
            logger.debug("Failed to parse submit. No input found. Skipping submit.")
            return None

        assert isinstance(input, Tag)
        version = input.get("value")
        version = int(str(version))

        td = element.find_next("td", class_="file")
        assert isinstance(td, Tag)

        a = td.find("a")
        assert isinstance(a, Tag)

        href = a.get("href")
        id = str(href).split("/")[-1].split(".")[0]

        name = a.text

        return Submit(id=id, version=version, name=name, problem_id=problem_id)

    len_before = len(submits_elements)
    submits = map(parse_submit, submits_elements)
    submits = [s for s in submits if s is not None]
    len_after = len(submits)

    logger.debug(
        f"Attempted to parse {len_before} submits. {len_after} submits parsed."
    )

    return submits


def get_submit_form(html: str) -> SubmitForm | None:
    soup = BeautifulSoup(html, "html.parser")

    tests = soup.select('input[name="test[id][]"]')
    tests = [str(t.get("value")) for t in tests if t.get("value") is not None]

    task_set_id = soup.select_one('input[name="test[task_set_id]"]')
    if task_set_id is None:
        return None
    task_set_id = task_set_id.get("value")
    assert task_set_id is not None

    student_id = soup.select_one('input[name="test[student_id]"]')
    assert student_id is not None
    student_id = student_id.get("value")
    assert student_id is not None

    select_test_type = soup.select_one('input[name="select_test_type"]')
    assert select_test_type is not None
    select_test_type = select_test_type.get("value")
    assert select_test_type is not None

    return SubmitForm(
        tests=tests,
        task_set_id=str(task_set_id),
        student_id=str(student_id),
        select_test_type=str(select_test_type),
    )


def get_test_queue(html: str) -> list[Test]:
    soup = BeautifulSoup(html, "html.parser")
    test_elements = soup.select("tbody tr")
    if len(test_elements) == 0:
        return []

    def parse_test(element) -> Test:
        id_element = element.select_one("td > a")
        # Grab the id from the last part of the URL (...asdf/123.html)
        href = id_element.get("href")
        id = int(href.split("/")[-1][:-5])

        cols = element.find_all("td")
        start_time_el = cols[2]
        start_time = start_time_el.text
        start_time = datetime.strptime(start_time, "%d.%m.%Y %H:%M:%S")

        end_time_el = cols[3]
        if end_time_el.text == "Ešte neukončené!":
            end_time = None
        else:
            end_time = end_time_el.text
            end_time = datetime.strptime(end_time, "%d.%m.%Y %H:%M:%S")

        return Test(id=id, start_time=start_time, end_time=end_time)

    return [parse_test(e) for e in test_elements]


def get_test_result(html: str) -> TestResult:
    soup = BeautifulSoup(html, "html.parser")
    total_points = soup.select_one(
        "table.tests_result_sum_table > tbody > tr:nth-child(4) > td"
    )
    if total_points is None:
        raise ListParserError("Failed to parse total points")
    total_points = float(total_points.text.strip())

    problem_elements = soup.select("table.tests_evaluation_table > tbody > tr")

    def parse_problem_result(element) -> TestResultProblem:
        items = element.find_all("td")
        name = items[0].text.strip()
        percentage = float(items[1].text.strip()[0:-1])
        points = float(items[2].text.strip())

        return TestResultProblem(name=name, percentage=percentage, points=points)

    problmes = [parse_problem_result(e) for e in problem_elements]

    return TestResult(total_points=total_points, problems=problmes)
