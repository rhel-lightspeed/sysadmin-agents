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
Capacity and Disk Analysis Specialist Agent.

Analyzes disk usage, identifies space-consuming directories,
and provides cleanup recommendations with safety assessments.

Uses YAML for instructions (Agent Config pattern) with MCP tools
added programmatically to avoid serialization issues.
"""

import logging
from pathlib import Path

from core.agent_loader import create_agent_with_mcp

logger = logging.getLogger(__name__)

# Path to the configuration file
CONFIG_PATH = Path(__file__).parent / "root_agent.yaml"

# Create the capacity agent with MCP tools
# Uses YAML for config, programmatic creation for MCP (ADK workaround)
capacity_agent = create_agent_with_mcp(CONFIG_PATH)
logger.info(f"Capacity agent created: {capacity_agent.name}")

# Alias for ADK web discovery
root_agent = capacity_agent
