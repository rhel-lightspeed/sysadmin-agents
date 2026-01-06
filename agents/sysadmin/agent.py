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
Sysadmin Orchestrator Agent.

Expert Linux/RHEL system administrator that routes to specialist sub-agents
based on the type of problem the user describes.

Uses YAML for instructions (Agent Config pattern) with sub-agents
imported from Python modules to ensure MCP tools work correctly.
"""

import logging
from pathlib import Path

import yaml

from core.config import settings

logger = logging.getLogger(__name__)

# Path to the configuration file
CONFIG_PATH = Path(__file__).parent / "root_agent.yaml"


def _load_config() -> dict:
    """Load orchestrator configuration from YAML file."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _create_sysadmin_agent():
    """
    Create the sysadmin orchestrator agent.
    
    Creates fresh sub-agent instances to avoid "already has a parent" errors.
    Sub-agents are created with MCP tools via create_agent_with_mcp().
    """
    from pathlib import Path

    from google.adk.agents import Agent

    from core.agent_loader import create_agent_with_mcp

    # Load configuration from YAML
    config = _load_config()

    # Get paths to sub-agent configs
    agents_dir = Path(__file__).parent.parent

    # Create FRESH sub-agent instances (not imported globals)
    # This avoids "already has a parent agent" errors on reload
    rca_sub = create_agent_with_mcp(agents_dir / "rca" / "root_agent.yaml")
    performance_sub = create_agent_with_mcp(agents_dir / "performance" / "root_agent.yaml")
    capacity_sub = create_agent_with_mcp(agents_dir / "capacity" / "root_agent.yaml")
    upgrade_sub = create_agent_with_mcp(agents_dir / "upgrade" / "root_agent.yaml")

    # Create orchestrator with fresh sub-agents
    # The orchestrator doesn't need MCP tools directly - sub-agents have them
    agent = Agent(
        model=config.get("model", settings.DEFAULT_MODEL),
        name=config.get("name", "sysadmin"),
        description=config.get("description", "").strip() if config.get("description") else "",
        instruction=config.get("instruction", "").strip() if config.get("instruction") else "",
        sub_agents=[
            rca_sub,
            performance_sub,
            capacity_sub,
            upgrade_sub,
        ],
    )

    logger.info(f"Sysadmin orchestrator created with {len(agent.sub_agents)} sub-agents")
    return agent


# Create the sysadmin agent instance
sysadmin_agent = _create_sysadmin_agent()

# Alias for ADK web discovery
root_agent = sysadmin_agent
