import tomlkit
import os
import glob
import queue

from dataclasses import dataclass
import constants

config_location = os.path.join(os.path.dirname(__file__), "global-config.toml")


@dataclass
class GlobalConfig:
    email: str
    password: str

    def __init__(self, email, password):
        if type(email) is not str:
            raise Exception(f"Invalid email in config file: {email}, expected string")

        if type(password) is not str:
            raise Exception(
                f"Invalid password in config file: {password}, expected string"
            )


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

    return GlobalConfig(email=email, password=password)


def save_global_config(config: GlobalConfig) -> None:
    if os.path.exists(config_location):
        with open(config_location) as f:
            contents = f.read()
            file = tomlkit.parse(contents)
    else:
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


project_config_name = "list-submit.toml"


@dataclass
class TaskConfig:
    course_id: int
    problem_id: int
    files: list[str]

    def __init__(self, course_id: int, problem_id: int, files: list[str]):
        if not (type(course_id) is int and course_id > 0):
            raise Exception(f"Invalid course_id in config file: {course_id}")

        if not (type(problem_id) is int and problem_id > 0):
            raise Exception(f"Invalid problem_id in config file: {problem_id}")

        if not (type(files) == "list" and all(type(item) is str for item in files)):
            raise Exception(f"Not all files specified are strings: {files}")


@dataclass
class ProjectConfig:
    version: str
    task: TaskConfig


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
                return os.path.join(dir, project_config_name)

            directories = [d for d in listing if os.path.isdir(d)]
            for d in directories:
                q.put(d)

        return None

    dir = os.getcwd()
    while (dir := os.path.dirname(dir)) != dir:
        if project_config_name in os.listdir(dir):
            return os.path.join(dir, project_config_name)

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

    return ProjectConfig(
        version=version,
        task=TaskConfig(
            problem_id=cfg["task"]["problem_id"],
            course_id=cfg["task"]["course_id"],
            files=cfg["task"]["files"],
        ),
    )


def __default_project_config_toml():
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
        current_config = __default_project_config_toml()

    # TODO: This breaks any comments or structure user has,
    # Future version should include a betters migration solution
    version = current_config["version"]
    if version != constants.VERSION:
        current_config = __default_project_config_toml()

    current_config["version"] = constants.VERSION
    current_config["task"]["course_id"] = config.task.course_id
    current_config["task"]["problem_id"] = config.task.problem_id
    current_config["task"]["files"] = config.task.files


def add_files_to_project(project: str | None, pattern: str) -> None:
    # TODO: Assign root dir based on the project config
    files = glob.glob(pattern, recursive=True, root_dir=None)
    # TODO: Merge the files with the project config


def remove_files_from_project(project: str | None, pattern: str) -> None:
    # TODO: Assign root dir based on the project config
    files = glob.glob(pattern, recursive=True, root_dir=None)
    # TODO: Remove the files from the project config
