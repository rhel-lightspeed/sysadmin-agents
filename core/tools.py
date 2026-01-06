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

Note: For most use cases, use create_agent_with_mcp() from agent_loader.py
which handles MCP toolset creation automatically.
"""

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_mcp_toolset() -> Any | None:
    """
    Get the MCP toolset instance (lazily initialized, cached).

    Uses lru_cache for thread-safe singleton pattern instead of
    global mutable state.

    Returns:
        McpToolset instance, or None if not available.
    """
    try:
        from core.mcp import create_mcp_toolset

        toolset = create_mcp_toolset()
        if toolset:
            logger.info("MCP toolset initialized successfully")
        return toolset
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
