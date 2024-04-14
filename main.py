#!/usr/bin/env python3
import atexit
import time
import sys
import logging
import glob
import os

import list_api
import out
import ui
import cli
import config


def exit_handler():
    # If the program is terminated, or an unexpected error occurs,
    # make sure the cursor is shown again
    out.show_cursor()


atexit.register(exit_handler)


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

    problems = ui.display_request(
        f"problems for course '{course.name}'",
        lambda: list_api.get_problems_for_course(session, course.id),
    )
    problem = ui.select_from_list(problems, lambda p: p.name)

    cfg = config.ProjectConfig(
        version=config.constants.VERSION,
        problem=config.ProblemConfig(
            problem_id=problem.id,
            course_id=course.id,
            # TODO: Run automatic project detection to prefill files
            files=[],
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

    session = ui.display_request(
        "logging in",
        lambda: list_api.login(global_config.email, global_config.password),
    )

    project_config_location = config.find_project_config(options.project)
    if project_config_location is None:
        project_config, problem = new_local_config(session)
        config.save_project_config(project_config)
    else:
        project_config = config.load_project_config(project_config_location)
        problems = ui.display_request(
            f"problems",
            lambda: list_api.get_problems_for_course(
                session, project_config.problem.course_id
            ),
        )
        problems = [p for p in problems if p.id == project_config.problem.problem_id]

        if len(problems) == 0:
            out.error(
                "Problem stored in config not found. It is probably after deadline."
            )
            exit(1)

        problem = problems[0]

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

    if len(project_config.problem.files) == 0:
        out.error(
            "No files to submit, the files list is empty\nAdd files using the --add flag"
        )
        exit(1)

    out.println(out.primary("Submitting"), "solution for", out.bold(problem.name))

    # with open("solution.zip", "rb") as f:
    #     byte_data = f.read()
    #     list_api.submit_solution(session, 5479, byte_data)

    # list_api.run_test_for_submit(session, 5479, 2)


def submit_solution(
    session: list_api.ListSession,
    problem: list_api.Problem,
    project_config: config.ProjectConfig,
):
    pass


if __name__ == "__main__":
    start = time.time()
    try:
        main()
    except KeyboardInterrupt:
        out.println(out.error("Interrupted"))
        exit(1)
    end = time.time()

    out.println(out.primary("Finished"), f"in {end - start:.2f} seconds")
