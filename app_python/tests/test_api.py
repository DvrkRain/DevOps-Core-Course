import os
import sys

import pytest
from fastapi.testclient import TestClient

SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, SRC_PATH)

from src.app import app


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def client():
    """Provide a fresh TestClient for each test."""
    return TestClient(app)


# ----------------------------------------------------------------------
# Tests for GET /
# ----------------------------------------------------------------------

def test_root_status_code(client):
    """Root endpoint must return HTTP 200 OK."""
    response = client.get("/")
    assert response.status_code == 200


def test_root_response_structure(client):
    """Root endpoint must contain all expected top-level sections."""
    response = client.get("/")
    data = response.json()
    expected_sections = {"service", "system", "runtime", "request", "endpoints"}
    assert expected_sections.issubset(data.keys())


def test_root_service_info(client):
    """Check 'service' section fields and types."""
    response = client.get("/")
    service = response.json()["service"]

    assert service["name"] == "devops-info-service"
    assert service["version"] == "1.0.0"
    assert isinstance(service["description"], str)
    assert service["framework"] == "FastAPI"


def test_root_system_info(client):
    """System information must contain required fields with correct types."""
    response = client.get("/")
    system = response.json()["system"]

    expected_fields = {
        "hostname", "platform", "platform_version",
        "architecture", "cpu_count", "python_version"
    }
    assert expected_fields.issubset(system.keys())
    assert isinstance(system["hostname"], str)
    assert isinstance(system["cpu_count"], int)


def test_root_runtime_info(client):
    """Runtime information must contain uptime and current time."""
    response = client.get("/")
    runtime = response.json()["runtime"]

    assert "uptime_seconds" in runtime
    assert "uptime_human" in runtime
    assert "current_time" in runtime
    assert isinstance(runtime["uptime_seconds"], int)
    assert isinstance(runtime["uptime_human"], str)
    assert isinstance(runtime["current_time"], str)


def test_root_request_info(client):
    """
    Request information must reflect the incoming request.
    We simulate a custom User-Agent and verify that the endpoint returns it.
    """
    test_user_agent = "pytest-agent/1.0"
    response = client.get("/", headers={"User-Agent": test_user_agent})
    req_info = response.json()["request"]

    assert req_info["user_agent"] == test_user_agent
    assert req_info["method"] == "GET"
    assert req_info["path"] == "/"
    # Client IP is usually "testclient" when using TestClient; just check it exists
    assert isinstance(req_info["client_ip"], str)


def test_root_endpoints_list(client):
    """The / endpoint must list all available endpoints."""
    response = client.get("/")
    endpoints = response.json()["endpoints"]

    expected = [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/docs", "method": "GET", "description": "OpenAPI documentation"},
        {"path": "/redoc", "method": "GET", "description": "ReDoc documentation"},
    ]
    assert endpoints == expected


# ----------------------------------------------------------------------
# Tests for GET /health
# ----------------------------------------------------------------------

def test_health_status_code(client):
    """Health endpoint must return HTTP 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_fields(client):
    """Health response must contain status, timestamp, and uptime."""
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)


def test_health_uptime_non_negative(client):
    """Uptime should be a non-negative integer."""
    response = client.get("/health")
    assert response.json()["uptime_seconds"] >= 0


# ----------------------------------------------------------------------
# Test for 404 Not Found
# ----------------------------------------------------------------------

def test_404_error_handler(client):
    """Request to a non-existent endpoint returns custom 404 JSON."""
    response = client.get("/i-do-not-exist")
    assert response.status_code == 404
    data = response.json()

    assert data["error"] == "Not Found"
    assert "does not exist" in data["message"]
    assert "available_endpoints" in data
    assert "/" in data["available_endpoints"]
    assert "/health" in data["available_endpoints"]