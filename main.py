"""
FastAPI entry point for Sysadmin Agents.

This module sets up the FastAPI application using the official Google ADK pattern
from the Cloud Run deployment documentation.

The application serves:
- ADK API Server (RESTful endpoints for agent interaction)
- ADK Web UI (development interface for testing agents)

Configuration sources (in order of precedence):
1. Environment variables (highest priority)
2. Mounted ConfigMap at /opt/app-root/config/.env
3. Local .env file (for development)

Reference:
    https://google.github.io/adk-docs/deploy/cloud-run/
"""

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# =============================================================================
# Load Configuration from Mounted ConfigMap (if present)
# =============================================================================

# Check for mounted .env file from ConfigMap
CONFIG_PATH = os.environ.get("CONFIG_PATH", "/opt/app-root/config")
MOUNTED_ENV_FILE = Path(CONFIG_PATH) / ".env"

if MOUNTED_ENV_FILE.exists():
    # Load environment variables from mounted ConfigMap
    # This allows configuration via Kubernetes ConfigMaps
    try:
        from dotenv import load_dotenv
        load_dotenv(MOUNTED_ENV_FILE)
        print(f"Loaded configuration from: {MOUNTED_ENV_FILE}")
    except ImportError:
        # python-dotenv not installed, skip loading
        print(f"Warning: python-dotenv not installed, skipping {MOUNTED_ENV_FILE}")

# =============================================================================
# Configuration from Environment Variables
# =============================================================================

# Get the directory where main.py is located (contains agents/ subdirectory)
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Session storage URI
# Note: Use 'sqlite+aiosqlite' instead of 'sqlite' because
# DatabaseSessionService requires an async driver
# Can be overridden to use PostgreSQL, etc. in production
SESSION_SERVICE_URI = os.environ.get(
    "SESSION_SERVICE_URI",
    "sqlite+aiosqlite:///./sessions.db"
)

# CORS allowed origins
# Parse from comma-separated string or use default
_allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "*")
if _allowed_origins_str == "*":
    ALLOWED_ORIGINS = ["*"]
else:
    ALLOWED_ORIGINS = [origin.strip() for origin in _allowed_origins_str.split(",")]

# Enable Web UI (set to False for API-only deployment)
SERVE_WEB_INTERFACE = os.environ.get("SERVE_WEB_UI", "true").lower() == "true"

# =============================================================================
# FastAPI Application
# =============================================================================

# Call the function to get the FastAPI app instance
# This is the official ADK pattern for deployment
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)


# =============================================================================
# Entry Point (for local development)
# =============================================================================

if __name__ == "__main__":
    # Use the PORT environment variable, defaulting to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

