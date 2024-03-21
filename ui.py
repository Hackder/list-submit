from typing import Callable
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
        exit(1)
