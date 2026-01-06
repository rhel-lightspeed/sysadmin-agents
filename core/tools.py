# Copyright 2025 Sysadmin Agents Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tools for sysadmin agents.

Provides MCP toolset wrapped for use with ADK Agent Config.
This module exposes tools that can be referenced in YAML agent configs.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Global MCP toolset instance (lazily initialized)
_mcp_toolset = None


def get_mcp_toolset() -> Any:
    """
    Get the MCP toolset instance (lazily initialized).

    Returns:
        MCPToolset or McpToolset instance, or None if not available.
    """
    global _mcp_toolset

    if _mcp_toolset is not None:
        return _mcp_toolset

    try:
        from core.mcp import create_mcp_toolset

        _mcp_toolset = create_mcp_toolset()
        return _mcp_toolset
    except Exception as e:
        logger.warning(f"Could not create MCP toolset: {e}")
        return None


def linux_mcp_tools() -> list[Any]:
    """
    Get the list of MCP tools for linux-mcp-server.

    This function returns a list suitable for use in Agent Config tools section.

    Returns:
        List containing the MCP toolset, or empty list if not available.
    """
    toolset = get_mcp_toolset()
    if toolset:
        return [toolset]
    return []
