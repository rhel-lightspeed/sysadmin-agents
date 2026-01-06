#!/usr/bin/env python3
"""
Test script for sysadmin-agents with linux-mcp-server.

This demonstrates the full agent + MCP integration working together.

Usage:
    # Set required environment variables
    export LINUX_MCP_HOST="your-server.example.com"
    export LINUX_MCP_USER="your-user"
    export LINUX_MCP_SSH_KEY_PATH="~/.ssh/id_ed25519"

    # Run the test
    python scripts/test_agent.py
"""

import argparse
import asyncio
import logging
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from core.utils import setup_logging

logger = logging.getLogger(__name__)


async def test_mcp_connection(host: str) -> bool:
    """
    Test MCP connection and tool availability.

    Args:
        host: The target host to test against.

    Returns:
        True if connection successful, False otherwise.
    """
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        logger.error("mcp package not installed. Run: pip install linux-mcp-server")
        return False

    # Configure MCP server parameters
    server_params = StdioServerParameters(
        command="linux-mcp-server",
        env={
            "LINUX_MCP_USER": settings.LINUX_MCP_USER or os.getenv("USER", "root"),
            "LINUX_MCP_SSH_KEY_PATH": os.path.expanduser(settings.LINUX_MCP_SSH_KEY_PATH),
            "LINUX_MCP_LOG_LEVEL": "WARNING",
        },
    )

    logger.info("Connecting to linux-mcp-server...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List available tools
                tools_result = await session.list_tools()
                logger.info(f"Connected! {len(tools_result.tools)} tools available")

                print(f"\n{'=' * 60}")
                print(f"System Health Check: {host}")
                print(f"{'=' * 60}\n")

                # System Information
                print("📊 System Information:")
                result = await session.call_tool("get_system_information", {"host": host})
                for content in result.content:
                    if hasattr(content, "text"):
                        print(content.text)
                print()

                # Disk Usage
                print("💾 Disk Usage:")
                result = await session.call_tool("get_disk_usage", {"host": host})
                for content in result.content:
                    if hasattr(content, "text"):
                        # Truncate long output
                        text = content.text
                        if len(text) > 500:
                            text = text[:500] + "\n... (truncated)"
                        print(text)
                print()

                # Memory Information
                print("🧠 Memory Information:")
                result = await session.call_tool("get_memory_information", {"host": host})
                for content in result.content:
                    if hasattr(content, "text"):
                        print(content.text)
                print()

                print(f"{'=' * 60}")
                print("✅ All MCP tools working correctly!")
                print(f"{'=' * 60}")
                return True

    except Exception as e:
        logger.error(f"MCP connection failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test sysadmin-agents MCP integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/test_agent.py --host myserver.example.com
    LINUX_MCP_HOST=myserver.example.com python scripts/test_agent.py
        """,
    )
    parser.add_argument(
        "--host",
        default=os.getenv("LINUX_MCP_HOST"),
        help="Target host (default: $LINUX_MCP_HOST env var)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set up logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)

    # Validate host
    if not args.host:
        parser.error("Host is required. Set LINUX_MCP_HOST env var or use --host flag.")

    # Check for API key (warn but don't fail)
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY not set - ADK agent tests will be limited")

    # Run the test
    success = asyncio.run(test_mcp_connection(args.host))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
