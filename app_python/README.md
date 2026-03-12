# DevOps Info Service

![CI](https://github.com/DvrkRain/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)
[![codecov](https://codecov.io/gh/DvrkRain/DevOps-Core-Course/branch/lab03/graph/badge.svg)](https://codecov.io/gh/DvrkRain/DevOps-Core-Course)
[![Ansible Deployment](https://github.com/DvrkRain/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/DvrkRain/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

A FastAPI web service that provides comprehensive system information and health status.

## Overview

This service is designed as part of the DevOps Engineering course. It provides:
- System information (hostname, platform, architecture, etc.)
- Runtime information (uptime, current time)
- Health check endpoint for monitoring
- Automatic OpenAPI documentation

## Prerequisites

- Python 3.14 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DvrkRain/DevOps-Core-Course.git
cd app_python
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

### Default configuration:
```bash
cd src
python app.py
```

Server starts at: http://localhost:5000

### Custom configuration using environment variables:
```bash
PORT=8080 python app.py
```
```bash
HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py
```

## API Endpoints
### `GET /`
Returns comprehensive service and system information.

Example Response:

```json
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "FastAPI"
    },
    "system": {
        "hostname": "claymix",
        "platform": "Windows",
        "platform_version": "10.0.26100",
        "architecture": "AMD64",
        "cpu_count": 12,
        "python_version": "3.14.2"
    },
    "runtime": {
        "uptime_seconds": 3,
        "uptime_human": "0 hours, 0 minutes",
        "current_time": "2026-01-22T21:17:24.835416+00:00",
        "timezone": "UTC"
    },
    "request": {
        "client_ip": "127.0.0.1",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "method": "GET",
        "path": "/"
    },
    "endpoints": [
        {
            "path": "/",
            "method": "GET",
            "description": "Service information"
        },
        {
            "path": "/health",
            "method": "GET",
            "description": "Health check"
        },
        {
            "path": "/docs",
            "method": "GET",
            "description": "OpenAPI documentation"
        },
        {
            "path": "/redoc",
            "method": "GET",
            "description": "ReDoc documentation"
        }
    ]
}
```

### `GET /health`
Health check endpoint for monitoring.

Example Response:

```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T14:30:00.000Z",
    "uptime_seconds": 3600
}
```

### `GET /docs`
Interactive OpenAPI/Swagger documentation.

### `GET /redoc`
Alternative API documentation.

## Configuration

| Variable | Default | Description |
| -------- | ------- | ----------- |
| HOST | 0.0.0.0 | Host to bind the server |
| PORT | 5000 | Port to listen on |
| DEBUG | False | Enable debug mode with auto-reload |

## Testing

### Running Tests Locally

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=term --cov-report=html

# Run tests only
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v
```

Test endpoints using curl:

``` bash
# Main endpoint
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health

# Pretty-print JSON
curl http://localhost:5000/ | python -m json.tool
```

## Development
### Project Structure
```text
app_python
|   .coverage
|   .coveragerc
|   .dockerignore
|   .gitignore
|   Dockerfile
|   README.md
|   requirements.txt
|   ruff.toml
|   tree.txt
|   
+---docs
|   |   LAB01.md
|   |   LAB02.md
|   |   LAB03.md
|   |   
|   \---screenshots
|           01-main-endpoint.png
|           02-health-check.png
|           03-formatted-output.png
|           04-docker-build.png
|           05-docker-run.png
|           06-container-endpoint-test.png
|           07-docker-hub.png
|           
+---src
|   \---app.py
|       __init__.py
|           
\---tests
        conftest.py
        test_api.py
        __init__.py

```

## Docker

### Building the Image

```bash
docker build -t timursalakhov/devops-info-service:latest .
```

### Running the Container

```bash
# Run with default settings
docker run -d -p 5000:5000 timursalakhov/devops-info-service:latest

# Run with custom port
docker run -d -p 8080:5000 timursalakhov/devops-info-service:latest

# Run with environment variables
docker run -d -p 5000:5000 -e DEBUG=True timursalakhov/devops-info-service:latest
```

### Pulling from Docker Hub

```bash
docker pull timursalakhov/devops-info-service:latest
docker run -d -p 5000:5000 timursalakhov/devops-info-service:latest
```

### Useful Commands

```bash
# View logs
docker logs <container-id>

# View logs in real-time
docker logs -f <container-id>

# Stop container
docker stop <container-id>

# Remove container
docker rm <container-id>

# Stop and remove in one command
docker rm -f <container-id>
```

### Docker Hub Repository

The image is available at: `https://hub.docker.com/r/timursalakhov/devops-info-service`

## CI/CD

This project uses GitHub Actions for continuous integration and deployment. The CI pipeline:
- Runs linting with Ruff
- Executes all unit tests with pytest
- Generates test coverage reports
- Performs security scanning with Snyk
- Builds and pushes Docker images to Docker Hub with CalVer versioning

See [docs/LAB03.md](docs/LAB03.md) for detailed CI/CD documentation.

## License
Educational project for DevOps Engineering course.
