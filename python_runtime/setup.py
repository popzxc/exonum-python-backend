#!/usr/bin/env python
"""Setup script for the Exonum python runtime."""
from distutils.core import setup

INSTALL_REQUIRES = ["protobuf", "pysodium", "tornado", "plyvel"]

PYTHON_REQUIRES = ">=3.4"

setup(
    name="exonum-python-runtime",
    version="0.1",
    description="Exonum Python Runtime",
    url="https://github.com/popzxc/exonum-python-backend",
    packages=["exonum_runtime"],
    install_requires=INSTALL_REQUIRES,
    python_requires=PYTHON_REQUIRES,
)
