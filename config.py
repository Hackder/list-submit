import tomlkit
import os
import glob

from dataclasses import dataclass
import constants

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


def add_files_to_project(project: str | None, pattern: str) -> None:
    # TODO: Assign root dir based on the project config
    files = glob.glob(pattern, recursive=True, root_dir=None)
    # TODO: Merge the files with the project config


def remove_files_from_project(project: str | None, pattern: str) -> None:
    # TODO: Assign root dir based on the project config
    files = glob.glob(pattern, recursive=True, root_dir=None)
    # TODO: Remove the files from the project config
