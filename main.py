#!/usr/bin/env python3
import atexit
from datetime import datetime
import io
import time
import sys
import logging
import glob
import os
import zipfile

import list_api
import out
import ui
import cli
import config
import detectors.python_detector


def exit_handler():
    # If the program is terminated, or an unexpected error occurs,
    # make sure the cursor is shown again
    out.show_cursor()


atexit.register(exit_handler)


DETECTORS = [detectors.python_detector.get_detector()]


def new_local_config(
    session: list_api.ListSession,
) -> tuple[config.ProjectConfig, list_api.Problem]:
    """
    Asks the user all the necessary questions to create a new project config
    """
    courses = ui.display_request(
        "all courses", lambda: list_api.get_all_courses(session)
    )
    out.println(out.bold("Select a course:"))
    course = ui.select_from_list(courses, lambda c: c.name)
    out.println()

    problems = ui.display_request(
        f"problems for course '{course.name}'",
        lambda: list_api.get_problems_for_course(session, course.id),
    )
    problem = ui.select_from_list(problems, lambda p: p.name)
    out.println()

    detector, probability, files, recommendations = max(
        map(lambda d: (d,) + d.detect(os.getcwd()), DETECTORS)
    )

    if probability < 0.3:
        out.println("Could not detect project files automatically.")
        files = []
    else:
        out.println(
            out.primary("Detected project as:"), out.primary(out.bold(detector.name))
        )
        for file in files[:-1]:
            out.println("|-", file)
        out.println("∟", files[-1])

        out.println()
        for recommendation in recommendations:
            out.println(out.error("Recommendation"), recommendation)

        if not ui.confirm("Do you want to use these files?", default="y"):
            files = []

    cfg = config.ProjectConfig(
        version=config.constants.VERSION,
        problem=config.ProblemConfig(
            problem_id=problem.id,
            problem_name=problem.name,
            course_id=course.id,
            files=files,
        ),
    )

    return (cfg, problem)


def main():
    options = ui.ok_or_exit(lambda: cli.parse_cli_params(sys.argv))

    logging.basicConfig(level=options.log_level)

    global_config = config.load_global_config()

    if options.auth:
        email = ui.prompt("Email: ")
        password = ui.prompt("Password: ", hide_input=True)

        global_config.email = email
        global_config.password = password
        config.save_global_config(global_config)
        exit(0)

    session = None
    project_config_location = config.find_project_config(options.project)
    new_config = False
    if project_config_location is None:
        session = ui.display_request(
            "logging in",
            lambda: list_api.login(global_config.email, global_config.password),
        )
        project_config, problem = new_local_config(session)
        new_config = True
        config.save_project_config(project_config, None)
    else:
        project_config = config.load_project_config(project_config_location)

    project_directory = (
        os.path.dirname(project_config_location)
        if project_config_location is not None
        else os.getcwd()
    )

    def get_relative_glob(glob_pattern: str, perspective_dir: str) -> list[str]:
        """
        Find all files matching the glob patter starting from cwd
        and returns their paths relative to the provided directory
        """
        files = glob.glob(glob_pattern, recursive=True, root_dir=None)
        files = [os.path.abspath(p) for p in files]
        files = [os.path.relpath(p, perspective_dir) for p in files]
        return files

    if options.add is not None:
        files = get_relative_glob(options.add, project_directory)

        for i in range(len(files)):
            out.println(out.primary("Adding"), files[i])

        if len(files) > 3:
            ui.confirm(
                f"You are about to add these {len(files)} files to the project. Continue?"
            )

        for file in files:
            if file not in project_config.problem.files:
                project_config.problem.files.append(file)

        config.save_project_config(project_config, project_config_location)
        exit(0)

    if options.remove is not None:
        files = get_relative_glob(options.remove, project_directory)
        for i in range(len(files)):
            out.println(out.primary("Removing"), files[i])

        project_config.problem.files = list(
            filter(lambda f: f not in files, project_config.problem.files)
        )

        config.save_project_config(project_config, project_config_location)
        exit(0)

    if session is None:
        session = ui.display_request(
            "logging in",
            lambda: list_api.login(global_config.email, global_config.password),
        )

    if len(project_config.problem.files) == 0:
        out.error(
            "No files to submit, the files list is empty\nAdd files using the --add flag"
        )
        exit(1)

    if new_config and not ui.confirm(
        "Do you want to submit the solution now?", default="y"
    ):
        exit(0)

    # Submit the solution

    out.println(
        out.primary("Submitting"),
        "solution for",
        out.bold(project_config.problem.problem_name),
    )
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file in project_config.problem.files:
            abs_path = os.path.join(project_directory, file)
            zip_file.write(abs_path, os.path.basename(abs_path))

    submit = ui.display_request(
        "submitting solution",
        lambda: list_api.submit_solution(
            session, project_config.problem.problem_id, zip_buffer.getvalue()
        ),
    )
    ui.display_request(
        "running tests",
        lambda: list_api.run_test_for_submit(
            session, project_config.problem.problem_id, submit.version
        ),
    )

    # Poll for test results

    form = list_api.get_submit_form(session, project_config.problem.problem_id)
    if form is None:
        out.println("Problem has no tests to watch")
        exit(0)

    def wait_for_results():
        start = datetime.now()
        while True:
            queue = list_api.get_student_test_queue(
                session, project_config.problem.problem_id, int(form.student_id)
            )
            closest = max(queue, key=lambda t: t.start_time - start)
            delta = closest.start_time - start
            if delta.total_seconds() > 0:
                time.sleep(0.5)
                continue

            if closest.end_time is not None:
                break
            time.sleep(0.5)

        return closest.id

    test_id = ui.display_request("waiting for results", wait_for_results)

    test_result = ui.display_request(
        "getting test results", lambda: list_api.get_test_result(session, test_id)
    )

    out.println(out.bold(f"Total points: {test_result.total_points}"))

    max_len = max(map(lambda p: len(p.name), test_result.problems), default=0)
    for problem in test_result.problems:
        out.println(
            problem.name.ljust(max_len + 5, " "),
            f"points: {out.bold(str(problem.points))}",
            f"percent: {out.bold(str(problem.percentage))}",
        )


if __name__ == "__main__":
    start = time.time()
    try:
        main()
    except KeyboardInterrupt:
        out.println(out.error("Interrupted"))
        exit(1)
    end = time.time()

    out.println(out.primary("Finished"), f"in {end - start:.2f} seconds")
