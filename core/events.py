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
Event handling utilities for ADK agents.

This module provides utilities for processing and handling ADK events,
following the patterns described in the ADK Events documentation.

Events are the fundamental units of information flow in ADK:
- User messages
- Agent replies
- Tool calls and results
- State changes
- Control signals (transfer, escalate)
- Errors

Example usage:
    async for event in runner.run_async(...):
        event_info = classify_event(event)
        if event_info.is_final:
            display_to_user(event_info.text)
        elif event_info.is_tool_call:
            log_tool_usage(event_info.tool_name, event_info.tool_args)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of ADK events."""

    USER_INPUT = "user_input"
    AGENT_TEXT = "agent_text"
    STREAMING_TEXT = "streaming_text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STATE_UPDATE = "state_update"
    AGENT_TRANSFER = "agent_transfer"
    ESCALATION = "escalation"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class EventInfo:
    """Parsed information from an ADK event."""

    event_type: EventType
    author: str
    invocation_id: str
    event_id: str

    # Content fields
    text: str | None = None
    is_partial: bool = False
    is_final: bool = False

    # Tool call fields
    is_tool_call: bool = False
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)

    # Tool result fields
    is_tool_result: bool = False
    tool_response: dict[str, Any] = field(default_factory=dict)

    # State/artifact changes
    state_delta: dict[str, Any] = field(default_factory=dict)
    artifact_delta: dict[str, int] = field(default_factory=dict)

    # Control signals
    transfer_to_agent: str | None = None
    escalate: bool = False
    skip_summarization: bool = False

    # Error fields
    error_code: str | None = None
    error_message: str | None = None

    # Raw event reference
    raw_event: Any = None


def classify_event(event: Any) -> EventInfo:
    """
    Classify and parse an ADK event into a structured EventInfo.

    This function follows the ADK event processing patterns:
    1. Identify the author (user or agent)
    2. Determine the event type (text, tool call, tool result, etc.)
    3. Extract relevant content and actions
    4. Check if it's a final response

    Args:
        event: An ADK Event object from the runner.

    Returns:
        EventInfo with parsed event data.
    """
    # Extract basic identifiers
    author = getattr(event, "author", "unknown")
    invocation_id = getattr(event, "invocation_id", "")
    event_id = getattr(event, "id", "")

    # Initialize EventInfo
    info = EventInfo(
        event_type=EventType.UNKNOWN,
        author=author,
        invocation_id=invocation_id,
        event_id=event_id,
        raw_event=event,
    )

    # Check for errors first
    error_code = getattr(event, "error_code", None)
    error_message = getattr(event, "error_message", None)
    if error_code or error_message:
        info.event_type = EventType.ERROR
        info.error_code = error_code
        info.error_message = error_message
        return info

    # Check for user input
    if author == "user":
        info.event_type = EventType.USER_INPUT
        if hasattr(event, "content") and event.content:
            info.text = _extract_text(event.content)
        return info

    # Extract actions if present
    actions = getattr(event, "actions", None)
    if actions:
        info.state_delta = getattr(actions, "state_delta", {}) or {}
        info.artifact_delta = getattr(actions, "artifact_delta", {}) or {}
        info.transfer_to_agent = getattr(actions, "transfer_to_agent", None)
        info.escalate = getattr(actions, "escalate", False) or False
        info.skip_summarization = getattr(actions, "skip_summarization", False) or False

        # Check for transfer signal
        if info.transfer_to_agent:
            info.event_type = EventType.AGENT_TRANSFER
            return info

        # Check for escalation
        if info.escalate:
            info.event_type = EventType.ESCALATION
            return info

    # Check for tool calls
    function_calls = _get_function_calls(event)
    if function_calls:
        info.event_type = EventType.TOOL_CALL
        info.is_tool_call = True
        # Take the first call for simplicity (can be extended for multiple)
        first_call = function_calls[0]
        info.tool_name = getattr(first_call, "name", None)
        info.tool_args = getattr(first_call, "args", {}) or {}
        return info

    # Check for tool results
    function_responses = _get_function_responses(event)
    if function_responses:
        info.event_type = EventType.TOOL_RESULT
        info.is_tool_result = True
        first_response = function_responses[0]
        info.tool_name = getattr(first_response, "name", None)
        info.tool_response = getattr(first_response, "response", {}) or {}
        return info

    # Check for content
    content = getattr(event, "content", None)
    if content:
        text = _extract_text(content)
        if text:
            info.text = text
            info.is_partial = getattr(event, "partial", False) or False

            if info.is_partial:
                info.event_type = EventType.STREAMING_TEXT
            else:
                info.event_type = EventType.AGENT_TEXT

            # Check if this is a final response
            info.is_final = _is_final_response(event)
            return info

    # Check for state/artifact only updates
    if info.state_delta or info.artifact_delta:
        info.event_type = EventType.STATE_UPDATE
        return info

    return info


def _extract_text(content: Any) -> str | None:
    """Extract text from event content."""
    if not content:
        return None

    parts = getattr(content, "parts", None)
    if not parts:
        return None

    for part in parts:
        text = getattr(part, "text", None)
        if text:
            return text

    return None


def _get_function_calls(event: Any) -> list:
    """Get function calls from an event."""
    # Try the helper method first
    if hasattr(event, "get_function_calls"):
        calls = event.get_function_calls()
        if calls:
            return list(calls)

    # Fallback: check content.parts for function_call
    content = getattr(event, "content", None)
    if not content:
        return []

    parts = getattr(content, "parts", None)
    if not parts:
        return []

    calls = []
    for part in parts:
        function_call = getattr(part, "function_call", None)
        if function_call:
            calls.append(function_call)

    return calls


def _get_function_responses(event: Any) -> list:
    """Get function responses from an event."""
    # Try the helper method first
    if hasattr(event, "get_function_responses"):
        responses = event.get_function_responses()
        if responses:
            return list(responses)

    # Fallback: check content.parts for function_response
    content = getattr(event, "content", None)
    if not content:
        return []

    parts = getattr(content, "parts", None)
    if not parts:
        return []

    responses = []
    for part in parts:
        function_response = getattr(part, "function_response", None)
        if function_response:
            responses.append(function_response)

    return responses


def _is_final_response(event: Any) -> bool:
    """
    Check if an event is a final response suitable for display.

    Follows ADK's is_final_response() logic:
    - Tool result with skip_summarization = True
    - Long-running tool call
    - Complete text (not partial, no function calls/responses)
    """
    # Use built-in helper if available
    if hasattr(event, "is_final_response"):
        return event.is_final_response()

    # Manual check
    partial = getattr(event, "partial", False) or False
    if partial:
        return False

    function_calls = _get_function_calls(event)
    if function_calls:
        return False

    function_responses = _get_function_responses(event)
    if function_responses:
        # Check skip_summarization
        actions = getattr(event, "actions", None)
        if actions and getattr(actions, "skip_summarization", False):
            return True
        return False

    # Has text content and not partial = final
    content = getattr(event, "content", None)
    if content and _extract_text(content):
        return True

    return False


# =============================================================================
# Event Stream Processing Utilities
# =============================================================================


class EventAccumulator:
    """
    Accumulates streaming events into complete responses.

    Useful for building up text from partial streaming events
    and tracking the conversation history.

    Example:
        accumulator = EventAccumulator()
        async for event in runner.run_async(...):
            accumulator.add(event)
            if accumulator.has_final_response:
                print(accumulator.final_text)
                accumulator.reset()
    """

    def __init__(self):
        self._streaming_text = ""
        self._final_text: str | None = None
        self._events: list[EventInfo] = []
        self._tool_calls: list[dict] = []
        self._tool_results: list[dict] = []
        self._state_changes: dict[str, Any] = {}

    def add(self, event: Any) -> EventInfo:
        """Add an event to the accumulator."""
        info = classify_event(event)
        self._events.append(info)

        # Accumulate streaming text
        if info.event_type == EventType.STREAMING_TEXT and info.text:
            self._streaming_text += info.text

        # Capture final text
        if info.is_final and info.text:
            self._final_text = self._streaming_text + info.text
            self._streaming_text = ""

        # Track tool calls
        if info.is_tool_call:
            self._tool_calls.append(
                {
                    "name": info.tool_name,
                    "args": info.tool_args,
                }
            )

        # Track tool results
        if info.is_tool_result:
            self._tool_results.append(
                {
                    "name": info.tool_name,
                    "response": info.tool_response,
                }
            )

        # Track state changes
        if info.state_delta:
            self._state_changes.update(info.state_delta)

        return info

    @property
    def has_final_response(self) -> bool:
        """Check if a final response has been received."""
        return self._final_text is not None

    @property
    def final_text(self) -> str | None:
        """Get the final accumulated text."""
        return self._final_text

    @property
    def streaming_text(self) -> str:
        """Get the current streaming text (incomplete)."""
        return self._streaming_text

    @property
    def tool_calls(self) -> list[dict]:
        """Get all tool calls made during this interaction."""
        return self._tool_calls

    @property
    def tool_results(self) -> list[dict]:
        """Get all tool results received during this interaction."""
        return self._tool_results

    @property
    def state_changes(self) -> dict[str, Any]:
        """Get all state changes from this interaction."""
        return self._state_changes

    @property
    def events(self) -> list[EventInfo]:
        """Get all parsed events."""
        return self._events

    def reset(self):
        """Reset the accumulator for a new interaction."""
        self._streaming_text = ""
        self._final_text = None
        self._events = []
        self._tool_calls = []
        self._tool_results = []
        self._state_changes = {}


# =============================================================================
# Event Logging and Debugging
# =============================================================================


def log_event(event: Any, level: int = logging.DEBUG) -> EventInfo:
    """
    Log an event with structured information.

    Args:
        event: The ADK event to log.
        level: Logging level to use.

    Returns:
        Parsed EventInfo.
    """
    info = classify_event(event)

    log_parts = [
        f"[{info.event_type.value}]",
        f"author={info.author}",
    ]

    if info.text:
        # Truncate long text for logging
        text_preview = info.text[:100] + "..." if len(info.text) > 100 else info.text
        log_parts.append(f"text='{text_preview}'")

    if info.is_tool_call:
        log_parts.append(f"tool={info.tool_name}")
        log_parts.append(f"args={info.tool_args}")

    if info.is_tool_result:
        log_parts.append(f"tool={info.tool_name}")
        log_parts.append(f"response_keys={list(info.tool_response.keys())}")

    if info.transfer_to_agent:
        log_parts.append(f"transfer_to={info.transfer_to_agent}")

    if info.escalate:
        log_parts.append("escalate=True")

    if info.state_delta:
        log_parts.append(f"state_delta_keys={list(info.state_delta.keys())}")

    if info.is_final:
        log_parts.append("FINAL")

    logger.log(level, " ".join(log_parts))
    return info


def format_event_summary(event: Any) -> str:
    """
    Format a human-readable summary of an event.

    Args:
        event: The ADK event to summarize.

    Returns:
        Formatted summary string.
    """
    info = classify_event(event)

    lines = [
        f"Event Type: {info.event_type.value}",
        f"Author: {info.author}",
        f"Event ID: {info.event_id}",
    ]

    if info.text:
        lines.append(f"Text: {info.text[:200]}{'...' if len(info.text) > 200 else ''}")

    if info.is_tool_call:
        lines.append(f"Tool Call: {info.tool_name}({info.tool_args})")

    if info.is_tool_result:
        lines.append(f"Tool Result: {info.tool_name} -> {info.tool_response}")

    if info.state_delta:
        lines.append(f"State Changes: {info.state_delta}")

    if info.transfer_to_agent:
        lines.append(f"Transfer To: {info.transfer_to_agent}")

    if info.escalate:
        lines.append("Escalation: True")

    if info.is_final:
        lines.append("*** FINAL RESPONSE ***")

    return "\n".join(lines)
