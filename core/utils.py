"""
Utility functions for sysadmin-agents.

Provides shared functionality used across multiple agents.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_agent_config(config_path: Path) -> dict[str, Any]:
    """
    Load agent configuration from a YAML file.

    Args:
        config_path: Path to the config.yaml file.

    Returns:
        Dictionary containing the parsed configuration.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If the YAML is invalid or missing required fields.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}") from e

    if config is None:
        raise ValueError(f"Empty config file: {config_path}")

    # Validate required fields
    _validate_agent_config(config, config_path)

    return config


def _validate_agent_config(config: dict[str, Any], config_path: Path) -> None:
    """
    Validate that an agent config has required fields.

    Args:
        config: The parsed configuration dictionary.
        config_path: Path to the config file (for error messages).

    Raises:
        ValueError: If required fields are missing.
    """
    required_fields = ["agent", "instruction"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field '{field}' in {config_path}")

    agent_section = config.get("agent", {})
    agent_required = ["name"]
    for field in agent_required:
        if field not in agent_section:
            raise ValueError(f"Missing required field 'agent.{field}' in {config_path}")


def load_config_for_agent(agent_name: str, base_dir: Path | None = None) -> dict[str, Any]:
    """
    Load configuration for a named agent.

    Convenience function that constructs the path and loads config.

    Args:
        agent_name: Name of the agent directory (e.g., "rca", "performance").
        base_dir: Base directory containing agent directories.
                  Defaults to the 'agents' directory in the project.

    Returns:
        Dictionary containing the parsed configuration.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If the YAML is invalid.
    """
    if base_dir is None:
        # Default to agents directory relative to project root
        base_dir = Path(__file__).parent.parent / "agents"

    config_path = base_dir / agent_name / "config.yaml"
    return load_agent_config(config_path)


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to the project root.
    """
    return Path(__file__).parent.parent


def setup_logging(
    level: str = "INFO",
    format_string: str | None = None,
) -> None:
    """
    Set up logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_string: Custom format string for log messages.
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=format_string,
    )
    logger.info(f"Logging configured at {level} level")
