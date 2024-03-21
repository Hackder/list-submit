import random
import time

import out

from .models import Course, Problem, Submit, ListSession


def login(email: str, password: str) -> ListSession:
    time.sleep(1)
    out.error("Login failed, bad server status code: 500", "Login failed")
    raise ListApiError("Login failed")


def get_all_courses(session: ListSession) -> list[Course]:
    time.sleep(1)
    out.error("Failed to parse course name", "Failed to parse course name")
    raise ListApiError("Failed to parse course name")


def mark_course_as_active(session: ListSession, course_id: int) -> None:
    time.sleep(1)
    out.error(
        "Failed to mark course as active, bad server status code: 500",
        "Failed to mark course as active",
    )
    raise ListApiError("Failed to mark course as active")


def get_problems_for_course(session: ListSession, course_id: int) -> list[Problem]:
    time.sleep(1)
    out.error("Failed to parse course name", "Failed to parse course name")
    raise ListApiError("Failed to parse course name")


version = 1


def submit_solution(
    session: ListSession, problem_id: int, solution_file: bytes
) -> Submit:
    time.sleep(1)

    out.error(
        "Failed to submit solution, bad server status code: 500",
        "Failed to submit solution",
    )
    raise ListApiError("Failed to submit solution")


def run_test_for_submit(
    session: ListSession, problem_id: int, submit_version: int
) -> None:
    time.sleep(1)
    out.error(
        "Failed to run test for submit, bad server status code: 500",
        "Failed to run test for submit",
    )
    raise ListApiError("Failed to run test for submit")


class ListApiError(Exception):
    pass
