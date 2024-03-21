import random
import time

from .models import Course, Problem, Submit, ListSession


def login(email: str, password: str) -> ListSession:
    time.sleep(0.3)
    print(f"Logging in with - email: {email}  password: {password}")
    return ListSession(session=None)  # type: ignore


def get_all_courses(session: ListSession) -> list[Course]:
    time.sleep(0.3)
    return [
        Course(id=1, name="Python Course"),
        Course(id=2, name="Java for beginners"),
        Course(id=3, name="Haskell for dummies"),
    ]


def mark_course_as_active(session: ListSession, course_id: int) -> None:
    time.sleep(0.3)
    name = get_all_courses(session)[course_id - 1].name
    print(f"Marking course as active - course_id: {course_id}, name: {name}")
    return None


def get_problems_for_course(session: ListSession, course_id: int) -> list[Problem]:
    time.sleep(0.3)
    name = get_all_courses(session)[course_id - 1].name
    name = name.lower().replace(" ", "_")
    return [
        Problem(
            id=110 + course_id,
            name="Problem 1",
            full_id=f"11{course_id}_{name}_problem_1",
        ),
        Problem(
            id=220 + course_id,
            name="Problem 2",
            full_id=f"22{course_id}_{name}_problem_2",
        ),
        Problem(
            id=330 + course_id,
            name="Problem 3",
            full_id=f"33{course_id}_{name}_problem_3",
        ),
    ]


version = 1


def submit_solution(
    session: ListSession, problem_id: int, solution_file: bytes
) -> Submit:
    global version
    time.sleep(0.3)
    course_id = problem_id % 10
    course_name = get_all_courses(session)[course_id - 1].name
    problem_name = get_problems_for_course(session, course_id)[problem_id // 100].name
    print(
        f"""
Submitting solution
    - problem_id: {problem_id}
    - problem: {problem_name}
    - course: {course_name}
    - file_size: {len(solution_file)} bytes
        """
    )

    random_name = random.choice(["GAs63U8SgeCi", "8rHxef7e7i13", "l7c0IU72Gm6t"])
    return Submit(
        id=random_name,
        version=version,
        name=f"Solution {version}",
        problem_id=problem_id,
    )


def run_test_for_submit(
    session: ListSession, problem_id: int, submit_version: int
) -> None:
    time.sleep(0.3)
    course_id = problem_id % 10
    problem_name = get_problems_for_course(session, course_id)[problem_id // 100].name
    print(
        f"""
Running test for submit
    - problem_id: {problem_id},
    - problem_name: {problem_name},
    - version: {submit_version}
"""
    )


class ListApiError(Exception):
    pass
