import pytest
import hypothesis


def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--api", action="store")
    parser.addoption("--spec-loc", action="store", default="openapi.json")
    parser.addoption("--skip-endpoints", action="store", default=[])
    parser.addoption("--max-examples", action="store", default=100, type=int)
    parser.addoption("--derandomize", action="store", default=False, type=bool)


def pytest_cmdline_main(config: pytest.Config):
    hypothesis.settings.register_profile(
        "custom_profile",
        max_examples=config.option.max_examples,
        derandomize=config.option.derandomize,
        deadline=None,
    )
    hypothesis.settings.load_profile("custom_profile")


def pytest_generate_tests(metafunc: pytest.Metafunc):
    for option in ["api", "spec_loc", "skip_endpoints"]:
        if (
            option in metafunc.fixturenames
            or metafunc.function.__name__ == "test_end_points_success"
        ):
            metafunc.parametrize(option, [getattr(metafunc.config.option, option)])
