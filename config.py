import configparser
import os

from dataclasses import dataclass
import constants

config_location = os.path.join(os.path.dirname(__file__), "global_config.ini")


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

    parser = configparser.ConfigParser()
    parser.read(config_location)

    version = parser.get("global", "version")
    if version != constants.VERSION:
        raise ValueError(
            f"Config version mismatch (running list-submit {constants.VERSION}, got config from {version})"
        )

    return GlobalConfig(
        email=parser.get("auth", "email"),
        password=parser.get("auth", "password"),
    )


def save_global_config(config: GlobalConfig) -> None:
    parser = configparser.ConfigParser()
    parser["global"] = {"version": constants.VERSION}
    parser["auth"] = {"email": config.email, "password": config.password}

    with open(config_location, "w") as f:
        parser.write(f)
