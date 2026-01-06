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
Agent loader utility following ADK Agent Config patterns.

Loads agents from YAML configuration files with support for:
- Environment variable overrides (model, temperature, etc.)
- Sub-agent resolution
- Callback registration
- MCP tools (via programmatic creation to avoid serialization issues)

NOTE: McpToolset is listed but "not fully supported" in ADK Agent Config YAML.
See: https://google.github.io/adk-docs/agents/config/
This module provides `create_agent_with_mcp()` as a workaround that:
- Uses YAML for instructions/config (Agent Config pattern)
- Creates agents programmatically with MCP tools (avoids serialization issues)
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_agent_from_yaml(config_path: Path):
    """
    Load an agent from an ADK Agent Config YAML file.

    Supports environment variable overrides:
    - AGENT_MODEL: Override the model for all agents
    - AGENT_TEMPERATURE: Override the temperature setting

    Args:
        config_path: Path to the root_agent.yaml file

    Returns:
        Configured ADK Agent instance
    """
    from google.adk.agents import Agent
    from google.adk.agents.llm_agent_config import LlmAgentConfig

    # Load and parse the YAML
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)

    # Apply environment variable overrides
    config_dict = _apply_env_overrides(config_dict)

    # Create the config object
    config = LlmAgentConfig(**config_dict)

    # Create the agent
    return Agent.from_config(config, str(config_path.absolute()))


def _apply_env_overrides(config_dict: dict) -> dict:
    """
    Apply environment variable overrides to the config.

    Supported environment variables:
    - AGENT_MODEL: Override the model (e.g., "gemini-2.0-flash", "gemini-1.5-pro")
    - AGENT_TEMPERATURE: Override temperature (e.g., "0.1", "0.7")
    - DEFAULT_MODEL: Fallback model override (from core.config)

    Args:
        config_dict: The parsed YAML configuration dictionary

    Returns:
        Modified configuration dictionary with overrides applied
    """
    # Model override
    model_override = os.environ.get("AGENT_MODEL")
    if not model_override:
        # Check for DEFAULT_MODEL from settings
        model_override = os.environ.get("DEFAULT_MODEL")

    if model_override:
        original_model = config_dict.get("model", "unknown")
        config_dict["model"] = model_override
        logger.info(f"Model override: {original_model} -> {model_override}")

    # Temperature override
    temp_override = os.environ.get("AGENT_TEMPERATURE")
    if temp_override:
        try:
            temperature = float(temp_override)
            if "generate_content_config" not in config_dict:
                config_dict["generate_content_config"] = {}
            original_temp = config_dict.get("generate_content_config", {}).get(
                "temperature", "default"
            )
            config_dict["generate_content_config"]["temperature"] = temperature
            logger.info(f"Temperature override: {original_temp} -> {temperature}")
        except ValueError:
            logger.warning(f"Invalid AGENT_TEMPERATURE value: {temp_override}")

    return config_dict


def get_agent_config(config_path: Path) -> dict:
    """
    Load and return the raw configuration dictionary from a YAML file.

    Useful for inspecting configuration without creating an agent.

    Args:
        config_path: Path to the root_agent.yaml file

    Returns:
        Configuration dictionary with environment overrides applied
    """
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)

    return _apply_env_overrides(config_dict)


def create_agent_with_mcp(
    config_path: Path,
    include_mcp: bool = True,
    include_callbacks: bool = True,
    use_planner: bool = False,
    disallow_transfer_to_parent: bool = False,
    disallow_transfer_to_peers: bool = False,
) -> Any:
    """
    Create an agent from YAML config with MCP tools and callbacks added programmatically.

    This function provides the ADK-recommended workaround for McpToolset
    serialization issues in Agent Config YAML. It:
    - Uses YAML for instructions/config (Agent Config pattern)
    - Creates agents programmatically with MCP tools (avoids serialization)
    - Applies security callbacks (rate limiting, input validation, safety)
    - Optionally enables PlanReActPlanner for structured reasoning

    See: https://google.github.io/adk-docs/agents/config/
    Note: "McpToolset is listed but not fully supported in Agent Config"

    Args:
        config_path: Path to the agent's YAML config file.
        include_mcp: Whether to include MCP toolset (default: True).
        include_callbacks: Whether to include security callbacks (default: True).
        use_planner: Whether to use PlanReActPlanner for structured reasoning (default: False).
            Should be True for sub-agents that execute tools and produce final answers.
            Should be False for orchestrators that only route via transfer_to_agent.
        disallow_transfer_to_parent: Prevent agent from transferring back to parent.
            Useful for sub-agents that should complete their task before returning.
        disallow_transfer_to_peers: Prevent agent from transferring to sibling agents.
            Useful for ensuring the orchestrator controls all routing decisions.

    Returns:
        Configured Agent instance with MCP tools and callbacks.

    Example:
        ```python
        from pathlib import Path
        from core.agent_loader import create_agent_with_mcp

        agent = create_agent_with_mcp(Path(__file__).parent / "root_agent.yaml")

        # As a sub-agent with planner and transfer restrictions
        sub_agent = create_agent_with_mcp(
            Path(__file__).parent / "root_agent.yaml",
            use_planner=True,  # Sub-agents should use planner
            disallow_transfer_to_peers=True,  # Only orchestrator routes
        )
        ```
    """
    from google.adk.agents import Agent

    from core.callbacks import create_callbacks_for_agent
    from core.config import settings
    from core.mcp import create_mcp_toolset

    # Load configuration from YAML (Agent Config pattern)
    config = get_agent_config(config_path)

    # Build tools list
    tools: list[Any] = []

    # Add MCP toolset if requested
    if include_mcp:
        mcp_toolset = create_mcp_toolset()
        if mcp_toolset:
            tools.append(mcp_toolset)
            logger.debug(f"MCP toolset added for agent: {config.get('name')}")
        else:
            logger.warning(f"MCP toolset not available for agent: {config.get('name')}")

    # Extract generation config if present
    generate_content_config = None
    gen_config = config.get("generate_content_config")
    if gen_config:
        try:
            from google.genai.types import GenerateContentConfig

            generate_content_config = GenerateContentConfig(**gen_config)
        except ImportError:
            logger.warning("google.genai.types not available, skipping generation config")

    # Get callbacks for security (rate limiting, input validation, safety screening)
    callbacks = {}
    if include_callbacks:
        callbacks = create_callbacks_for_agent()
        logger.debug(f"Callbacks added for agent: {config.get('name')}")

    # Build optional transfer restriction parameters
    transfer_params = {}
    if disallow_transfer_to_parent:
        transfer_params["disallow_transfer_to_parent"] = True
    if disallow_transfer_to_peers:
        transfer_params["disallow_transfer_to_peers"] = True

    # Add PlanReActPlanner if requested
    # PlanReActPlanner is model-agnostic and works with any model (Gemini, Claude, GPT, etc.)
    # It structures reasoning with: PLANNING -> ACTION -> REASONING -> FINAL_ANSWER
    # Use for sub-agents that execute tools and produce answers, NOT for routing orchestrators
    planner = None
    if use_planner:
        try:
            from google.adk.planners import PlanReActPlanner

            planner = PlanReActPlanner()
            logger.info(f"PlanReActPlanner enabled for agent: {config.get('name')}")
        except ImportError:
            logger.warning(f"PlanReActPlanner not available for agent: {config.get('name')}")

    # Create agent programmatically (avoids McpToolset serialization issues)
    agent = Agent(
        model=config.get("model", settings.DEFAULT_MODEL),
        name=config.get("name", "unnamed_agent"),
        description=config.get("description", "").strip() if config.get("description") else "",
        instruction=config.get("instruction", "").strip() if config.get("instruction") else "",
        tools=tools,
        planner=planner,  # PlanReActPlanner for structured reasoning (or None)
        output_key=config.get("output_key"),
        generate_content_config=generate_content_config,
        **transfer_params,  # Apply transfer restrictions for sub-agents
        **callbacks,  # Apply security callbacks
    )

    logger.info(f"Agent created with MCP tools and callbacks: {agent.name}")
    return agent
