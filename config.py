import tomllib
import os

from dataclasses import dataclass
import constants


@dataclass
class GlobalConfig:
    email: str
    password: str


def load_global_config() -> GlobalConfig | None:
    config_location = os.path.join(os.path.dirname(__file__), "global_config.toml")
    if not os.path.exists(config_location):
        return None

    with open(config_location, "rb") as f:
        config = tomllib.load(f)

    if config["version"] != constants.VERSION:
        raise ValueError(
            f"Config version mismatch (running list-submit {constants.VERSION}, got config from {config['version']})"
        )

    return GlobalConfig(
        email=config["email"],
        password=config["password"],
    )
