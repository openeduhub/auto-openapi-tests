import argparse
import os
import sys
from typing import Literal, Optional

import pytest

from auto_openapi_tests._version import __version__


def run(
    api: str,
    openapi_loc: str,
    skip_endpoints: list[str],
    max_examples: int,
    derandomize: bool,
    cache_dir: Optional[str] | Literal["disabled"] = None,
) -> int | pytest.ExitCode:
    cache_dir = (
        os.environ.get("PYTEST_CACHE_DIR", ".pytest_cache")
        if not cache_dir
        else cache_dir
    )

    if cache_dir == "disabled":
        cache_args = ["-p", "no:cacheprovider"]
    else:
        cache_args = ["-o", f"cache_dir={cache_dir}"]
    return pytest.main(
        [
            "-s",
            "tests/test_service.py",
            "--api",
            api,
            "--spec-loc",
            openapi_loc,
            "--skip-endpoints",
            str(skip_endpoints),
            "--max-examples",
            max_examples,
            "--derandomize",
            derandomize,
        ]
        + cache_args
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
        default="/openapi.json",
        help="The subdomain of the API that returns the OpenAPI specification",
        type=str,
    )
    parser.add_argument(
        "--skip-endpoints",
        action="store",
        nargs="*",
        default=[],
        help="The end-points of the API to not test",
        type=str,
    )
    parser.add_argument(
        "--cache-dir",
        action="store",
        default=".cache",
        help="The cache directory to be used. Set to 'disabled' to disable caching.",
    )
    parser.add_argument(
        "--max-examples",
        action="store",
        default=100,
        help="The maximum number of examples generated by Hypothesis.",
    )
    parser.add_argument(
        "--derandomize",
        action="store",
        default=False,
        help="Whether to randomly draw the examples by Hypothesis.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )

    # read passed CLI arguments
    args = parser.parse_args()

    sys.exit(
        run(
            api=args.api,
            openapi_loc=args.spec_loc,
            skip_endpoints=args.skip_endpoints,
            cache_dir=args.cache_dir,
            max_examples=args.max_examples,
            derandomize=args.derandomize,
        )
    )


if __name__ == "__main__":
    main()
