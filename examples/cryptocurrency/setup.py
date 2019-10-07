#!/usr/bin/env python
"""Setup Script for the Exonum Python Cryptocurrency Service."""
import setuptools

# INSTALL_REQUIRES = ["exonum_runtime"]
INSTALL_REQUIRES = []

PYTHON_REQUIRES = ">=3.7"

with open("README.md", "r") as readme:
    LONG_DESCRIPTION = readme.read()

setuptools.setup(
    name="exonum-python-cryptocurrency",
    version="0.1.0",
    author="The Exonum team",
    author_email="contact@exonum.com",
    description="Exonum Python Runtime",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/popzxc/exonum-python-backend",
    packages=setuptools.find_packages(),
    install_requires=INSTALL_REQUIRES,
    python_requires=PYTHON_REQUIRES,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
    ],
)
