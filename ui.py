from typing import Callable
from getpass import getpass

import time
import task
import out


def display_request[T](name: str, request: Callable[[], T]) -> T:
    """
    Prints the name of the request, and shows a loading spinner while
    the request is being made.

    Returns the result of the request.
    """

    # TODO: Handle failed requests

    def loading_spinner(is_alive: task.IsAlive) -> None:
        loading_chars = [".  ", ".. ", "...", " ..", "  .", "   "]
        loading_chars = ["◜", "◝", "◞", "◟"]
        out.hide_cursor()

        spinner_size = len(loading_chars[0])

        i = 0
        while is_alive():
            current_char = loading_chars[i]
            out.println(out.secondary(current_char), end="")
            out.flush()
            time.sleep(0.15)
            out.println("\b" * spinner_size, end="")
            i = (i + 1) % len(loading_chars)
        out.println("=> done")
        out.show_cursor()

    tab_spacing = " " * 2
    out.println(out.primary(f"{tab_spacing}Request"), name, "", end="")
    return task.run_with_companion(request, loading_spinner)


def ok_or_exit[T](task: Callable[[], T], code: int = 1) -> T:
    try:
        return task()
    except Exception as e:
        out.error(str(e))
        exit(code)


def prompt(
    message: str,
    hide_input: bool = False,
    validator: Callable[[str], bool] = lambda _: True,
) -> str:
    while True:
        if hide_input:
            value = getpass(out.bold(message))
        else:
            value = input(out.bold(message))

        if validator(value):
            return value


def select_from_list[T](items: list[T], display: Callable[[T], str]) -> T:
    for i, item in enumerate(items):
        out.println(out.secondary(f"{i + 1}."), display(item))

    while True:
        input = prompt("Select: ")
        try:
            index = int(input) - 1
            if index < 0 or index >= len(items):
                raise ValueError
        except ValueError:
            out.error(f"Invalid selection, pick number from 1 to {len(items)}")
            continue

        return items[index]
