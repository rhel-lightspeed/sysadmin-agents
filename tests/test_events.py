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

"""Tests for the events module."""

from dataclasses import dataclass
from typing import Any

from core.events import (
    EventAccumulator,
    EventType,
    classify_event,
    format_event_summary,
    log_event,
)

# =============================================================================
# Mock Event Classes for Testing
# =============================================================================


@dataclass
class MockPart:
    """Mock content part."""

    text: str | None = None
    function_call: Any = None
    function_response: Any = None


@dataclass
class MockContent:
    """Mock content with parts."""

    parts: list[MockPart] | None = None
    role: str = "model"


@dataclass
class MockFunctionCall:
    """Mock function call."""

    name: str
    args: dict[str, Any]


@dataclass
class MockFunctionResponse:
    """Mock function response."""

    name: str
    response: dict[str, Any]


@dataclass
class MockActions:
    """Mock event actions."""

    state_delta: dict[str, Any] | None = None
    artifact_delta: dict[str, int] | None = None
    transfer_to_agent: str | None = None
    escalate: bool = False
    skip_summarization: bool = False


@dataclass
class MockEvent:
    """Mock ADK event for testing."""

    author: str = "test_agent"
    invocation_id: str = "inv-123"
    id: str = "evt-456"
    content: MockContent | None = None
    partial: bool = False
    actions: MockActions | None = None
    error_code: str | None = None
    error_message: str | None = None

    def get_function_calls(self):
        if not self.content or not self.content.parts:
            return []
        return [p.function_call for p in self.content.parts if p.function_call]

    def get_function_responses(self):
        if not self.content or not self.content.parts:
            return []
        return [p.function_response for p in self.content.parts if p.function_response]

    def is_final_response(self):
        if self.partial:
            return False
        if self.get_function_calls():
            return False
        if self.get_function_responses():
            if self.actions and self.actions.skip_summarization:
                return True
            return False
        if self.content and any(p.text for p in (self.content.parts or [])):
            return True
        return False


# =============================================================================
# EventType Tests
# =============================================================================


class TestEventType:
    """Tests for EventType enum."""

    def test_event_types(self):
        """Should have all expected event types."""
        assert EventType.USER_INPUT.value == "user_input"
        assert EventType.AGENT_TEXT.value == "agent_text"
        assert EventType.STREAMING_TEXT.value == "streaming_text"
        assert EventType.TOOL_CALL.value == "tool_call"
        assert EventType.TOOL_RESULT.value == "tool_result"
        assert EventType.STATE_UPDATE.value == "state_update"
        assert EventType.AGENT_TRANSFER.value == "agent_transfer"
        assert EventType.ESCALATION.value == "escalation"
        assert EventType.ERROR.value == "error"
        assert EventType.UNKNOWN.value == "unknown"


# =============================================================================
# classify_event Tests
# =============================================================================


class TestClassifyEvent:
    """Tests for classify_event function."""

    def test_user_input_event(self):
        """Should classify user input correctly."""
        event = MockEvent(
            author="user",
            content=MockContent(parts=[MockPart(text="Hello, help me debug")]),
        )
        info = classify_event(event)

        assert info.event_type == EventType.USER_INPUT
        assert info.author == "user"
        assert info.text == "Hello, help me debug"

    def test_agent_text_event(self):
        """Should classify agent text response correctly."""
        event = MockEvent(
            author="sysadmin",
            content=MockContent(parts=[MockPart(text="I'll help you debug.")]),
            partial=False,
        )
        info = classify_event(event)

        assert info.event_type == EventType.AGENT_TEXT
        assert info.author == "sysadmin"
        assert info.text == "I'll help you debug."
        assert info.is_final is True

    def test_streaming_text_event(self):
        """Should classify streaming text correctly."""
        event = MockEvent(
            author="sysadmin",
            content=MockContent(parts=[MockPart(text="Processing...")]),
            partial=True,
        )
        info = classify_event(event)

        assert info.event_type == EventType.STREAMING_TEXT
        assert info.is_partial is True
        assert info.is_final is False

    def test_tool_call_event(self):
        """Should classify tool call correctly."""
        event = MockEvent(
            author="rca_agent",
            content=MockContent(
                parts=[
                    MockPart(
                        function_call=MockFunctionCall(
                            name="get_system_information",
                            args={"host": "server1"},
                        )
                    )
                ]
            ),
        )
        info = classify_event(event)

        assert info.event_type == EventType.TOOL_CALL
        assert info.is_tool_call is True
        assert info.tool_name == "get_system_information"
        assert info.tool_args == {"host": "server1"}

    def test_tool_result_event(self):
        """Should classify tool result correctly."""
        event = MockEvent(
            author="rca_agent",
            content=MockContent(
                parts=[
                    MockPart(
                        function_response=MockFunctionResponse(
                            name="get_system_information",
                            response={"hostname": "server1", "os": "Linux"},
                        )
                    )
                ]
            ),
        )
        info = classify_event(event)

        assert info.event_type == EventType.TOOL_RESULT
        assert info.is_tool_result is True
        assert info.tool_name == "get_system_information"
        assert info.tool_response == {"hostname": "server1", "os": "Linux"}

    def test_state_update_event(self):
        """Should classify state update correctly."""
        event = MockEvent(
            author="sysadmin",
            content=None,
            actions=MockActions(state_delta={"last_host": "server1"}),
        )
        info = classify_event(event)

        assert info.event_type == EventType.STATE_UPDATE
        assert info.state_delta == {"last_host": "server1"}

    def test_agent_transfer_event(self):
        """Should classify agent transfer correctly."""
        event = MockEvent(
            author="sysadmin",
            actions=MockActions(transfer_to_agent="rca_agent"),
        )
        info = classify_event(event)

        assert info.event_type == EventType.AGENT_TRANSFER
        assert info.transfer_to_agent == "rca_agent"

    def test_escalation_event(self):
        """Should classify escalation correctly."""
        event = MockEvent(
            author="loop_agent",
            content=MockContent(parts=[MockPart(text="Max retries reached")]),
            actions=MockActions(escalate=True),
        )
        info = classify_event(event)

        assert info.event_type == EventType.ESCALATION
        assert info.escalate is True

    def test_error_event(self):
        """Should classify error event correctly."""
        event = MockEvent(
            author="sysadmin",
            error_code="SAFETY_FILTER",
            error_message="Response blocked",
        )
        info = classify_event(event)

        assert info.event_type == EventType.ERROR
        assert info.error_code == "SAFETY_FILTER"
        assert info.error_message == "Response blocked"

    def test_unknown_event(self):
        """Should handle unknown event type."""
        event = MockEvent(author="unknown_agent", content=None, actions=None)
        info = classify_event(event)

        assert info.event_type == EventType.UNKNOWN


# =============================================================================
# EventAccumulator Tests
# =============================================================================


class TestEventAccumulator:
    """Tests for EventAccumulator class."""

    def test_accumulate_streaming_text(self):
        """Should accumulate streaming text chunks."""
        accumulator = EventAccumulator()

        # Add streaming chunks
        chunk1 = MockEvent(
            author="agent",
            content=MockContent(parts=[MockPart(text="Hello, ")]),
            partial=True,
        )
        chunk2 = MockEvent(
            author="agent",
            content=MockContent(parts=[MockPart(text="world!")]),
            partial=False,
        )

        accumulator.add(chunk1)
        assert accumulator.streaming_text == "Hello, "
        assert not accumulator.has_final_response

        accumulator.add(chunk2)
        assert accumulator.has_final_response
        assert accumulator.final_text == "Hello, world!"

    def test_track_tool_calls(self):
        """Should track tool calls."""
        accumulator = EventAccumulator()

        tool_event = MockEvent(
            author="agent",
            content=MockContent(
                parts=[
                    MockPart(
                        function_call=MockFunctionCall(
                            name="get_disk_usage",
                            args={"host": "server1"},
                        )
                    )
                ]
            ),
        )
        accumulator.add(tool_event)

        assert len(accumulator.tool_calls) == 1
        assert accumulator.tool_calls[0]["name"] == "get_disk_usage"
        assert accumulator.tool_calls[0]["args"] == {"host": "server1"}

    def test_track_tool_results(self):
        """Should track tool results."""
        accumulator = EventAccumulator()

        result_event = MockEvent(
            author="agent",
            content=MockContent(
                parts=[
                    MockPart(
                        function_response=MockFunctionResponse(
                            name="get_disk_usage",
                            response={"usage_percent": 85},
                        )
                    )
                ]
            ),
        )
        accumulator.add(result_event)

        assert len(accumulator.tool_results) == 1
        assert accumulator.tool_results[0]["name"] == "get_disk_usage"
        assert accumulator.tool_results[0]["response"] == {"usage_percent": 85}

    def test_track_state_changes(self):
        """Should track state changes."""
        accumulator = EventAccumulator()

        state_event = MockEvent(
            author="agent",
            actions=MockActions(state_delta={"analyzed_host": "server1"}),
        )
        accumulator.add(state_event)

        assert accumulator.state_changes == {"analyzed_host": "server1"}

    def test_reset(self):
        """Should reset accumulator."""
        accumulator = EventAccumulator()

        event = MockEvent(
            author="agent",
            content=MockContent(parts=[MockPart(text="Response")]),
            partial=False,
        )
        accumulator.add(event)

        assert accumulator.has_final_response
        assert len(accumulator.events) == 1

        accumulator.reset()

        assert not accumulator.has_final_response
        assert accumulator.final_text is None
        assert len(accumulator.events) == 0
        assert len(accumulator.tool_calls) == 0


# =============================================================================
# Logging and Formatting Tests
# =============================================================================


class TestLogging:
    """Tests for logging utilities."""

    def test_log_event(self):
        """Should log event without error."""
        event = MockEvent(
            author="sysadmin",
            content=MockContent(parts=[MockPart(text="Test response")]),
        )
        info = log_event(event)

        assert info.event_type == EventType.AGENT_TEXT
        assert info.text == "Test response"

    def test_format_event_summary(self):
        """Should format event summary."""
        event = MockEvent(
            author="sysadmin",
            content=MockContent(parts=[MockPart(text="Analysis complete.")]),
            partial=False,
        )
        summary = format_event_summary(event)

        assert "Event Type: agent_text" in summary
        assert "Author: sysadmin" in summary
        assert "Text: Analysis complete." in summary
        assert "FINAL RESPONSE" in summary


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for events module."""

    def test_core_exports_events(self):
        """Core module should export event utilities."""
        from core import (
            EventAccumulator,
            EventInfo,
            EventType,
            classify_event,
            format_event_summary,
            log_event,
        )

        assert EventType is not None
        assert EventInfo is not None
        assert EventAccumulator is not None
        assert callable(classify_event)
        assert callable(log_event)
        assert callable(format_event_summary)

    def test_full_conversation_flow(self):
        """Should handle a full conversation flow."""
        accumulator = EventAccumulator()

        # User input
        user_event = MockEvent(
            author="user",
            content=MockContent(parts=[MockPart(text="Check disk usage on server1")]),
        )
        info = accumulator.add(user_event)
        assert info.event_type == EventType.USER_INPUT

        # Agent makes tool call
        tool_call_event = MockEvent(
            author="capacity_agent",
            content=MockContent(
                parts=[
                    MockPart(
                        function_call=MockFunctionCall(
                            name="get_disk_usage",
                            args={"host": "server1"},
                        )
                    )
                ]
            ),
        )
        info = accumulator.add(tool_call_event)
        assert info.event_type == EventType.TOOL_CALL

        # Tool returns result
        tool_result_event = MockEvent(
            author="capacity_agent",
            content=MockContent(
                parts=[
                    MockPart(
                        function_response=MockFunctionResponse(
                            name="get_disk_usage",
                            response={"filesystem": "/", "usage_percent": 85},
                        )
                    )
                ]
            ),
        )
        info = accumulator.add(tool_result_event)
        assert info.event_type == EventType.TOOL_RESULT

        # Agent provides final response
        final_event = MockEvent(
            author="capacity_agent",
            content=MockContent(parts=[MockPart(text="Disk usage on server1 is at 85%.")]),
            partial=False,
        )
        info = accumulator.add(final_event)
        assert info.event_type == EventType.AGENT_TEXT
        assert info.is_final is True

        # Verify accumulator state
        assert len(accumulator.events) == 4
        assert len(accumulator.tool_calls) == 1
        assert len(accumulator.tool_results) == 1
        assert accumulator.has_final_response
        assert "85%" in accumulator.final_text
