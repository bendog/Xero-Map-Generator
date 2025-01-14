import unittest

# import argparse
import pytest


def pytest_addoption(parser):
    # parser.addoption("--enable-debug", action="store_true", default=False, help="debug tests")
    # parser.addoption("--run-slow", action="store_true", default=False, help="run slow tests")
    # parser.addoption("--run-local", action="store_true", default=False, help="run slow tests")
    pass


def pytest_collection_modifyitems(config, items):
    # skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    # skip_local = pytest.mark.skip(reason="need --runlocal option to tun")
    # if not config.getoption("--run-slow"):
    #     for item in items:
    #         if "slow" in item.keywords:
    #             item.add_marker(skip_slow)
    # if not config.getoption('--run-local'):
    #     for item in items:
    #         if "local" in item.keywords:
    #             item.add_marker(skip_local)
    pass


@pytest.fixture(scope="class")
def debug(request):
    response = request.config.getoption("--debug")
    request.cls.debug = response
