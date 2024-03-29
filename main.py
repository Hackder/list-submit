#!/usr/bin/env python3
import atexit
import time
import sys
import logging

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


def main():
    options = ui.ok_or_exit(lambda: cli.parse_cli_params(sys.argv))
<<<<<<< HEAD
    # TODO: Set level from options when new options PR get's merged
    logging.basicConfig(level=logging.DEBUG)

    if options.help:
        cli.print_help_message()
        return

=======
>>>>>>> 95d6b18 (feat: add/remove files glob parsing)
    global_config = config.load_global_config()

    if options.auth:
        email = ui.prompt("Email: ")
        password = ui.prompt("Password: ", hide_input=True)

        global_config.email = email
        global_config.password = password
        config.save_global_config(global_config)
        exit(0)

    if options.add is not None:
        config.add_files_to_project(options.project, options.add)
        exit(0)

    if options.remove is not None:
        config.remove_files_from_project(options.project, options.remove)
        exit(0)

    session = ui.display_request(
        "logging in",
        lambda: list_api.login(global_config.email, global_config.password),
    )

    courses = ui.display_request(
        "all courses", lambda: list_api.get_all_courses(session)
    )

    course = courses[2]
    problems = ui.display_request(
        f"problems for course '{course.name}'",
        lambda: list_api.get_problems_for_course(session, course.id),
    )

    print(problems)

    # with open("solution.zip", "rb") as f:
    #     byte_data = f.read()
    #     list_api.submit_solution(session, 5479, byte_data)

    # list_api.run_test_for_submit(session, 5479, 2)


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()

    out.println(out.primary("Finished"), f"in {end - start:.2f} seconds")
