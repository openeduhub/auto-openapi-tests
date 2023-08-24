import argparse
import sys

import pytest

from auto_openapi_tests._version import __version__


def run(api: str, openapi_loc: str) -> int | pytest.ExitCode:
    print(f"running on {api}")
    return pytest.main(
        ["-s", "tests/test_service.py", "--api", api, "--spec-loc", openapi_loc]
    )


def main():
    # define CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api",
        action="store",
        help="The full location to send requests to the API to",
        type=str,
    )
    parser.add_argument(
        "--spec-loc",
        action="store",
        default="openapi.json",
        help="The subdomain of the API that returns the OpenAPI specification",
        type=str,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )

    # read passed CLI arguments
    args = parser.parse_args()

    sys.exit(run(args.api, args.spec_loc))


if __name__ == "__main__":
    main()
