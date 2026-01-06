"""
MCP (Model Context Protocol) utilities for linux-mcp-server integration.

Provides shared configuration and connection utilities for all agents.

The MCP server allows agents to execute commands on remote Linux systems
via SSH using the linux-mcp-server package.

ADK Pattern Notes:
- McpToolset is instantiated synchronously at agent definition time
- The toolset manages the MCP server lifecycle internally
- Use StdioConnectionParams with StdioServerParameters for local MCP servers
"""

import logging
import os
import shutil
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
        logger.debug(f"SSH key not found: {ssh_key_path}")

    if settings.LINUX_MCP_USER:
        env["LINUX_MCP_USER"] = settings.LINUX_MCP_USER

    if settings.LINUX_MCP_KEY_PASSPHRASE:
        env["LINUX_MCP_KEY_PASSPHRASE"] = settings.LINUX_MCP_KEY_PASSPHRASE

    if settings.LINUX_MCP_ALLOWED_LOG_PATHS:
        env["LINUX_MCP_ALLOWED_LOG_PATHS"] = settings.LINUX_MCP_ALLOWED_LOG_PATHS

    return env


def _get_stdio_server_params() -> Any:
    """
    Get StdioServerParameters for linux-mcp-server.

    Returns:
        StdioServerParameters configured for linux-mcp-server.

    Raises:
        ImportError: If mcp package is not installed.
    """
    try:
        from mcp import StdioServerParameters
    except ImportError:
        # Try alternative import path for older mcp versions
        from mcp.client.stdio import StdioServerParameters

    return StdioServerParameters(
        command="linux-mcp-server",
        env=get_mcp_env(),
    )


def create_mcp_toolset() -> Any | None:
    """
    Create an McpToolset connected to linux-mcp-server.

    This follows the ADK pattern for MCP integration:
    1. Create StdioServerParameters with command and env
    2. Wrap in StdioConnectionParams
    3. Pass to McpToolset constructor

    Returns:
        McpToolset instance, or None if creation fails.

    Note:
        Per ADK documentation: When deploying agents with MCP tools,
        the agent and its McpToolset must be defined synchronously.
        This function is designed for synchronous agent definition.

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
        # Get the server parameters
        server_params = _get_stdio_server_params()

        # Try the preferred ADK pattern: McpToolset with StdioConnectionParams
        try:
            from google.adk.tools.mcp_tool import McpToolset
            from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

            connection_params = StdioConnectionParams(server_params=server_params)
            toolset = McpToolset(connection_params=connection_params)
            logger.info("McpToolset created with StdioConnectionParams")
            return toolset
        except ImportError:
            pass

        # Fallback: Try direct McpToolset import (some ADK versions)
        try:
            from google.adk.tools import McpToolset

            toolset = McpToolset(connection_params=server_params)
            logger.info("McpToolset created (direct import)")
            return toolset
        except ImportError:
            pass

        # Last resort: Try deprecated MCPToolset (older ADK versions)
        try:
            from google.adk.tools import MCPToolset

            toolset = MCPToolset(connection_params=server_params)
            logger.warning("Using deprecated MCPToolset - consider upgrading google-adk")
            return toolset
        except ImportError:
            pass

        logger.error("No compatible McpToolset class found in google-adk")
        return None

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
    result: dict[str, Any] = {
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
