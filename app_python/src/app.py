import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pythonjsonlogger import jsonlogger

# Configuration from environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"


def _configure_logging() -> logging.Logger:
    """Configure root logger to emit structured JSON on stdout."""
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    return logging.getLogger(__name__)


logger = _configure_logging()

# FastAPI application
app = FastAPI(
    title="DevOps Info Service",
    version="1.0.0",
    description="Service providing system information and health status",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application start time
START_TIME = datetime.now(timezone.utc)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Emit one structured JSON log line per HTTP request/response."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "http request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": client_ip,
            "duration_ms": duration_ms,
        },
    )
    return response


def get_uptime() -> dict[str, Any]:
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


@app.get("/", response_class=JSONResponse)
async def get_service_information(request: Request) -> dict[str, Any]:
    """Main endpoint — returns comprehensive service and system information."""
    uptime_info = get_uptime()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 0,
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime_info["seconds"],
            "uptime_human": uptime_info["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/docs", "method": "GET", "description": "OpenAPI documentation"},
            {"path": "/redoc", "method": "GET", "description": "ReDoc documentation"},
        ],
    }

    return response


@app.get("/health", response_class=JSONResponse)
async def health_check() -> dict[str, Any]:
    """Health check endpoint for monitoring and Kubernetes probes."""
    uptime_info = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_info["seconds"],
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 error handler."""
    logger.error(
        "not found",
        extra={"path": request.url.path, "status_code": 404},
    )
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested endpoint {request.url.path} does not exist",
            "available_endpoints": ["/", "/health", "/docs", "/redoc"],
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 error handler."""
    logger.error(
        "internal server error",
        extra={"status_code": 500, "detail": str(exc)},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(
        "starting devops info service",
        extra={"host": HOST, "port": PORT, "debug": DEBUG},
    )
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info",
    )
