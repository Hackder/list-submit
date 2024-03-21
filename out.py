import os
import sys
from typing import Any

if os.name == "nt":
    import ctypes

    class _CursorInfo(ctypes.Structure):
        _fields_ = [("size", ctypes.c_int), ("visible", ctypes.c_byte)]


# A unit object used for default argument values,
# to prevent unintended collisions with provided values
__UNIT = object()


def error(message: str, context: Any = __UNIT) -> None:
    print(message, file=sys.stderr)
    if context is not __UNIT:
        print(context, file=sys.stderr)


RESET = "\033[0m"
PRIMARY = "\033[95m"
SECONDARY = "\033[94m"


def println(*args, end: str = "\n") -> None:
    sys.stdout.write(" ".join(map(str, args)) + end)


def flush() -> None:
    sys.stdout.flush()


def color(text: str, color_code: str) -> str:
    return color_code + text + RESET


def primary(text: str) -> str:
    return color(text, PRIMARY)


def secondary(text: str) -> str:
    return color(text, SECONDARY)


def hide_cursor():
    """
    Hide cursor
    """
    if os.name == "nt":
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = False
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == "posix":
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()


def show_cursor():
    """
    Show cursor.
    """
    if os.name == "nt":
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = True
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == "posix":
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
