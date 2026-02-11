"""Pytest configuration and fixtures for testing the FastAPI application."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from app import app


@pytest.fixture
def client():
    """
    Create a FastAPI TestClient for testing endpoints.

    This fixture provides a test client that can be used to make
    HTTP requests to the FastAPI application without running a server.
    """
    return TestClient(app)
