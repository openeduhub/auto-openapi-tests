import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--api", action="store")
    parser.addoption("--spec-loc", action="store", default="openapi.json")


def pytest_generate_tests(metafunc: pytest.Metafunc):
    for option in ["api", "spec_loc"]:
        if (
            option in metafunc.fixturenames
            or metafunc.function.__name__ == "test_end_points_success"
        ):
            metafunc.parametrize(option, [getattr(metafunc.config.option, option)])
