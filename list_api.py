import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from dataclasses import dataclass

import out


LIST_BASE_URL = "https://list.fmph.uniba.sk"


@dataclass
class ListSession:
    """
    Session object that holds the current active session.
    You can obtain this session by calling `list_api.login`

    Example:
    session = list_api.login("email", "password")

    Attributes:
        session (requests.Session): The active session object.
    """

    session: requests.Session


@dataclass
class Course:
    """
    Course object with course id and name.

    Attributes:
        id: The id of the course.
        name: The name of the course.
    """

    id: int
    name: str


@dataclass
class Problem:
    """
    L.I.S.T. assigned task.

    Attributes:
        id: The ID of the problem.
        full_id: id + name in snake_case.
        name: The name of the problem.
    """

    id: int
    full_id: str
    name: str


@dataclass
class Submit:
    """
    Submit represents a submission of a solution to a problem.
    Automated tests can be run for a submition using `list_api.run_test_for_submit`.

    Attributes:
        id: The ID of the submission.
        version: The version of the submission.
        name: The name of the submission.
        problem_id: The ID of the problem associated with the submission.
    """

    id: str
    version: int
    name: str
    problem_id: int


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

    soup = BeautifulSoup(response.text, "html.parser")
    course_elements = soup.find_all("div", class_="period_course")

    def create_course(element) -> Course | None:
        name_h4 = element.find("h4")

        if name_h4 is None:
            out.error("Failed to parse course name", response)
            return None

        name = name_h4.text or "Empty name"

        anchors = element.find_all("a")

        if len(anchors) == 0:
            out.error(f"Failed to parse course anchors: {name}", element)
            return None

        anchor = anchors[-1]

        if anchor.text != "Zobraz detaily":
            out.error(f"Failed to parse course id: {name}", response)
            raise ListApiError("Failed to parse course name")

        href = anchor.get("href")

        if href is None:
            out.error("Failed to parse course href", response)
            return None

        # TODO: Handle errors
        id = href.split("/")[-1].split(".")[0]
        id = int(id)

        return Course(id=id, name=name)

    courses = map(create_course, course_elements)
    courses = [c for c in courses if c is not None]

    return courses


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

    soup = BeautifulSoup(response.text, "html.parser")

    problem_elements = soup.find_all("td", class_="td_name")

    def parse_problem(element) -> Problem:
        anchor = element.find("a")

        href = anchor.get("href")

        # TODO: Handle errors
        full_id = href.split("/")[-1].split(".")[0]
        id = int(full_id.split("_")[0])
        name = anchor.text

        return Problem(id=id, full_id=full_id, name=name)

    problems = map(parse_problem, problem_elements)
    return list(problems)


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

    soup = BeautifulSoup(response.text, "html.parser")
    submits_elements = soup.select("table.solutions_table tr")

    def parse_submit(element: Tag) -> Submit | None:
        input = element.find("input")

        if input is None:
            out.error("Failed to parse submit input", element)
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

    submits = map(parse_submit, submits_elements)
    submits = [s for s in submits if s is not None]

    return submits[-1]


def run_test_for_submit(
    session: ListSession, problem_id: int, submit_version: int
) -> None:
    response = session.session.get(__url(f"/tasks/task/{problem_id}.html"))

    soup = BeautifulSoup(response.text, "html.parser")

    tests = soup.select('input[name="test[id][]"]')
    tests = [t.get("value") for t in tests if t.get("value") is not None]

    task_set_id = soup.select_one('input[name="test[task_set_id]"]')
    assert task_set_id is not None
    task_set_id = task_set_id.get("value")

    student_id = soup.select_one('input[name="test[student_id]"]')
    assert student_id is not None
    student_id = student_id.get("value")

    select_test_type = soup.select_one('input[name="select_test_type"]')
    assert select_test_type is not None
    select_test_type = select_test_type.get("value")

    data = {
        "test[task_set_id]": task_set_id,
        "test[student_id]": student_id,
        "test[version]": submit_version,
        "select_test_type": select_test_type,
        "test[id][]": tests,
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


class ListApiError(Exception):
    pass
