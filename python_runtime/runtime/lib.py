"""TODO"""
import asyncio
import sys
import os

from .runtime import PythonRuntime


def main() -> None:
    """Starts the Exonum Python Runtime."""
    config_path = parse_args()

    loop = asyncio.new_event_loop()

    _runtime = PythonRuntime(loop, config_path)

    loop.run_forever()


def parse_args() -> str:
    """Parses config file path from command line arguments."""
    if len(sys.argv) != 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print_help()
        sys.exit(0)

    config_path = sys.argv[1]
    if not os.path.isfile(config_path):
        print("Specified path is not a valid file path")
        sys.exit(1)

    return config_path


def print_help() -> None:
    """Prints help message."""
    usage = """
    Exonum Python runtime.

    Usage: python3.7 -m exonum_python_runtime path/to/config.toml
    """

    print(usage)


if __name__ == "__main__":
    main()
