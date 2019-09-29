"""Module capable of loading the Python Runtime configuration file."""

import toml


class Configuration:
    """Python Runtime configuration."""

    def __init__(self, path: str) -> None:
        self._config_path = path
        self._load_config()

    def _load_config(self) -> None:
        toml_config = toml.load(self._config_path)

        self.rust_lib_path = toml_config["python"]["rust_library_path"]
        self.db_options = toml_config["database"]
