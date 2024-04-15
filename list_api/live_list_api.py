import requests
from .models import Course, Problem, Submit, ListSession, Test, SubmitForm, TestResult
import logging

import out
from . import list_parser

logger = logging.getLogger(__name__)


LIST_BASE_URL = "https://list.fmph.uniba.sk"


def __url(path: str) -> str:
    return LIST_BASE_URL + path


def login(email: str, password: str) -> ListSession:
    session = requests.Session()

    data = {
        "student[email]": email,
        "student[password]": password,
        "button_submit": "Prihlás ma",
    }
    response = session.post(
        __url("/students/do_login.html"), data=data, allow_redirects=False
    )

    if response.status_code != 302:
        out.error(
            f"Login failed, bad server status code: {response.status_code}", response
        )
        raise ListApiError("Login failed")

    cookie = response.cookies.get("list_session")
    if cookie is None:
        out.error("Failed to obtain session cookie", response)
        raise ListApiError("Failed to obtain session cookie")

    return ListSession(session=session)


def get_all_courses(session: ListSession) -> list[Course]:
    response = session.session.get(__url("/courses.html"))
    return list_parser.get_all_courses(response.text)


def mark_course_as_active(session: ListSession, course_id: int) -> None:
    response = session.session.get(__url(f"/courses/activate_course/{course_id}.html"))

    if response.status_code != 200:
        out.error(
            f"Failed to mark course as active, bad server status code: {response.status_code}",
            response,
        )
        raise ListApiError("Failed to mark course as active")

    body = response.json()

    if "status" not in body:
        out.error("Failed to parse response", response)
        raise ListApiError("Failed to parse response")

    if body["status"] != True:
        out.error("Failed to mark course as active", response)
        raise ListApiError("Failed to mark course as active")


def get_problems_for_course(session: ListSession, course_id: int) -> list[Problem]:
    mark_course_as_active(session, course_id)

    response = session.session.get(__url(f"/tasks.html"))
    return list_parser.get_problems(response.text)


def submit_solution(
    session: ListSession, problem_id: int, solution_file: bytes
) -> Submit:
    data = {
        "submit_button": "Odovzdať riešenie",
    }

    files = {
        "file": ("solution.zip", solution_file),
    }

    response = session.session.post(
        __url(f"/tasks/upload_solution/{problem_id}.html"),
        data=data,
        files=files,
    )

    if response.status_code != 200:
        out.error(
            f"Failed to submit solution, bad server status code: {response.status_code}",
            response,
        )
        raise ListApiError("Failed to submit solution")

    submits = list_parser.get_submits(response.text, problem_id)
    return submits[-1]


def run_test_for_submit(
    session: ListSession, problem_id: int, submit_version: int
) -> None:
    form = get_submit_form(session, problem_id)

    if form is None:
        out.println("Problem has no tests to run")
        return None

    data = {
        "test[task_set_id]": form.task_set_id,
        "test[student_id]": form.student_id,
        "test[version]": submit_version,
        "select_test_type": form.select_test_type,
        "test[id][]": form.tests,
    }

    response = session.session.post(
        __url(f"/index.php/fetests/enqueue_test"),
        data=data,
    )

    if response.status_code != 200:
        out.error(
            f"Failed to run test for submit, bad server status code: {response.status_code}",
            response,
        )
        raise ListApiError("Failed to run test for submit")

    body = response.json()

    if "status" not in body or body["status"] != True:
        out.error("Failed to parse response", response)
        raise ListApiError("Failed to parse response")


def get_submit_form(session: ListSession, problem_id: int) -> SubmitForm | None:
    response = session.session.get(__url(f"/tasks/task/{problem_id}.html"))

    form = list_parser.get_submit_form(response.text)

    if form is None:
        logger.debug("The specified problem has no test running form")
        return None

    return form


def get_student_test_queue(
    session: ListSession, problem_id: int, student_id: int
) -> list[Test]:
    response = session.session.get(
        __url(f"/index.php/fetests/get_student_test_queue/{problem_id}/{student_id}")
    )
    return list_parser.get_test_queue(response.text)


def get_test_result(session: ListSession, test_id: int) -> TestResult:
    response = session.session.get(__url(f"/tasks/test_result/{test_id}.html"))
    return list_parser.get_test_result(response.text)


class ListApiError(Exception):
    pass
