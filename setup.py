#!/usr/bin/env python3
from setuptools import setup
from auto_openapi_tests._version import __version__

setup(
    name="auto-openapi-tests",
    version=__version__,
    description="Automatic testing suite for services that implement an OpenAPI interface",
    author="Jonas Opitz",
    author_email="jonas.opitz@gwdg.de",
    packages=["auto_openapi_tests"],
    install_requires=[
        d for d in open("requirements.txt").readlines() if not d.startswith("--")
    ],
    package_dir={"": "."},
    entry_points={
        "console_scripts": ["auto-openapi-tests = auto_openapi_tests.run:main"]
    },
)
