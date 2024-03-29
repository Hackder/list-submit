from dataclasses import dataclass
import argparse


@dataclass
class CliOptions:
    force: bool = False
    auth: bool = False
    project: str | None = ""
    add: str | None = ""
    remove: str | None = ""


DESCRIPTION = """
This is a simple CLI utility for submitting solution to L.I.S.T. automatically.
It will take all of your project files, zip them acording to the L.I.S.T. requirements,
submit them to the L.I.S.T. server, and run the tests for you. All automatically.
"""

parser = argparse.ArgumentParser(
    prog="list-submit",
    description=DESCRIPTION.strip(),
)

parser.add_argument("project", nargs="?", default=None)
parser.add_argument("-f", "--force", action="store_true", help="Force the operation")
parser.add_argument(
    "--auth", action="store_true", help="Retype your L.I.S.T. email and password"
)
parser.add_argument(
    "-a",
    "--add",
    action="store",
    help="Add all files mathing the provided glob pattern",
)
parser.add_argument(
    "-r",
    "--remove",
    action="store",
    help="Remove all files mathing the provided glob pattern",
)


def parse_cli_params(argv: list[str]) -> CliOptions:
    # remove the program name from the arguments
    argv = argv[1:]

    options = parser.parse_args(argv)
    return CliOptions(
        force=options.force,
        auth=options.auth,
        project=options.project,
        add=options.add,
        remove=options.remove,
    )
