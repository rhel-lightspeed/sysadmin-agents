"""
Agent factory for creating specialist agents from YAML configuration.

This module provides a unified way to create ADK agents from configuration files,
reducing code duplication across specialist agents and ensuring consistent
application of all configuration options.
"""

import logging
from pathlib import Path
from typing import Any

from core.callbacks import create_callbacks_for_agent
from core.config import settings
from core.mcp import create_mcp_toolset
from core.utils import load_agent_config

logger = logging.getLogger(__name__)


def create_specialist_agent(
    config_path: Path,
    include_callbacks: bool = True,
    include_mcp: bool = True,
) -> Any:
    """
    Create a specialist agent from a YAML configuration file.

    This factory function handles all the common setup for specialist agents:
    - Loading and validating configuration
    - Creating MCP toolset for remote system access
    - Setting up callbacks for validation and state management
    - Applying thinking/generation configuration
    - Setting output_key for session state persistence

    Args:
        config_path: Path to the agent's config.yaml file.
        include_callbacks: Whether to include standard callbacks (default: True).
        include_mcp: Whether to include MCP toolset (default: True).

    Returns:
        Configured Agent instance.

    Raises:
        ImportError: If google-adk is not installed.
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config is invalid.

    Example:
        ```python
        from pathlib import Path
        from core.agent_factory import create_specialist_agent

        rca_agent = create_specialist_agent(Path(__file__).parent / "config.yaml")
        ```
    """
    try:
        from google.adk.agents import Agent
    except ImportError as e:
        logger.error(f"google-adk not installed: {e}")
        raise

    # Load configuration
    config = load_agent_config(config_path)
    agent_config = config.get("agent", {})

    logger.debug(f"Creating agent from config: {config_path}")

    # Build tools list
    tools: list[Any] = []
    if include_mcp:
        toolset = create_mcp_toolset()
        if toolset:
            tools.append(toolset)
            logger.info(f"Agent {agent_config.get('name')}: MCP toolset created")
        else:
            logger.warning(f"Agent {agent_config.get('name')}: MCP toolset not available")

    # Get callbacks if requested
    callbacks = create_callbacks_for_agent() if include_callbacks else {}

    # Build generation config if thinking is enabled
    generate_content_config = _create_generation_config(config)

    # Create the agent with all configuration applied
    agent = Agent(
        model=agent_config.get("model", settings.DEFAULT_MODEL),
        name=agent_config.get("name", "unnamed_agent"),
        description=agent_config.get("description", "").strip(),
        instruction=config.get("instruction", "").strip(),
        tools=tools,
        output_key=config.get("output_key"),
        generate_content_config=generate_content_config,
        **callbacks,
    )

    logger.info(f"Agent created: {agent.name}")
    return agent


def _create_generation_config(config: dict[str, Any]) -> Any | None:
    """
    Create GenerateContentConfig from thinking configuration.

    Args:
        config: The full agent configuration dictionary.

    Returns:
        GenerateContentConfig if thinking is enabled, None otherwise.
    """
    thinking_config = config.get("thinking", {})

    if not thinking_config.get("enabled", False):
        return None

    try:
        from google.genai.types import GenerateContentConfig
    except ImportError:
        logger.warning("google.genai.types not available, skipping generation config")
        return None

    # Create config with reasonable defaults for deterministic behavior
    return GenerateContentConfig(
        temperature=0.1,  # Lower temperature for more consistent outputs
        top_p=0.5,  # More focused sampling
    )


def create_orchestrator_agent(
    name: str,
    description: str,
    instruction: str,
    sub_agents: list[Any],
    use_planner: bool = True,
) -> Any:
    """
    Create an orchestrator agent that coordinates sub-agents.

    This is used for the main sysadmin agent that routes to specialists.

    Args:
        name: Agent name.
        description: Agent description.
        instruction: System instruction for the agent.
        sub_agents: List of specialist sub-agents.
        use_planner: Whether to use PlanReActPlanner (default: True).

    Returns:
        Configured orchestrator Agent.
    """
    try:
        from google.adk.agents import Agent
        from google.adk.planners import PlanReActPlanner
    except ImportError as e:
        logger.error(f"google-adk not installed: {e}")
        raise

    # Get callbacks
    callbacks = create_callbacks_for_agent()

    # Create the orchestrator
    agent = Agent(
        model=settings.DEFAULT_MODEL,
        name=name,
        description=description,
        instruction=instruction.strip(),
        sub_agents=sub_agents,
        planner=PlanReActPlanner() if use_planner else None,
        **callbacks,
    )

    logger.info(f"Orchestrator agent created: {name} with {len(sub_agents)} sub-agents")
    return agent


def create_sub_agent_wrapper(
    source_agent: Any,
    name: str,
    description: str,
    disallow_transfer_to_parent: bool = True,
    disallow_transfer_to_peers: bool = True,
) -> Any:
    """
    Create a sub-agent wrapper from an existing agent.

    This wraps a standalone specialist agent for use as a sub-agent
    in an orchestrator, with appropriate transfer restrictions.

    Args:
        source_agent: The original agent to wrap.
        name: New name for the sub-agent (typically "name_specialist").
        description: Description optimized for routing decisions.
        disallow_transfer_to_parent: Prevent transfer back to parent.
        disallow_transfer_to_peers: Prevent transfer to sibling agents.

    Returns:
        Wrapped Agent configured as a sub-agent.
    """
    try:
        from google.adk.agents import Agent
    except ImportError as e:
        logger.error(f"google-adk not installed: {e}")
        raise

    return Agent(
        model=source_agent.model,
        name=name,
        description=description,
        instruction=source_agent.instruction,
        tools=source_agent.tools,
        disallow_transfer_to_parent=disallow_transfer_to_parent,
        disallow_transfer_to_peers=disallow_transfer_to_peers,
    )
