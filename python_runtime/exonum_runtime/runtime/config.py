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
        self.artifacts_sources_folder = toml_config["python"]["artifacts_sources_folder"]
        self.built_sources_folder = toml_config["python"]["built_sources_folder"]
        self.runtime_api_port = toml_config["python"]["api_port"]
        self.service_api_ports_start = toml_config["python"]["service_api_ports_start"]
