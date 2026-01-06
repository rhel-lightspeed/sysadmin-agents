# Containerfile for Sysadmin Agents
# Based on official Google ADK deployment patterns
# Compatible with Podman and Docker
#
# Build:
#   podman build -t sysadmin-agents:latest -f Containerfile .
#
# Run:
#   podman run -d \
#     -p 8000:8000 \
#     -e GOOGLE_API_KEY="your-key" \
#     -e LINUX_MCP_USER="admin" \
#     -v ~/.ssh/id_ed25519:/opt/app-root/src/.ssh/id_ed25519:ro \
#     sysadmin-agents:latest

FROM registry.access.redhat.com/ubi9/python-311:latest

# Labels for container metadata
LABEL org.opencontainers.image.title="Sysadmin Agents"
LABEL org.opencontainers.image.description="AI agents for Linux/RHEL system administration using Google ADK"
LABEL org.opencontainers.image.source="https://github.com/your-org/sysadmin-agents"

# Set working directory (UBI images use /opt/app-root/src by default)
WORKDIR /opt/app-root/src

# Copy dependency files first for better layer caching
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies
# Note: Using pip since UBI9 python image has pip pre-installed
# Install google-adk with web UI support and linux-mcp-server
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        "google-adk[web]>=1.18.0" \
        "linux-mcp-server>=0.1.0a0" \
        "pyyaml>=6.0.0" \
        "pydantic-settings>=2.0.0" \
        "aiosqlite>=0.19.0" \
        "python-dotenv>=1.0.0"

# Copy application code
COPY main.py ./
COPY agents/ ./agents/
COPY core/ ./core/

# Create directories for runtime mounts (UBI9 runs as non-root user UID 1001)
# - SSH keys: mounted at runtime for MCP server
# - Config overrides: optional ConfigMap mounts for external configuration
RUN mkdir -p ${HOME}/.ssh && \
    chmod 700 ${HOME}/.ssh && \
    mkdir -p /opt/app-root/config && \
    mkdir -p /opt/app-root/agent-config

# Environment variables with sensible defaults
# All can be overridden at runtime
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Session storage (SQLite by default, can be overridden)
ENV SESSION_SERVICE_URI="sqlite+aiosqlite:///./sessions.db"

# CORS allowed origins (configure for your deployment)
ENV ALLOWED_ORIGINS="*"

# MCP server configuration defaults
# Uses $HOME/.ssh which is /opt/app-root/src/.ssh in UBI9
ENV LINUX_MCP_SSH_KEY_PATH="/opt/app-root/src/.ssh/id_ed25519"
ENV LINUX_MCP_LOG_LEVEL="INFO"
ENV LINUX_MCP_ALLOWED_LOG_PATHS="/var/log/messages,/var/log/secure"

# Config mount paths (for ConfigMap/Secret mounts)
# Mount .env file to /opt/app-root/config/.env for app configuration
ENV CONFIG_PATH="/opt/app-root/config"
# Mount agent config overrides to /opt/app-root/agent-config
ENV AGENT_CONFIG_PATH="/opt/app-root/agent-config"

# Expose the server port
EXPOSE 8000

# Health check using Python (curl not available in UBI9 minimal)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/list-apps')" || exit 1

# Run the FastAPI application using uvicorn
# Following the exact pattern from Google ADK Cloud Run docs
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

