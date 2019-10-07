"""Helper script that uploads artifacts to the Python Runtime.

Note that you have to call it for every network manually."""

from typing import Tuple, Any
import sys
import os

import requests


def print_help() -> None:
    """Shows help message and exits."""
    help_msg = """
    Artifact uploader script.
    This script isn't checking input data to be valid, so verify it yourself.

    Usage:
        python file_uploader.py 127.0.0.1:8090 file_a [file_b, ...]

        First argument is the address and the port of the Python runtime API.
        Second (and all others) are paths to the files to upload.
    """

    print(help_msg)
    sys.exit(0)


def file_entry(file_path: str) -> Tuple[str, Any, str]:
    """Creates a tuple expected by Requests from file path"""
    file_name = os.path.split(file_path)[1]
    file_handler = open(file_path, "rb")
    content_type = "application/octet-stream"

    return (file_name, file_handler, content_type)


def run() -> None:
    """Runs the script."""

    if len(sys.argv) < 3:
        print_help()

    network = sys.argv[1]
    # Trim the last slash.
    if network[-1] == "/":
        network = network[:-1]
    files = sys.argv[2:]

    files_upload_entry = [("artifacts", file_entry(file_path)) for file_path in files]

    endpoint = f"{network}/artifacts"

    result = requests.post(endpoint, files=files_upload_entry)

    print(result)

    if result.status_code == 200:
        print(result.json())


if __name__ == "__main__":
    run()
