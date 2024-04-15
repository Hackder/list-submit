from __future__ import annotations
from typing import Literal
import requests
from datetime import datetime
from dataclasses import dataclass


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


@dataclass
class Test:
    id: int
    start_time: datetime
    end_time: datetime | None


@dataclass
class SubmitForm:
    tests: list[str]
    task_set_id: str
    student_id: str
    select_test_type: str


@dataclass
class TestResult:
    total_points: float
    problems: list[TestResultProblem]


@dataclass
class TestResultProblem:
    name: str
    percentage: float
    points: float
