from __future__ import annotations
import tomlkit
import os
import glob
import queue
import logging

from dataclasses import dataclass
import constants

logger = logging.getLogger(__name__)

config_location = os.path.join(os.path.dirname(__file__), "global-config.toml")


@dataclass
class GlobalConfig:
    email: str
    password: str


def default_global_config() -> GlobalConfig:
    return GlobalConfig(
        email="",
        password="",
    )


def load_global_config() -> GlobalConfig:
    if not os.path.exists(config_location):
        return default_global_config()

    with open(config_location) as f:
        contents = f.read()
        config = tomlkit.parse(contents)

    version = config["version"]
    if version != constants.VERSION:
        raise ValueError(
            f"Config version mismatch (running list-submit {constants.VERSION}, got config from {version})"
        )

    auth = config.get("auth")
    email = auth and auth.get("email")
    password = auth and auth.get("password")

    if not isinstance(email, tomlkit.items.String):
        raise ValueError("Email not found in global config file, or email not a string")

    if not isinstance(password, tomlkit.items.String):
        raise ValueError(
            "Password not found in global config file, or email not a string"
        )

    logger.debug("Parsed global config file from: %s", config_location)

    return GlobalConfig(email=email.value, password=password.value)


def save_global_config(config: GlobalConfig) -> None:
    if os.path.exists(config_location):
        with open(config_location) as f:
            contents = f.read()
            file = tomlkit.parse(contents)
    else:
        logger.debug(
            "No global config file in: %s, creating new one from template",
            config_location,
        )
        with open(
            os.path.join(os.path.dirname(__file__), "templates", "global-config.toml")
        ) as f:
            contents = f.read()
            file = tomlkit.parse(contents)

    file["version"] = constants.VERSION
    file["auth"]["email"] = config.email
    file["auth"]["password"] = config.password

    serialized = tomlkit.dumps(file)
    with open(config_location, "w") as f:
        f.write(serialized)

    logger.debug("Saved global config file to: %s", config_location)


project_config_name = "list-submit.toml"


@dataclass
class ProblemConfig:
    course_id: int
    problem_id: int
    files: list[str]


@dataclass
class ProjectConfig:
    version: str
    problem: ProblemConfig


def find_project_config(name: str | None) -> str | None:
    """
    Find the location of a project config file.

    If name is provided, performs a BFS serach on all subdirectories
    (does not include the cwd in search) of cwd looking for a directory
    with the provided name and a config file within it

    if `name` is None, looks in the current directory,
    and than all the parent directories until it finds
    a config file. If none is found, returns None
    """

    if name is not None:
        q = queue.Queue()
        while not q.empty():
            dir = q.get()
            listing = os.listdir(dir)
            has_config_file = project_config_name in listing
            if os.path.dirname(dir) == name and has_config_file:
                project_directory = os.path.join(dir, project_config_name)
                logger.debug(
                    "Found project with name: %s, directory: %s",
                    name,
                    project_directory,
                )
                return project_directory

            directories = [d for d in listing if os.path.isdir(d)]
            for d in directories:
                q.put(d)

        logger.debug("Project directory with name %s not found", name)
        return None

    dir = os.getcwd()
    while True:
        if project_config_name in os.listdir(dir):
            return os.path.join(dir, project_config_name)

        new_dir = os.path.dirname(dir)
        if new_dir == dir:
            break
        dir = new_dir

    logger.debug("No config file found in all parent directories")
    return None


def load_project_config(config_path: str):
    with open(config_path, "r") as f:
        contents = f.read()
        cfg = tomlkit.parse(contents)

    version = cfg["version"]
    if version != constants.VERSION:
        raise ValueError(
            f"Config version mismatch (running list-submit {constants.VERSION}, got config from {version})"
        )

    problem_id = cfg["problem"]["problem_id"]
    if not isinstance(problem_id, tomlkit.items.Integer):
        raise ValueError(
            "Problem ID not found in project config file, or not an integer"
        )

    course_id = cfg["problem"]["course_id"]
    if not isinstance(course_id, tomlkit.items.Integer):
        raise ValueError(
            "Course ID not found in project config file, or not an integer"
        )

    files = cfg["problem"]["files"]
    if not isinstance(files, tomlkit.items.Array):
        raise ValueError("Files not found in project config file, or not an array")
    if not all(isinstance(f, tomlkit.items.String) for f in files):
        raise ValueError("Files not an array of strings")

    logger.debug("Project config loaded from: %s", config_path)
    return ProjectConfig(
        version=version,
        problem=ProblemConfig(
            problem_id=cfg["problem"]["problem_id"],
            course_id=cfg["problem"]["course_id"],
            files=cfg["problem"]["files"],
        ),
    )


def __default_project_config_toml():
    logger.debug("Loading default project config toml template")
    template_path = os.path.join(
        os.path.dirname(__file__), "templates", "project-config.toml"
    )
    with open(template_path) as f:
        contents = f.read()
        current_config = tomlkit.parse(contents)

    return current_config


def save_project_config(config: ProjectConfig, path: str | None = None):
    """
    Saves the config file to the specified location.
    If no location is provided uses the default location,
    assuming that cwd is the project directory

    If there is a config already present at the location,
    and has a different version, a completely new config will be created
    from the template.
    """
    path = path or os.path.join(os.getcwd(), project_config_name)

    if os.path.exists(path):
        with open(path, "r") as f:
            contents = f.read()
            current_config = tomlkit.parse(contents)
    else:
        path = os.path.join(os.getcwd(), project_config_name)
        current_config = __default_project_config_toml()

    # TODO: This breaks any comments or structure user has,
    # Future version should include a betters migration solution
    version = current_config["version"]
    if version != constants.VERSION:
        logger.debug(
            "Config version missmatch while saving project config to: %s", path
        )
        current_config = __default_project_config_toml()

    current_config["version"] = constants.VERSION
    current_config["problem"]["course_id"] = config.problem.course_id
    current_config["problem"]["problem_id"] = config.problem.problem_id
    current_config["problem"]["files"] = config.problem.files

    new_content = tomlkit.dumps(current_config)
    with open(path, "w") as f:
        f.write(new_content)

    logger.debug("Saved config file to: %s")


def add_files_to_project(project: str | None, pattern: str) -> None:
    # TODO: Assign root dir based on the project config
    files = glob.glob(pattern, recursive=True, root_dir=None)
    # TODO: Merge the files with the project config


def remove_files_from_project(project: str | None, pattern: str) -> None:
    # TODO: Assign root dir based on the project config
    files = glob.glob(pattern, recursive=True, root_dir=None)
    # TODO: Remove the files from the project config
