"""
Callback functions for ADK agents.

Provides input validation, tool argument checking, session state management,
and rate limiting following Google ADK best practices.

Configuration is loaded from callbacks_config.yaml for easy customization.

Callback Signatures (per official ADK documentation):
- before_agent_callback: (CallbackContext) -> Optional[types.Content]
- after_agent_callback: (CallbackContext) -> Optional[types.Content]
- before_model_callback: (CallbackContext, LlmRequest) -> Optional[LlmResponse]
- after_model_callback: (CallbackContext, LlmResponse) -> Optional[LlmResponse]
- before_tool_callback: (BaseTool, Dict[str, Any], ToolContext) -> Optional[Dict]
- after_tool_callback: (BaseTool, Dict[str, Any], ToolContext, Any) -> Optional[Dict]
"""

import logging
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from core.config import settings

# ADK type imports - using try/except for graceful degradation
try:
    from google.adk.agents.callback_context import CallbackContext
    from google.adk.models.llm_request import LlmRequest
    from google.adk.models.llm_response import LlmResponse
    from google.adk.tools.base_tool import BaseTool
    from google.adk.tools.tool_context import ToolContext

    ADK_TYPES_AVAILABLE = True
except ImportError:
    # Fallback for environments where ADK is not fully installed
    CallbackContext = Any
    LlmRequest = Any
    LlmResponse = Any
    BaseTool = Any
    ToolContext = Any
    ADK_TYPES_AVAILABLE = False

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration Loading
# =============================================================================

CONFIG_PATH = Path(__file__).parent / "callbacks_config.yaml"


@lru_cache(maxsize=1)
def _load_callbacks_config() -> dict:
    """Load callback configuration from YAML file.

    Returns:
        Configuration dictionary with rate limiting, security patterns, etc.
    """
    try:
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f)
        logger.debug(f"Loaded callbacks config from {CONFIG_PATH}")
        return config
    except Exception as e:
        logger.warning(f"Could not load callbacks config: {e}, using defaults")
        return {}


def _get_config() -> dict:
    """Get the callbacks configuration."""
    return _load_callbacks_config()


# =============================================================================
# Configuration Accessors
# =============================================================================


def get_rate_limit_secs() -> int:
    """Get rate limit window in seconds."""
    config = _get_config()
    return config.get("rate_limiting", {}).get("window_seconds", 60)


def get_rpm_quota() -> int:
    """Get requests per minute quota."""
    config = _get_config()
    return config.get("rate_limiting", {}).get("requests_per_minute", 10)


def get_blocked_patterns() -> list[str]:
    """Get list of blocked command patterns."""
    config = _get_config()
    patterns = config.get("security", {}).get("blocked_patterns", [])
    return [p["pattern"] for p in patterns if isinstance(p, dict) and "pattern" in p]


def get_sensitive_patterns() -> list[str]:
    """Get list of sensitive command patterns."""
    config = _get_config()
    patterns = config.get("security", {}).get("sensitive_patterns", [])
    return [p["pattern"] for p in patterns if isinstance(p, dict) and "pattern" in p]


def get_host_aware_tools() -> list[str]:
    """Get list of tools that require host parameter."""
    config = _get_config()
    return config.get("host_validation", {}).get("host_aware_tools", [])


def get_disk_warning_threshold() -> int:
    """Get disk usage warning threshold percentage."""
    config = _get_config()
    return config.get("thresholds", {}).get("disk_warning_percent", 90)


def get_memory_warning_threshold() -> int:
    """Get memory usage warning threshold percentage."""
    config = _get_config()
    return config.get("thresholds", {}).get("memory_warning_percent", 90)


# =============================================================================
# Rate Limit Callback (before_model_callback)
# =============================================================================


def rate_limit_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """
    Callback that implements query rate limiting.

    Prevents exceeding API quotas by tracking requests per minute.
    When the limit is reached, returns an LlmResponse asking the user to wait
    instead of blocking with sleep (which would block the async event loop).

    Args:
        callback_context: CallbackContext with session state.
        llm_request: The LLM request being made.

    Returns:
        None to proceed with LLM call, or LlmResponse to block.
    """
    # Fix empty text parts (can cause API errors)
    if hasattr(llm_request, "contents"):
        for content in llm_request.contents:
            if hasattr(content, "parts"):
                for part in content.parts:
                    if hasattr(part, "text") and part.text == "":
                        part.text = " "

    now = time.time()
    rpm_quota = get_rpm_quota()
    rate_limit_secs = get_rate_limit_secs()

    if "timer_start" not in callback_context.state:
        callback_context.state["timer_start"] = now
        callback_context.state["request_count"] = 1
        logger.debug(
            "rate_limit_callback [timestamp: %i, req_count: 1, elapsed_secs: 0]",
            now,
        )
        return None

    request_count = callback_context.state["request_count"] + 1
    elapsed_secs = now - callback_context.state["timer_start"]

    logger.debug(
        "rate_limit_callback [timestamp: %i, request_count: %i, elapsed_secs: %i]",
        now,
        request_count,
        elapsed_secs,
    )

    if request_count > rpm_quota:
        remaining_secs = rate_limit_secs - elapsed_secs
        if remaining_secs > 0:
            # Instead of blocking with sleep, return a response
            # This preserves the async event loop
            logger.warning(
                "Rate limit reached (%d/%d). User should wait %.0f seconds.",
                request_count - 1,
                rpm_quota,
                remaining_secs,
            )
            callback_context.state["rate_limited"] = True
            callback_context.state["rate_limit_reset"] = now + remaining_secs

            # Return an LlmResponse to gracefully handle rate limiting
            if ADK_TYPES_AVAILABLE:
                try:
                    from google.genai import types

                    return LlmResponse(
                        content=types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    text=(
                                        f"I'm currently processing many requests. "
                                        f"Please wait about {int(remaining_secs)} seconds "
                                        f"and try again. This helps ensure reliable service."
                                    )
                                )
                            ],
                        )
                    )
                except ImportError:
                    pass
            # If we can't create LlmResponse, allow the request (graceful degradation)
            return None
        else:
            # Window has expired, reset the counter
            callback_context.state["timer_start"] = now
            callback_context.state["request_count"] = 1
            callback_context.state["rate_limited"] = False
    else:
        callback_context.state["request_count"] = request_count

    return None  # Allow the LLM call to proceed


# =============================================================================
# Input Validation Callback (before_model_callback)
# =============================================================================


def input_validation_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """
    Validate user input before it reaches the LLM.

    Checks for dangerous command patterns that could harm systems.
    In production mode, blocks dangerous requests by returning an LlmResponse.
    In development, logs warnings only.

    Args:
        callback_context: CallbackContext with session state.
        llm_request: The LLM request being made.

    Returns:
        None to proceed with LLM call, or LlmResponse to block.
    """
    if not hasattr(llm_request, "contents"):
        return None

    # Extract user text from request
    user_text = ""
    for content in llm_request.contents:
        if hasattr(content, "parts"):
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    user_text += part.text + " "

    user_text = user_text.lower()

    # Check for blocked patterns (most dangerous)
    for pattern in get_blocked_patterns():
        if re.search(pattern, user_text, re.IGNORECASE):
            logger.error(f"Blocked dangerous pattern detected: {pattern}")
            callback_context.state["security_warning"] = f"Blocked pattern detected: {pattern}"
            # In production, block the request by returning an LlmResponse
            if settings.ENVIRONMENT == "production" and ADK_TYPES_AVAILABLE:
                try:
                    from google.genai import types

                    return LlmResponse(
                        content=types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    text=(
                                        "I cannot process this request as it contains potentially "
                                        "dangerous commands. Please rephrase your request."
                                    )
                                )
                            ],
                        )
                    )
                except ImportError:
                    pass
            return None  # In development, just log and continue

    # Check for sensitive patterns (warn only)
    for pattern in get_sensitive_patterns():
        if re.search(pattern, user_text, re.IGNORECASE):
            logger.warning(f"Sensitive pattern detected: {pattern}")
            callback_context.state["security_warning"] = f"Sensitive operation detected: {pattern}"
            return None  # Just warn, don't block

    return None  # Allow the LLM call to proceed


def create_before_model_callback():
    """
    Create a combined before_model_callback that handles both
    rate limiting and input validation.

    Returns:
        Combined callback function with proper ADK signature.
    """

    def combined_callback(
        callback_context: CallbackContext, llm_request: LlmRequest
    ) -> LlmResponse | None:
        """Combined before_model callback."""
        # Run rate limiting first
        rate_result = rate_limit_callback(callback_context, llm_request)
        if rate_result is not None:
            return rate_result

        # Then run input validation
        validation_result = input_validation_callback(callback_context, llm_request)
        if validation_result is not None:
            return validation_result

        return None  # Allow the LLM call to proceed

    return combined_callback


# =============================================================================
# Before Agent Callback
# =============================================================================


def before_agent_callback(callback_context: CallbackContext) -> Any | None:
    """
    Initialize session state before agent execution.

    Sets up default state values, loads persisted context, and injects
    externalized configuration for use in instruction templating.

    Args:
        callback_context: CallbackContext with session state.

    Returns:
        None to proceed with agent execution, or types.Content to skip
        the agent's execution and use the returned content as the response.
    """
    state = callback_context.state

    # Initialize investigation context if not present
    if "investigation_context" not in state:
        state["investigation_context"] = {
            "hosts_accessed": [],
            "tools_used": [],
            "start_time": time.time(),
        }
        logger.debug("Initialized investigation context")

    # Initialize allowed hosts from environment (if configured)
    if "allowed_hosts" not in state:
        # In production, this would be loaded from configuration
        state["allowed_hosts"] = []  # Empty means all hosts allowed

    # Track session start
    if "session_start" not in state:
        state["session_start"] = time.time()
        logger.info("New session started")

    # Inject externalized configuration into state for instruction templating
    # This enables using {var} syntax in YAML instructions to reference
    # configurable values like thresholds instead of hardcoding them
    if "config_injected" not in state:
        try:
            from core.state import inject_config_into_state

            inject_config_into_state(state)
            state["config_injected"] = True
        except Exception as e:
            logger.warning(f"Could not inject agent config: {e}")

    return None  # Proceed with agent execution


# =============================================================================
# Before Tool Callback
# =============================================================================


def before_tool_callback(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> dict[str, Any] | None:
    """
    Validate tool arguments before execution.

    Checks for required parameters, validates host access,
    and logs tool usage for audit purposes.

    Args:
        tool: The tool being called (BaseTool instance).
        args: Arguments being passed to the tool.
        tool_context: ToolContext with session state.

    Returns:
        None to proceed with tool execution, or dict to override tool result.
    """
    tool_name = getattr(tool, "name", str(tool))
    logger.debug(f"Before tool: {tool_name} with args: {args}")

    # Track tool usage in session state
    if "investigation_context" in tool_context.state:
        tools_used = tool_context.state["investigation_context"].get("tools_used", [])
        tools_used.append({"tool": tool_name, "time": time.time()})
        tool_context.state["investigation_context"]["tools_used"] = tools_used

    # Validate host parameter for host-aware tools
    host_aware_tools = get_host_aware_tools()
    if tool_name in host_aware_tools:
        host = args.get("host")

        if host:
            # Track host access
            if "investigation_context" in tool_context.state:
                hosts_accessed = tool_context.state["investigation_context"].get(
                    "hosts_accessed", []
                )
                if host not in hosts_accessed:
                    hosts_accessed.append(host)
                    tool_context.state["investigation_context"]["hosts_accessed"] = hosts_accessed

            # Update last host investigated
            tool_context.state["last_host_investigated"] = host

            # Check allowed hosts (if configured)
            allowed_hosts = tool_context.state.get("allowed_hosts", [])
            if allowed_hosts and host not in allowed_hosts:
                error_msg = (
                    f"Host '{host}' is not in the allowed hosts list. "
                    f"Allowed hosts: {allowed_hosts}"
                )
                logger.warning(error_msg)
                if settings.ENVIRONMENT == "production":
                    # Return a dict to override the tool result (per ADK spec)
                    return {
                        "status": "error",
                        "error_message": error_msg,
                    }

    return None


# =============================================================================
# After Tool Callback
# =============================================================================


def after_tool_callback(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: Any,
) -> dict[str, Any] | None:
    """
    Process tool results after execution.

    Can modify or augment tool responses, log results,
    or trigger follow-up actions.

    Args:
        tool: The tool that was called (BaseTool instance).
        args: Arguments that were passed.
        tool_context: ToolContext with session state.
        tool_response: The tool's response (can be any type).

    Returns:
        Modified response dict, or None to use original.
    """
    tool_name = getattr(tool, "name", str(tool))
    logger.debug(
        f"After tool: {tool_name}, response keys: {tool_response.keys() if isinstance(tool_response, dict) else type(tool_response)}"
    )

    # Store significant findings in session state
    if isinstance(tool_response, dict):
        # Track disk space warnings
        if tool_name == "get_disk_usage":
            usage_pct = tool_response.get("usage_percent", 0)
            disk_threshold = get_disk_warning_threshold()
            if usage_pct > disk_threshold:
                tool_context.state["disk_warning"] = {
                    "host": args.get("host", "unknown"),
                    "usage_percent": usage_pct,
                    "detected_at": time.time(),
                }
                logger.warning(f"High disk usage detected: {usage_pct}%")

        # Track memory warnings
        if tool_name == "get_memory_information":
            mem_used_pct = tool_response.get("percent_used", 0)
            memory_threshold = get_memory_warning_threshold()
            if mem_used_pct > memory_threshold:
                tool_context.state["memory_warning"] = {
                    "host": args.get("host", "unknown"),
                    "percent_used": mem_used_pct,
                    "detected_at": time.time(),
                }
                logger.warning(f"High memory usage detected: {mem_used_pct}%")

    return None


# =============================================================================
# Callback Factory Functions
# =============================================================================


def create_callbacks_for_agent(include_safety: bool = True) -> dict[str, Any]:
    """
    Create a dictionary of all callbacks for agent configuration.

    Following official ADK callback signatures:
    - before_agent_callback: (CallbackContext) -> Optional[types.Content]
    - before_model_callback: (CallbackContext, LlmRequest) -> Optional[LlmResponse]
    - before_tool_callback: (BaseTool, Dict, ToolContext) -> Optional[Dict]
    - after_tool_callback: (BaseTool, Dict, ToolContext, Any) -> Optional[Dict]

    Args:
        include_safety: Whether to include LLM-based safety screening.
                       Recommended for production environments.

    Returns:
        Dictionary with callback function references for Agent constructor.
    """
    from core.safety import (
        create_safety_screening_callback,
        create_tool_safety_callback,
    )

    # Create the base before_model_callback
    base_callback = create_before_model_callback()

    if include_safety:
        # Wrap with safety screening
        safety_callback = create_safety_screening_callback()

        def combined_before_model(
            callback_context: CallbackContext, llm_request: LlmRequest
        ) -> LlmResponse | None:
            """Combined callback with safety screening."""
            # Run safety screening first
            safety_result = safety_callback(callback_context, llm_request)
            if safety_result is not None:
                return safety_result
            # Then run rate limiting and input validation
            return base_callback(callback_context, llm_request)

        before_model = combined_before_model

        # Create tool callback with safety
        base_tool_callback = before_tool_callback
        tool_safety = create_tool_safety_callback()

        def combined_tool_callback(
            tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
        ) -> dict[str, Any] | None:
            """Combined tool callback with safety screening."""
            # Run safety screening first
            safety_result = tool_safety(tool, args, tool_context)
            if safety_result is not None:
                return safety_result
            # Then run regular validation
            return base_tool_callback(tool, args, tool_context)

        tool_callback = combined_tool_callback
    else:
        before_model = base_callback
        tool_callback = before_tool_callback

    return {
        "before_model_callback": before_model,
        "before_agent_callback": before_agent_callback,
        "before_tool_callback": tool_callback,
        "after_tool_callback": after_tool_callback,
    }
