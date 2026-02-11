import logging
import os
import platform
import socket
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configuration from environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# FastAPI application
app = FastAPI(
    title="DevOps Info Service",
    version="1.0.0",
    description="Service providing system information and health status",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (optional, useful for web frontend later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application start time
START_TIME = datetime.now(timezone.utc)


def get_uptime() -> dict[str, Any]:
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


@app.get("/", response_class=JSONResponse)
async def get_service_information(request: Request) -> dict[str, Any]:
    """
    Main endpoint - returns comprehensive service and system information.
    """
    logger.info(f"Request received: {request.method} {request.url.path}")

    # Collect all information
    uptime_info = get_uptime()

    # Prepare response
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
    """
    Health check endpoint for monitoring and Kubernetes probes.
    """
    uptime_info = get_uptime()

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_info["seconds"],
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 error handler."""
    logger.error(f"Not found server error: {exc}")
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
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")

    uvicorn.run(
        "app:app", host=HOST, port=PORT, reload=DEBUG, log_level="debug" if DEBUG else "info"
    )
