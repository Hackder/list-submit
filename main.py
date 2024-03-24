import atexit
import time
import sys

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

    if options.help:
        cli.print_help_message()
        return

    global_config = config.load_global_config()

    out.println(out.primary("Changed files"), "game_of_life.py, test_game_of_life.py")

    session = ui.display_request(
        "logging in", lambda: list_api.login("example@acme.com", "password")
    )

    courses = ui.display_request(
        "all courses", lambda: list_api.get_all_courses(session)
    )

    problems = ui.display_request(
        f"problems for course '{courses[0].name}'",
        lambda: list_api.get_problems_for_course(session, 1),
    )

    # with open("solution.zip", "rb") as f:
    #     byte_data = f.read()
    #     list_api.submit_solution(session, 5479, byte_data)

    # list_api.run_test_for_submit(session, 5479, 2)


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()

    out.println(out.primary("Finished"), f"in {end - start:.2f} seconds")
