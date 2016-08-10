"""Helper to launch unit test and coverage."""

import os
import sys

import pytest
import coverage


def run():
    """Run all tests."""
    os.environ['PROJETY_CONFIG'] = 'testing'

    # start coverage engine
    cov = coverage.Coverage(branch=True)
    cov.start()

    # run tests
    ok = pytest.main(['--ignore', 'venv/', '-v', '-x'])

    # print coverage report
    cov.stop()
    print('')
    cov.report(omit=['manage.py', 'tests/*', 'venv*/*'])

    sys.exit(0 if ok else 1)
