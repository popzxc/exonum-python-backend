"""TODO"""
import asyncio
import sys
import os
import logging

import tornado.concurrent
import tornado.ioloop
import tornado.web
import tornado.platform.asyncio
import tornado.httpclient

from .runtime import PythonRuntime


async def _asyncio_main(logger: logging.Logger, loop: asyncio.AbstractEventLoop) -> None:
    while True:
        await asyncio.sleep(0.1)


def main() -> None:
    """Starts the Exonum Python Runtime."""

    # TODO check if `protoc` is installed.

    logging.basicConfig(level=logging.DEBUG)

    logger = logging.getLogger(__name__)

    logger.debug("Started python runtime")

    config_path = parse_args()

    loop = asyncio.get_event_loop()

    tornado.platform.asyncio.AsyncIOMainLoop().install()

    _runtime = PythonRuntime(loop, config_path)

    loop.run_until_complete(_asyncio_main(logger, loop))


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
