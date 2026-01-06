"""
MCP (Model Context Protocol) utilities for linux-mcp-server integration.

Provides shared configuration and connection utilities for all agents.

The MCP server allows agents to execute commands on remote Linux systems
via SSH using the linux-mcp-server package.
"""

import logging
import os
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)


def get_mcp_env() -> dict[str, str]:
    """
    Get environment variables for linux-mcp-server.

    Reads configuration from settings and returns a dictionary
    suitable for passing to StdioServerParameters.

    Returns:
        Dictionary of environment variables for MCP server.

    Environment Variables Used:
        - LINUX_MCP_LOG_LEVEL: Log level for MCP server
        - LINUX_MCP_SSH_KEY_PATH: Path to SSH private key
        - LINUX_MCP_USER: SSH user for remote connections
        - LINUX_MCP_KEY_PASSPHRASE: Optional passphrase for SSH key
        - LINUX_MCP_ALLOWED_LOG_PATHS: Comma-separated paths to allowed logs
    """
    env: dict[str, str] = {
        "LINUX_MCP_LOG_LEVEL": settings.LINUX_MCP_LOG_LEVEL,
    }

    # Expand ~ in SSH key path and validate
    ssh_key_path = os.path.expanduser(settings.LINUX_MCP_SSH_KEY_PATH)
    if os.path.exists(ssh_key_path):
        env["LINUX_MCP_SSH_KEY_PATH"] = ssh_key_path
        logger.debug(f"Using SSH key: {ssh_key_path}")
    else:
        logger.warning(f"SSH key not found: {ssh_key_path}")

    if settings.LINUX_MCP_USER:
        env["LINUX_MCP_USER"] = settings.LINUX_MCP_USER

    if settings.LINUX_MCP_KEY_PASSPHRASE:
        env["LINUX_MCP_KEY_PASSPHRASE"] = settings.LINUX_MCP_KEY_PASSPHRASE

    if settings.LINUX_MCP_ALLOWED_LOG_PATHS:
        env["LINUX_MCP_ALLOWED_LOG_PATHS"] = settings.LINUX_MCP_ALLOWED_LOG_PATHS

    return env


def get_mcp_connection_params() -> Any:
    """
    Get connection parameters for linux-mcp-server.

    Returns a configured StdioServerParameters object that can be
    passed to MCPToolset for tool integration.

    This function handles API variations between different versions
    of the mcp package.

    Returns:
        StdioServerParameters (or equivalent) configured for linux-mcp-server.

    Raises:
        ImportError: If mcp package is not installed.
        RuntimeError: If no compatible connection params class is found.
    """
    # Try to import connection parameters - handle different API versions
    stdio_params_class = None

    # Primary: StdioServerParameters from mcp package
    try:
        from mcp import StdioServerParameters

        stdio_params_class = StdioServerParameters
        logger.debug("Using mcp.StdioServerParameters")
    except ImportError:
        pass

    # Fallback: Try alternative import paths
    if stdio_params_class is None:
        try:
            from mcp.client.stdio import StdioServerParameters

            stdio_params_class = StdioServerParameters
            logger.debug("Using mcp.client.stdio.StdioServerParameters")
        except ImportError:
            pass

    if stdio_params_class is None:
        logger.error("mcp package not installed or incompatible version")
        raise ImportError(
            "mcp package required for MCP integration. Install with: pip install linux-mcp-server"
        )

    return stdio_params_class(
        command="linux-mcp-server",
        env=get_mcp_env(),
    )


def create_mcp_toolset() -> Any | None:
    """
    Create an McpToolset connected to linux-mcp-server.

    This is a convenience function that handles errors gracefully
    and returns None if connection fails. Use this when you want
    optional MCP support (agent works without MCP tools).

    Returns:
        McpToolset instance, or None if creation fails.

    Example:
        ```python
        toolset = create_mcp_toolset()
        if toolset:
            agent = Agent(tools=[toolset], ...)
        else:
            agent = Agent(tools=[], ...)  # No MCP tools
        ```
    """
    try:
        # Try the new McpToolset first (preferred)
        try:
            from google.adk.tools import McpToolset

            connection_params = get_mcp_connection_params()
            toolset = McpToolset(connection_params=connection_params)
            logger.info("McpToolset created successfully")
            return toolset
        except ImportError:
            # Fall back to deprecated MCPToolset for older versions
            from google.adk.tools import MCPToolset

            connection_params = get_mcp_connection_params()
            toolset = MCPToolset(connection_params=connection_params)
            logger.info("MCPToolset created successfully (deprecated)")
            return toolset
    except ImportError as e:
        logger.error(f"Required package not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create MCP toolset: {e}")
        return None


def verify_mcp_installation() -> dict[str, Any]:
    """
    Verify that MCP is properly installed and configured.

    Useful for health checks and diagnostics.

    Returns:
        Dictionary with status information:
        - mcp_installed: bool
        - adk_installed: bool
        - ssh_key_exists: bool
        - linux_mcp_server_available: bool
        - errors: list of error messages
    """
    import shutil

    result = {
        "mcp_installed": False,
        "adk_installed": False,
        "ssh_key_exists": False,
        "linux_mcp_server_available": False,
        "errors": [],
    }

    # Check mcp package
    try:
        import mcp  # noqa: F401

        result["mcp_installed"] = True
    except ImportError as e:
        result["errors"].append(f"mcp not installed: {e}")

    # Check google-adk
    try:
        import google.adk  # noqa: F401

        result["adk_installed"] = True
    except ImportError as e:
        result["errors"].append(f"google-adk not installed: {e}")

    # Check SSH key
    ssh_key_path = os.path.expanduser(settings.LINUX_MCP_SSH_KEY_PATH)
    result["ssh_key_exists"] = os.path.exists(ssh_key_path)
    if not result["ssh_key_exists"]:
        result["errors"].append(f"SSH key not found: {ssh_key_path}")

    # Check linux-mcp-server command
    result["linux_mcp_server_available"] = shutil.which("linux-mcp-server") is not None
    if not result["linux_mcp_server_available"]:
        result["errors"].append("linux-mcp-server command not found in PATH")

    return result
