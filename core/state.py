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
State management utilities for ADK agents.

This module provides utilities for managing session state following
ADK best practices for state prefixes and organization.

State Prefixes:
- No prefix: Session-specific state (e.g., 'current_task', 'booking_step')
- user: - User-specific state shared across sessions (e.g., 'user:preferences')
- app: - Application-wide state shared across all users (e.g., 'app:settings')
- temp: - Temporary invocation state, discarded after invocation (e.g., 'temp:cache')

Example usage:
    from core.state import StateManager

    # In a callback or tool function
    state = StateManager(context.state)

    # Session state (persists for this session)
    state.set("investigation_context", {...})

    # User state (persists across sessions for this user)
    state.set_user("preferences", {"theme": "dark"})

    # App state (shared across all users)
    state.set_app("global_settings", {...})

    # Temporary state (discarded after this invocation)
    state.set_temp("intermediate_result", {...})
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# State Key Prefixes
# =============================================================================


class StatePrefix:
    """State key prefixes for different scopes."""

    USER = "user:"  # User-specific, shared across sessions
    APP = "app:"  # Application-wide, shared across all users
    TEMP = "temp:"  # Temporary, discarded after invocation


# =============================================================================
# Sysadmin Agent State Keys
# =============================================================================


class StateKeys:
    """
    Centralized state key definitions for sysadmin agents.

    Using a class for state keys ensures consistency and makes
    refactoring easier.
    """

    # Session-level state (no prefix)
    INVESTIGATION_CONTEXT = "investigation_context"
    SESSION_START = "session_start"
    LAST_HOST_INVESTIGATED = "last_host_investigated"
    DISK_WARNING = "disk_warning"
    MEMORY_WARNING = "memory_warning"
    LAST_RCA_REPORT = "last_rca_report"
    LAST_PERFORMANCE_REPORT = "last_performance_report"
    LAST_CAPACITY_REPORT = "last_capacity_report"

    # User-level state (user: prefix)
    USER_ALLOWED_HOSTS = "user:allowed_hosts"
    USER_PREFERENCES = "user:preferences"
    USER_NOTIFICATION_SETTINGS = "user:notification_settings"

    # App-level state (app: prefix)
    APP_GLOBAL_SETTINGS = "app:global_settings"
    APP_DEFAULT_HOST = "app:default_host"

    # Temporary state (temp: prefix) - discarded after invocation
    TEMP_RATE_LIMIT_START = "temp:timer_start"
    TEMP_REQUEST_COUNT = "temp:request_count"
    TEMP_SECURITY_WARNING = "temp:security_warning"
    TEMP_SAFETY_BLOCKED = "temp:safety_blocked"
    TEMP_SAFETY_REASON = "temp:safety_reason"
    TEMP_SAFETY_CATEGORY = "temp:safety_category"


# =============================================================================
# State Manager
# =============================================================================


class StateManager:
    """
    Wrapper for managing session state with proper prefixes.

    This class provides a clean interface for reading and writing
    state with the correct prefixes for different scopes.

    Example:
        state = StateManager(context.state)
        state.set("task_status", "active")  # Session state
        state.set_user("theme", "dark")     # User state
        state.set_temp("cache", {...})      # Temporary state
    """

    def __init__(self, state_dict: dict[str, Any]):
        """
        Initialize with a state dictionary.

        Args:
            state_dict: The state dictionary from context.state
        """
        self._state = state_dict

    # -------------------------------------------------------------------------
    # Session State (no prefix)
    # -------------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Get a session-level state value."""
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a session-level state value."""
        self._state[key] = value
        logger.debug(f"State set: {key}")

    def has(self, key: str) -> bool:
        """Check if a session-level state key exists."""
        return key in self._state

    def delete(self, key: str) -> None:
        """Delete a session-level state key."""
        if key in self._state:
            del self._state[key]
            logger.debug(f"State deleted: {key}")

    # -------------------------------------------------------------------------
    # User State (user: prefix)
    # -------------------------------------------------------------------------

    def get_user(self, key: str, default: Any = None) -> Any:
        """Get a user-level state value (persists across sessions)."""
        return self._state.get(f"{StatePrefix.USER}{key}", default)

    def set_user(self, key: str, value: Any) -> None:
        """Set a user-level state value (persists across sessions)."""
        full_key = f"{StatePrefix.USER}{key}"
        self._state[full_key] = value
        logger.debug(f"User state set: {full_key}")

    def has_user(self, key: str) -> bool:
        """Check if a user-level state key exists."""
        return f"{StatePrefix.USER}{key}" in self._state

    # -------------------------------------------------------------------------
    # App State (app: prefix)
    # -------------------------------------------------------------------------

    def get_app(self, key: str, default: Any = None) -> Any:
        """Get an app-level state value (shared across all users)."""
        return self._state.get(f"{StatePrefix.APP}{key}", default)

    def set_app(self, key: str, value: Any) -> None:
        """Set an app-level state value (shared across all users)."""
        full_key = f"{StatePrefix.APP}{key}"
        self._state[full_key] = value
        logger.debug(f"App state set: {full_key}")

    def has_app(self, key: str) -> bool:
        """Check if an app-level state key exists."""
        return f"{StatePrefix.APP}{key}" in self._state

    # -------------------------------------------------------------------------
    # Temporary State (temp: prefix)
    # -------------------------------------------------------------------------

    def get_temp(self, key: str, default: Any = None) -> Any:
        """Get a temporary state value (discarded after invocation)."""
        return self._state.get(f"{StatePrefix.TEMP}{key}", default)

    def set_temp(self, key: str, value: Any) -> None:
        """Set a temporary state value (discarded after invocation)."""
        full_key = f"{StatePrefix.TEMP}{key}"
        self._state[full_key] = value
        logger.debug(f"Temp state set: {full_key}")

    def has_temp(self, key: str) -> bool:
        """Check if a temporary state key exists."""
        return f"{StatePrefix.TEMP}{key}" in self._state

    # -------------------------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------------------------

    def get_all(self) -> dict[str, Any]:
        """Get all state as a dictionary."""
        return dict(self._state)

    def get_session_state(self) -> dict[str, Any]:
        """Get only session-level state (no prefix)."""
        return {
            k: v
            for k, v in self._state.items()
            if not k.startswith((StatePrefix.USER, StatePrefix.APP, StatePrefix.TEMP))
        }

    def get_user_state(self) -> dict[str, Any]:
        """Get only user-level state."""
        prefix_len = len(StatePrefix.USER)
        return {k[prefix_len:]: v for k, v in self._state.items() if k.startswith(StatePrefix.USER)}

    def get_app_state(self) -> dict[str, Any]:
        """Get only app-level state."""
        prefix_len = len(StatePrefix.APP)
        return {k[prefix_len:]: v for k, v in self._state.items() if k.startswith(StatePrefix.APP)}

    def get_temp_state(self) -> dict[str, Any]:
        """Get only temporary state."""
        prefix_len = len(StatePrefix.TEMP)
        return {k[prefix_len:]: v for k, v in self._state.items() if k.startswith(StatePrefix.TEMP)}


# =============================================================================
# Investigation Context
# =============================================================================


@dataclass
class InvestigationContext:
    """
    Structured context for tracking an investigation across tool calls.

    This provides a type-safe way to manage investigation state
    instead of using raw dictionaries.
    """

    hosts_accessed: list[str] = field(default_factory=list)
    tools_used: list[dict[str, Any]] = field(default_factory=list)
    start_time: float = 0.0
    warnings: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    def add_host(self, host: str) -> None:
        """Track a host access."""
        if host not in self.hosts_accessed:
            self.hosts_accessed.append(host)

    def add_tool_usage(self, tool_name: str, timestamp: float) -> None:
        """Track a tool usage."""
        self.tools_used.append({"tool": tool_name, "time": timestamp})

    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)

    def add_finding(self, finding: str) -> None:
        """Add a finding."""
        self.findings.append(finding)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for state storage."""
        return {
            "hosts_accessed": self.hosts_accessed,
            "tools_used": self.tools_used,
            "start_time": self.start_time,
            "warnings": self.warnings,
            "findings": self.findings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InvestigationContext":
        """Create from dictionary."""
        return cls(
            hosts_accessed=data.get("hosts_accessed", []),
            tools_used=data.get("tools_used", []),
            start_time=data.get("start_time", 0.0),
            warnings=data.get("warnings", []),
            findings=data.get("findings", []),
        )


# =============================================================================
# State Initialization
# =============================================================================


def initialize_session_state(state: dict[str, Any]) -> None:
    """
    Initialize default session state values.

    Call this in before_agent_callback to ensure required state exists.

    Args:
        state: The session state dictionary.
    """
    import time

    manager = StateManager(state)

    # Initialize investigation context if not present
    if not manager.has(StateKeys.INVESTIGATION_CONTEXT):
        context = InvestigationContext(start_time=time.time())
        manager.set(StateKeys.INVESTIGATION_CONTEXT, context.to_dict())
        logger.debug("Initialized investigation context")

    # Initialize session start time
    if not manager.has(StateKeys.SESSION_START):
        manager.set(StateKeys.SESSION_START, time.time())
        logger.debug("Initialized session start time")


def get_investigation_context(state: dict[str, Any]) -> InvestigationContext:
    """
    Get the investigation context from state.

    Args:
        state: The session state dictionary.

    Returns:
        InvestigationContext object.
    """
    manager = StateManager(state)
    data = manager.get(StateKeys.INVESTIGATION_CONTEXT, {})
    return InvestigationContext.from_dict(data)


def save_investigation_context(state: dict[str, Any], context: InvestigationContext) -> None:
    """
    Save the investigation context to state.

    Args:
        state: The session state dictionary.
        context: The InvestigationContext to save.
    """
    manager = StateManager(state)
    manager.set(StateKeys.INVESTIGATION_CONTEXT, context.to_dict())


# =============================================================================
# Agent Configuration Loading
# =============================================================================

_agent_config_cache: dict[str, Any] | None = None


def load_agent_config() -> dict[str, Any]:
    """
    Load agent configuration from YAML file.

    This externalizes hardcoded values from agent instructions, including:
    - Performance thresholds (CPU, memory, disk warning/critical levels)
    - Upgrade requirements (disk space, memory requirements)
    - Common space consumers (paths for capacity analysis)
    - Safety ratings for cleanup operations

    These values can be injected into session state and used with ADK's
    instruction templating via {var} syntax.

    Returns:
        Configuration dictionary.

    Example:
        config = load_agent_config()
        thresholds = config.get("performance_thresholds", {})
        cpu_warning = thresholds.get("cpu", {}).get("warning_percent", 80)
    """
    global _agent_config_cache

    if _agent_config_cache is not None:
        return _agent_config_cache

    from pathlib import Path

    import yaml

    config_path = Path(__file__).parent / "agent_config.yaml"

    try:
        with open(config_path) as f:
            _agent_config_cache = yaml.safe_load(f) or {}
        logger.debug(f"Loaded agent config from {config_path}")
    except FileNotFoundError:
        logger.warning(f"Agent config not found at {config_path}, using defaults")
        _agent_config_cache = {}
    except Exception as e:
        logger.error(f"Error loading agent config: {e}")
        _agent_config_cache = {}

    return _agent_config_cache


def get_performance_thresholds() -> dict[str, Any]:
    """
    Get performance thresholds from config.

    Returns:
        Dictionary with cpu, memory, swap, disk, and load_average thresholds.
    """
    config = load_agent_config()
    return config.get("performance_thresholds", {})


def get_upgrade_requirements() -> dict[str, Any]:
    """
    Get upgrade requirements from config.

    Returns:
        Dictionary with disk_space and memory requirements.
    """
    config = load_agent_config()
    return config.get("upgrade_requirements", {})


def format_thresholds_for_instruction() -> str:
    """
    Format performance thresholds as a markdown table for use in instructions.

    This allows thresholds to be externally configured while still being
    included in agent instructions.

    Returns:
        Markdown table string.
    """
    thresholds = get_performance_thresholds()

    cpu = thresholds.get("cpu", {})
    memory = thresholds.get("memory", {})
    swap = thresholds.get("swap", {})
    disk = thresholds.get("disk", {})

    return f"""| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Usage | > {cpu.get('warning_percent', 80)}% | > {cpu.get('critical_percent', 95)}% |
| Memory Usage | > {memory.get('warning_percent', 80)}% | > {memory.get('critical_percent', 95)}% |
| Swap Usage | > {swap.get('warning_percent', 50)}% | > {swap.get('critical_percent', 80)}% |
| Disk Usage | > {disk.get('warning_percent', 80)}% | > {disk.get('critical_percent', 95)}% |"""


def inject_config_into_state(state: dict[str, Any]) -> None:
    """
    Inject agent configuration into session state for instruction templating.

    This enables using {var} syntax in agent instructions to reference
    externalized configuration values.

    Args:
        state: The session state dictionary.

    Example YAML instruction using state variables:
        instruction: |
          CPU warning threshold is {cpu_warning_percent}%.
          Memory critical threshold is {memory_critical_percent}%.
    """
    config = load_agent_config()
    manager = StateManager(state)

    # Inject flattened performance thresholds
    perf = config.get("performance_thresholds", {})
    if cpu := perf.get("cpu"):
        manager.set("cpu_warning_percent", cpu.get("warning_percent", 80))
        manager.set("cpu_critical_percent", cpu.get("critical_percent", 95))
    if memory := perf.get("memory"):
        manager.set("memory_warning_percent", memory.get("warning_percent", 80))
        manager.set("memory_critical_percent", memory.get("critical_percent", 95))
    if disk := perf.get("disk"):
        manager.set("disk_warning_percent", disk.get("warning_percent", 80))
        manager.set("disk_critical_percent", disk.get("critical_percent", 95))

    # Inject OS configuration
    os_config = config.get("os", {})
    manager.set("os_primary", os_config.get("primary", "Linux/RHEL"))

    # Inject formatted thresholds table for instructions
    manager.set("performance_thresholds_table", format_thresholds_for_instruction())

    logger.debug("Injected agent config into session state")
