from dataclasses import dataclass
from typing import Callable, Any

import out
import constants


@dataclass
class CliOptions:
    force: bool = False
    auth: bool = False
    help: bool = False
    project: str = ""


@dataclass(frozen=True)
class CliArgument:
    name: str
    aliases: list[str]
    description: str
    value_parser: Callable[[str], Any]


cli_arguments = [
    CliArgument("help", ["h"], "Show this help message", lambda x: bool(x)),
    CliArgument("force", ["f"], "Force the operation", lambda x: bool(x)),
    CliArgument(
        "auth", ["a"], "Retype your L.I.S.T. email and password", lambda x: bool(x)
    ),
]
# The default param that doesn't require a switch to be used
cli_param = CliArgument(
    "project",
    [],
    "optionally specify project name (folder name) to submit",
    lambda x: str(x),
)


def find_argument(name: str) -> CliArgument:
    for arg in cli_arguments:
        if arg.name == name or name in arg.aliases:
            return arg
    raise ValueError(f"Unknown argument: {name}")


def parse_cli_params(argv: list[str]) -> CliOptions:
    options = CliOptions()

    if len(argv) <= 1:
        return options

    parsed_param = False

    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            switch = arg[2:]
        elif arg.startswith("-"):
            switch = arg[1:]
        elif not parsed_param:
            parsed_param = True
            setattr(options, cli_param.name, cli_param.value_parser(arg))
            i += 1
            continue
        else:
            raise ValueError(f"Unknown argument: {arg}")

        argument = find_argument(switch)

        if isinstance(getattr(options, argument.name), bool):
            setattr(options, argument.name, True)
            i += 1
            continue

        if i + 1 >= len(argv):
            raise ValueError(f"Missing value for {arg}")

        value = argv[i + 1]
        setattr(options, argument.name, argument.value_parser(value))

        i += 2

    return options


DESCRIPTION = """
This is a simple CLI utility for submitting solution to L.I.S.T. automatically.
It will take all of your project files, zip them acording to the L.I.S.T. requirements,
submit them to the L.I.S.T. server, and run the tests for you. All automatically.
"""


def format_argument(arg: CliArgument) -> str:
    aliases = [f"-{alias}" for alias in arg.aliases]
    aliases = ", ".join(aliases)
    return out.secondary(f"  --{arg.name}, {aliases}: ") + arg.description


def print_help_message():
    out.println(out.primary("list-submit"), "v" + constants.VERSION)
    out.println(out.primary("Usage"), "python main.py [options] [project?]")
    out.println()
    out.println(out.primary("Description"))
    out.println(DESCRIPTION.strip())
    out.println()
    out.println(out.primary("Options"))
    for arg in cli_arguments:
        out.println(format_argument(arg))
    out.println(" ", out.primary(f"{cli_param.name}:"), cli_param.description)
