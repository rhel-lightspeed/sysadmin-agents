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
created programmatically to ensure MCP tools work correctly.

Architecture:
- Orchestrator routes via transfer_to_agent (no planner needed - it's a router, not a worker)
- Sub-agents: RCA, Performance, Capacity, Upgrade, Security (these do the actual work)
- Transfer control: Sub-agents can't route to peers (only back to orchestrator)

NOTE: PlanReActPlanner is NOT used on the orchestrator because:
- Orchestrator's job is to ROUTE (transfer_to_agent), not to plan/execute/answer
- PlanReActPlanner expects a FINAL_ANSWER, but orchestrator just transfers
- Using PlanReActPlanner on a router causes output format issues
"""

import logging
from pathlib import Path

import yaml

from google.adk.agents import Agent

from core.agent_loader import create_agent_with_mcp
from core.callbacks import create_callbacks_for_agent
from core.config import settings

logger = logging.getLogger(__name__)

# Path to the configuration file
CONFIG_PATH = Path(__file__).parent / "root_agent.yaml"


def _load_config() -> dict:
    """Load orchestrator configuration from YAML file."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _init_agent() -> Agent:
    """
    Initialize the sysadmin orchestrator agent.

    Following ADK Java pattern: static initAgent() factory method.
    Creates fresh sub-agent instances to avoid "already has a parent" errors.

    Sub-agent transfer restrictions:
    - disallow_transfer_to_peers=True: Can't route directly to sibling agents
    - disallow_transfer_to_parent=False (default): CAN return to orchestrator
    """
    config = _load_config()
    agents_dir = Path(__file__).parent.parent

    # Create fresh sub-agent instances for this orchestrator
    # Each sub-agent gets:
    # - MCP tools for system interaction
    # - PlanReActPlanner for structured reasoning (model-agnostic)
    # - Callbacks for security (rate limiting, input validation, safety)
    # - Transfer restriction: can't route to peers, only back to orchestrator
    rca_sub = create_agent_with_mcp(
        agents_dir / "rca" / "root_agent.yaml",
        use_planner=True,  # Sub-agents execute tools and produce answers
        disallow_transfer_to_peers=True,
    )
    performance_sub = create_agent_with_mcp(
        agents_dir / "performance" / "root_agent.yaml",
        use_planner=True,  # Sub-agents execute tools and produce answers
        disallow_transfer_to_peers=True,
    )
    capacity_sub = create_agent_with_mcp(
        agents_dir / "capacity" / "root_agent.yaml",
        use_planner=True,  # Sub-agents execute tools and produce answers
        disallow_transfer_to_peers=True,
    )
    upgrade_sub = create_agent_with_mcp(
        agents_dir / "upgrade" / "root_agent.yaml",
        use_planner=True,  # Sub-agents execute tools and produce answers
        disallow_transfer_to_peers=True,
    )
    security_sub = create_agent_with_mcp(
        agents_dir / "security" / "root_agent.yaml",
        use_planner=True,  # Sub-agents execute tools and produce answers
        disallow_transfer_to_peers=True,
    )

    # Get callbacks for the orchestrator
    callbacks = create_callbacks_for_agent(include_safety=True)

    # Create the orchestrator agent
    # NOTE: No planner for orchestrator - it's a router that uses transfer_to_agent
    # PlanReActPlanner is for agents that execute tools and produce final answers
    agent = Agent(
        model=config.get("model", settings.DEFAULT_MODEL),
        name=config.get("name", "sysadmin"),
        description=config.get("description", "").strip() if config.get("description") else "",
        instruction=config.get("instruction", "").strip() if config.get("instruction") else "",
        sub_agents=[rca_sub, performance_sub, capacity_sub, upgrade_sub, security_sub],
        **callbacks,
    )

    logger.info(f"Sysadmin orchestrator created with {len(agent.sub_agents)} sub-agents")
    return agent


# ADK pattern: module-level root_agent (like Java's public static final ROOT_AGENT)
root_agent = _init_agent()

# Alias for convenience
sysadmin_agent = root_agent
