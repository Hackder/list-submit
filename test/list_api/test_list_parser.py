from datetime import datetime
import unittest
import os

import list_api.list_parser as list_parser
from list_api.models import Course, Problem, Submit, TestResult, TestResultProblem


class TestListParserCourses(unittest.TestCase):
    def test_get_all_courses(self):
        with open(
            os.path.join(os.path.dirname(__file__), "courses_one_selected.html")
        ) as f:
            html = f.read()

        courses = list_parser.get_all_courses(html)

        self.assertEqual(
            courses,
            [
                Course(id=152, name="Funkcionálne programovanie"),
                Course(id=155, name="Programovanie 2"),
                Course(id=151, name="Programovanie 4 - Java"),
                Course(id=153, name="Umelá Inteligencia"),
            ],
        )

    # TODO: Add more tricky tests


class TestListParserProblems(unittest.TestCase):
    def test_get_problems(self):
        with open(os.path.join(os.path.dirname(__file__), "problems_list.html")) as f:
            html = f.read()

        problems = list_parser.get_problems(html)

        self.assertEqual(
            problems,
            [
                Problem(id=5377, full_id="5377_cvicenie_5", name="Cvičenie 5"),
                Problem(id=5365, full_id="5365_domaca_uloha_5", name="Domáca úloha 5"),
                Problem(id=5364, full_id="5364_domaca_uloha_6", name="Domáca úloha 6"),
                Problem(
                    id=5460,
                    full_id="5460_premia_kone_na_sachovnici_s_damami",
                    name="Prémia Kone na šachovnici (s dámami)",
                ),
                Problem(
                    id=5462,
                    full_id="5462_premia_obrateny_fibonacci",
                    name="Prémia Obrátený Fibonacci",
                ),
                Problem(
                    id=5484,
                    full_id="5484_premia_prednaskova",
                    name="Prémia prednášková",
                ),
                Problem(id=5358, full_id="5358_errata", name="Errata"),
                Problem(
                    id=5499,
                    full_id="5499_premia_return_true",
                    name="Prémia Return true",
                ),
            ],
        )


class TestListParserSubmit(unittest.TestCase):
    def test_get_12_submits(self):
        with open(
            os.path.join(os.path.dirname(__file__), "12_submits_3_tests.html")
        ) as f:
            html = f.read()

        submits = list_parser.get_submits(html, 5365)

        self.assertEqual(
            submits,
            [
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc183ZDA0XzEuemlw",
                    version=1,
                    name="JurajPetras_1.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc185MDAxXzIuemlw",
                    version=2,
                    name="JurajPetras_2.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc183MGZmXzMuemlw",
                    version=3,
                    name="JurajPetras_3.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc19iM2U1XzQuemlw",
                    version=4,
                    name="JurajPetras_4.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc19mYmIxXzUuemlw",
                    version=5,
                    name="JurajPetras_5.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc180YzJiXzYuemlw",
                    version=6,
                    name="JurajPetras_6.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc183MDZmXzcuemlw",
                    version=7,
                    name="JurajPetras_7.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc19kMDdiXzguemlw",
                    version=8,
                    name="JurajPetras_8.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc18xNTE5Xzkuemlw",
                    version=9,
                    name="JurajPetras_9.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc18xZTZlXzEwLnppcA__",
                    version=10,
                    name="JurajPetras_10.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc19mODk3XzExLnppcA__",
                    version=11,
                    name="JurajPetras_11.zip",
                    problem_id=5365,
                ),
                Submit(
                    id="MjIyMV9KdXJhalBldHJhc19iMjhmXzEyLnppcA__",
                    version=12,
                    name="JurajPetras_12.zip",
                    problem_id=5365,
                ),
            ],
        )

    def test_get_zero_submits(self):
        with open(os.path.join(os.path.dirname(__file__), "zero_submits.html")) as f:
            html = f.read()

        submits = list_parser.get_submits(html, 5365)

        self.assertEqual(submits, [])


class TestListParserSubmitForm(unittest.TestCase):
    def test_get_submit_form(self):
        with open(
            os.path.join(os.path.dirname(__file__), "12_submits_3_tests.html")
        ) as f:
            html = f.read()

        submit_form = list_parser.get_submit_form(html)

        self.assertEqual(
            submit_form,
            list_parser.SubmitForm(
                tests=["1170", "1192", "1048"],
                task_set_id="5365",
                student_id="2221",
                select_test_type="java",
            ),
        )

    def test_get_submit_form_with_no_test(self):
        with open(os.path.join(os.path.dirname(__file__), "no_tests.html")) as f:
            html = f.read()

        submit_form = list_parser.get_submit_form(html)

        self.assertEqual(
            submit_form,
            None,
        )


class TestListParserTestQueue(unittest.TestCase):
    def test_two_finished(self):
        with open(
            os.path.join(os.path.dirname(__file__), "tests_two_finished.html")
        ) as f:
            html = f.read()

        tests = list_parser.get_test_queue(html)

        self.assertEqual(
            tests,
            [
                list_parser.Test(
                    id=116941,
                    start_time=datetime(2024, 4, 15, 10, 31, 48),
                    end_time=datetime(2024, 4, 15, 10, 31, 50),
                ),
                list_parser.Test(
                    id=116939,
                    start_time=datetime(2024, 4, 15, 10, 23, 26),
                    end_time=datetime(2024, 4, 15, 10, 23, 28),
                ),
            ],
        )

    def test_one_unfinished(self):
        with open(
            os.path.join(os.path.dirname(__file__), "tests_one_unfinished.html")
        ) as f:
            html = f.read()

        tests = list_parser.get_test_queue(html)

        self.assertEqual(
            tests,
            [
                list_parser.Test(
                    id=116939,
                    start_time=datetime(2024, 4, 15, 10, 23, 26),
                    end_time=datetime(2024, 4, 15, 10, 23, 28),
                ),
                list_parser.Test(
                    id=116941,
                    start_time=datetime(2024, 4, 15, 10, 31, 48),
                    end_time=None,
                ),
            ],
        )


class ListParserTestResult(unittest.TestCase):
    def test_one_successful_result(self):
        with open(
            os.path.join(os.path.dirname(__file__), "one_successful_test_result.html")
        ) as f:
            html = f.read()

        test = list_parser.get_test_result(html)

        expected_output = """
Stage 1 / 1: running test ...
----- Running test file Testriesenie.py
test1 Turing() ok
test2 Turing() ok
test3 Turing() ok
test4 Turing() ok
test5 Turing() ok
----------------------------------------------------------------------
Ran 5 tests in 1.030s

OK

uspesnost: 100 % = 5.00 bodov
----- Testing finished.
""".strip()

        self.assertEqual(
            test,
            TestResult(
                total_points=5.0,
                problems=[
                    TestResultProblem(
                        name="pprojl 03",
                        points=5.0,
                        percentage=100.0,
                        output=expected_output,
                    )
                ],
            ),
        )
