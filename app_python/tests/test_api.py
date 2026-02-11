"""
Unit tests for DevOps Info Service API endpoints.

Tests cover:
- GET / - Service information endpoint
- GET /health - Health check endpoint
- Error handling (404 responses)
"""



class TestServiceInfoEndpoint:
    """Tests for the main service information endpoint (GET /)."""

    def test_service_info_success(self, client):
        """Test successful response from service info endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_service_info_structure(self, client):
        """Test that response contains all required top-level sections."""
        response = client.get("/")
        data = response.json()

        # Check all required sections exist
        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "endpoints" in data

    def test_service_section_fields(self, client):
        """Test service section contains required fields."""
        response = client.get("/")
        service = response.json()["service"]

        assert "name" in service
        assert "version" in service
        assert "description" in service
        assert "framework" in service

        # Validate specific values
        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["framework"] == "FastAPI"

    def test_system_section_fields(self, client):
        """Test system section contains required fields."""
        response = client.get("/")
        system = response.json()["system"]

        required_fields = [
            "hostname",
            "platform",
            "platform_version",
            "architecture",
            "cpu_count",
            "python_version"
        ]

        for field in required_fields:
            assert field in system, f"Missing field: {field}"
            assert system[field] is not None, f"Field {field} is None"

        # Validate types
        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["cpu_count"], int)
        assert system["cpu_count"] > 0

    def test_runtime_section_fields(self, client):
        """Test runtime section contains required fields."""
        response = client.get("/")
        runtime = response.json()["runtime"]

        required_fields = [
            "uptime_seconds",
            "uptime_human",
            "current_time",
            "timezone"
        ]

        for field in required_fields:
            assert field in runtime, f"Missing field: {field}"

        # Validate types
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0
        assert isinstance(runtime["uptime_human"], str)
        assert isinstance(runtime["current_time"], str)
        assert runtime["timezone"] == "UTC"

    def test_request_section_fields(self, client):
        """Test request section contains client information."""
        response = client.get("/")
        request_info = response.json()["request"]

        required_fields = ["client_ip", "user_agent", "method", "path"]

        for field in required_fields:
            assert field in request_info, f"Missing field: {field}"

        # Validate specific values
        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"

    def test_endpoints_section_structure(self, client):
        """Test endpoints section lists available endpoints."""
        response = client.get("/")
        endpoints = response.json()["endpoints"]

        assert isinstance(endpoints, list)
        assert len(endpoints) > 0

        # Check first endpoint structure
        endpoint = endpoints[0]
        assert "path" in endpoint
        assert "method" in endpoint
        assert "description" in endpoint

        # Verify at least the main endpoints are listed
        paths = [ep["path"] for ep in endpoints]
        assert "/" in paths
        assert "/health" in paths


class TestHealthCheckEndpoint:
    """Tests for the health check endpoint (GET /health)."""

    def test_health_check_success(self, client):
        """Test successful health check response."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_health_check_structure(self, client):
        """Test health check response contains required fields."""
        response = client.get("/health")
        data = response.json()

        required_fields = ["status", "timestamp", "uptime_seconds"]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_health_check_status(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_check_uptime(self, client):
        """Test health check includes valid uptime."""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

    def test_health_check_timestamp(self, client):
        """Test health check includes valid timestamp."""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["timestamp"], str)
        # Verify it looks like an ISO timestamp (basic check)
        assert "T" in data["timestamp"]
        assert data["timestamp"].endswith("+00:00") or data["timestamp"].endswith("Z")


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_404_not_found(self, client):
        """Test 404 error for non-existent endpoint."""
        response = client.get("/nonexistent")

        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"

    def test_404_error_structure(self, client):
        """Test 404 error response contains helpful information."""
        response = client.get("/invalid-path")
        data = response.json()

        assert "error" in data
        assert "message" in data
        assert "available_endpoints" in data

        # Verify error message is helpful
        assert "Not Found" in data["error"]
        assert isinstance(data["available_endpoints"], list)

    def test_invalid_method(self, client):
        """Test that POST to GET-only endpoint returns 405."""
        response = client.post("/")

        # FastAPI returns 405 Method Not Allowed for invalid methods
        assert response.status_code == 405


class TestConcurrentRequests:
    """Tests for handling multiple concurrent requests."""

    def test_multiple_health_checks(self, client):
        """Test multiple health check requests return consistent results."""
        responses = [client.get("/health") for _ in range(5)]

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    def test_uptime_increases(self, client):
        """Test that uptime increases over time."""
        import time

        response1 = client.get("/health")
        uptime1 = response1.json()["uptime_seconds"]

        # Wait a small amount of time
        time.sleep(0.1)

        response2 = client.get("/health")
        uptime2 = response2.json()["uptime_seconds"]

        # Uptime should be greater or equal (may be same if < 1 second passed)
        assert uptime2 >= uptime1


class TestDataValidation:
    """Tests for data type validation and consistency."""

    def test_cpu_count_positive(self, client):
        """Test that CPU count is a positive integer."""
        response = client.get("/")
        cpu_count = response.json()["system"]["cpu_count"]

        assert isinstance(cpu_count, int)
        assert cpu_count > 0

    def test_hostname_not_empty(self, client):
        """Test that hostname is not empty."""
        response = client.get("/")
        hostname = response.json()["system"]["hostname"]

        assert isinstance(hostname, str)
        assert len(hostname) > 0

    def test_version_format(self, client):
        """Test that service version follows semantic versioning."""
        response = client.get("/")
        version = response.json()["service"]["version"]

        assert isinstance(version, str)
        # Basic semver check (X.Y.Z)
        parts = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)
