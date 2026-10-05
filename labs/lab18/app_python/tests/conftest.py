"""Pytest configuration and fixtures for testing the FastAPI application."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set DATA_DIR to a temp directory before importing the app module,
# so the visits counter doesn't write to the real /data path during tests.
_test_data_dir = tempfile.mkdtemp(prefix="devops_test_")
os.environ["DATA_DIR"] = _test_data_dir

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from app import app


@pytest.fixture(autouse=True)
def _clean_visits_file():
    """Remove the visits file before each test for isolation."""
    visits_path = os.path.join(_test_data_dir, "visits")
    if os.path.exists(visits_path):
        os.remove(visits_path)
    yield


@pytest.fixture
def client():
    """
    Create a FastAPI TestClient for testing endpoints.

    This fixture provides a test client that can be used to make
    HTTP requests to the FastAPI application without running a server.
    """
    return TestClient(app)


def pytest_sessionfinish(session, exitstatus):
    """Clean up the temporary data directory after all tests complete."""
    shutil.rmtree(_test_data_dir, ignore_errors=True)
