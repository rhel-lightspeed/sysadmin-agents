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
Tests for ADK callback functions.

Tests callbacks using real function calls with minimal state objects,
following the pattern used in Google ADK samples.
"""

import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Simple state container for testing (mimics ADK context.state)
# =============================================================================


class SimpleState(dict):
    """Dict-like state container for testing callbacks."""

    pass


class SimpleContext:
    """Simple context object for testing callbacks."""

    def __init__(self, state: dict | None = None):
        self.state = SimpleState(state or {})


class SimpleTool:
    """Simple tool object for testing callbacks."""

    def __init__(self, name: str):
        self.name = name


class SimpleLlmRequest:
    """Simple LLM request object for testing callbacks."""

    def __init__(self, contents: list | None = None):
        self.contents = contents or []


class SimplePart:
    """Simple part object for testing callbacks."""

    def __init__(self, text: str = ""):
        self.text = text


class SimpleContent:
    """Simple content object for testing callbacks."""

    def __init__(self, parts: list | None = None):
        self.parts = parts or []


# =============================================================================
# Test Rate Limiting - Direct function testing
# =============================================================================


def test_rate_limit_initializes_state_on_first_call():
    """Should initialize timer and counter on first call."""
    from core.callbacks import rate_limit_callback

    context = SimpleContext()
    request = SimpleLlmRequest()

    rate_limit_callback(context, request)

    assert "timer_start" in context.state
    assert context.state["request_count"] == 1


def test_rate_limit_increments_counter():
    """Should increment request counter on each call."""
    from core.callbacks import rate_limit_callback

    context = SimpleContext(
        {
            "timer_start": time.time(),
            "request_count": 5,
        }
    )
    request = SimpleLlmRequest()

    rate_limit_callback(context, request)

    assert context.state["request_count"] == 6


def test_rate_limit_fixes_empty_text_parts():
    """Should fix empty text parts that can cause API errors."""
    from core.callbacks import rate_limit_callback

    part = SimplePart(text="")
    content = SimpleContent(parts=[part])
    request = SimpleLlmRequest(contents=[content])
    context = SimpleContext()

    rate_limit_callback(context, request)

    assert part.text == " "


# =============================================================================
# Test Input Validation - Direct function testing
# =============================================================================


def test_input_validation_detects_dangerous_rm_rf():
    """Should detect rm -rf / pattern."""
    from core.callbacks import input_validation_callback

    part = SimplePart(text="Please run rm -rf / on the server")
    content = SimpleContent(parts=[part])
    request = SimpleLlmRequest(contents=[content])
    context = SimpleContext()

    input_validation_callback(context, request)

    assert "security_warning" in context.state
    assert "Blocked" in context.state["security_warning"]


def test_input_validation_detects_mkfs():
    """Should detect mkfs pattern."""
    from core.callbacks import input_validation_callback

    part = SimplePart(text="Run mkfs.ext4 /dev/sda1")
    content = SimpleContent(parts=[part])
    request = SimpleLlmRequest(contents=[content])
    context = SimpleContext()

    input_validation_callback(context, request)

    assert "security_warning" in context.state


def test_input_validation_detects_systemctl_stop():
    """Should detect systemctl stop pattern."""
    from core.callbacks import input_validation_callback

    part = SimplePart(text="Run systemctl stop nginx")
    content = SimpleContent(parts=[part])
    request = SimpleLlmRequest(contents=[content])
    context = SimpleContext()

    input_validation_callback(context, request)

    assert "security_warning" in context.state
    assert "Sensitive" in context.state["security_warning"]


def test_input_validation_allows_safe_requests():
    """Should not flag safe requests."""
    from core.callbacks import input_validation_callback

    part = SimplePart(text="Check disk usage on server1")
    content = SimpleContent(parts=[part])
    request = SimpleLlmRequest(contents=[content])
    context = SimpleContext()

    input_validation_callback(context, request)

    assert "security_warning" not in context.state


def test_input_validation_handles_empty_request():
    """Should handle request with no contents."""
    from core.callbacks import input_validation_callback

    request = SimpleLlmRequest(contents=[])
    context = SimpleContext()

    # Should not raise
    input_validation_callback(context, request)

    assert "security_warning" not in context.state


# =============================================================================
# Test Before Agent Callback - Direct function testing
# =============================================================================


def test_before_agent_initializes_investigation_context():
    """Should initialize investigation context on new session."""
    from core.callbacks import before_agent_callback

    context = SimpleContext()

    before_agent_callback(context)

    assert "investigation_context" in context.state
    ctx = context.state["investigation_context"]
    assert "hosts_accessed" in ctx
    assert "tools_used" in ctx
    assert "start_time" in ctx
    assert isinstance(ctx["hosts_accessed"], list)
    assert isinstance(ctx["tools_used"], list)


def test_before_agent_initializes_session_start():
    """Should track session start time."""
    from core.callbacks import before_agent_callback

    context = SimpleContext()

    before_agent_callback(context)

    assert "session_start" in context.state
    assert isinstance(context.state["session_start"], float)


def test_before_agent_preserves_existing_context():
    """Should not overwrite existing investigation context."""
    from core.callbacks import before_agent_callback

    existing_context = {
        "hosts_accessed": ["server1", "server2"],
        "tools_used": [{"tool": "get_disk_usage", "time": 12345.0}],
        "start_time": 12345.0,
    }
    context = SimpleContext({"investigation_context": existing_context})

    before_agent_callback(context)

    # Should preserve existing data
    assert context.state["investigation_context"]["hosts_accessed"] == ["server1", "server2"]
    assert len(context.state["investigation_context"]["tools_used"]) == 1


def test_before_agent_initializes_allowed_hosts():
    """Should initialize allowed_hosts if not present."""
    from core.callbacks import before_agent_callback

    context = SimpleContext()

    before_agent_callback(context)

    assert "allowed_hosts" in context.state
    assert isinstance(context.state["allowed_hosts"], list)


# =============================================================================
# Test Before Tool Callback - Direct function testing
# =============================================================================


def test_before_tool_tracks_tool_usage():
    """Should track tool calls in investigation context."""
    from core.callbacks import before_tool_callback

    tool = SimpleTool(name="get_disk_usage")
    context = SimpleContext(
        {
            "investigation_context": {
                "hosts_accessed": [],
                "tools_used": [],
                "start_time": time.time(),
            }
        }
    )

    result = before_tool_callback(tool, {"host": "server1"}, context)

    assert result is None  # Should proceed
    assert len(context.state["investigation_context"]["tools_used"]) == 1
    assert context.state["investigation_context"]["tools_used"][0]["tool"] == "get_disk_usage"


def test_before_tool_tracks_host_access():
    """Should track host access for host-aware tools."""
    from core.callbacks import before_tool_callback

    tool = SimpleTool(name="get_system_information")
    context = SimpleContext(
        {
            "investigation_context": {
                "hosts_accessed": [],
                "tools_used": [],
                "start_time": time.time(),
            }
        }
    )

    before_tool_callback(tool, {"host": "webserver01"}, context)

    assert "webserver01" in context.state["investigation_context"]["hosts_accessed"]
    assert context.state["last_host_investigated"] == "webserver01"


def test_before_tool_does_not_duplicate_hosts():
    """Should not duplicate hosts in accessed list."""
    from core.callbacks import before_tool_callback

    tool = SimpleTool(name="get_cpu_information")
    context = SimpleContext(
        {
            "investigation_context": {
                "hosts_accessed": ["server1"],
                "tools_used": [],
                "start_time": time.time(),
            }
        }
    )

    before_tool_callback(tool, {"host": "server1"}, context)
    before_tool_callback(tool, {"host": "server1"}, context)

    assert context.state["investigation_context"]["hosts_accessed"].count("server1") == 1


def test_before_tool_tracks_multiple_hosts():
    """Should track multiple different hosts."""
    from core.callbacks import before_tool_callback

    tool = SimpleTool(name="get_memory_information")
    context = SimpleContext(
        {
            "investigation_context": {
                "hosts_accessed": [],
                "tools_used": [],
                "start_time": time.time(),
            }
        }
    )

    before_tool_callback(tool, {"host": "server1"}, context)
    before_tool_callback(tool, {"host": "server2"}, context)
    before_tool_callback(tool, {"host": "server3"}, context)

    hosts = context.state["investigation_context"]["hosts_accessed"]
    assert len(hosts) == 3
    assert "server1" in hosts
    assert "server2" in hosts
    assert "server3" in hosts


def test_before_tool_handles_non_host_tool():
    """Should handle tools that don't require host parameter."""
    from core.callbacks import before_tool_callback

    tool = SimpleTool(name="some_other_tool")
    context = SimpleContext(
        {
            "investigation_context": {
                "hosts_accessed": [],
                "tools_used": [],
                "start_time": time.time(),
            }
        }
    )

    result = before_tool_callback(tool, {"param": "value"}, context)

    assert result is None
    assert len(context.state["investigation_context"]["tools_used"]) == 1


# =============================================================================
# Test After Tool Callback - Direct function testing
# =============================================================================


def test_after_tool_detects_high_disk_usage():
    """Should flag high disk usage in session state."""
    from core.callbacks import after_tool_callback

    tool = SimpleTool(name="get_disk_usage")
    context = SimpleContext()
    response = {"usage_percent": 95, "mount": "/"}

    after_tool_callback(tool, {"host": "server1"}, context, response)

    assert "disk_warning" in context.state
    assert context.state["disk_warning"]["usage_percent"] == 95
    assert context.state["disk_warning"]["host"] == "server1"


def test_after_tool_detects_high_memory_usage():
    """Should flag high memory usage in session state."""
    from core.callbacks import after_tool_callback

    tool = SimpleTool(name="get_memory_information")
    context = SimpleContext()
    response = {"percent_used": 92, "total_mb": 16384}

    after_tool_callback(tool, {"host": "dbserver"}, context, response)

    assert "memory_warning" in context.state
    assert context.state["memory_warning"]["percent_used"] == 92
    assert context.state["memory_warning"]["host"] == "dbserver"


def test_after_tool_ignores_normal_disk_usage():
    """Should not flag normal disk usage."""
    from core.callbacks import after_tool_callback

    tool = SimpleTool(name="get_disk_usage")
    context = SimpleContext()
    response = {"usage_percent": 50}

    after_tool_callback(tool, {"host": "server1"}, context, response)

    assert "disk_warning" not in context.state


def test_after_tool_ignores_normal_memory_usage():
    """Should not flag normal memory usage."""
    from core.callbacks import after_tool_callback

    tool = SimpleTool(name="get_memory_information")
    context = SimpleContext()
    response = {"percent_used": 65}

    after_tool_callback(tool, {"host": "server1"}, context, response)

    assert "memory_warning" not in context.state


def test_after_tool_handles_non_dict_response():
    """Should handle non-dict responses gracefully."""
    from core.callbacks import after_tool_callback

    tool = SimpleTool(name="get_disk_usage")
    context = SimpleContext()

    # Should not raise for string response
    result = after_tool_callback(tool, {"host": "server1"}, context, "some string")
    assert result is None

    # Should not raise for list response
    result = after_tool_callback(tool, {"host": "server1"}, context, ["item1", "item2"])
    assert result is None


# =============================================================================
# Test Callback Factory - Direct function testing
# =============================================================================


def test_create_callbacks_returns_all_callbacks():
    """Should return dict with all callback functions."""
    from core.callbacks import create_callbacks_for_agent

    callbacks = create_callbacks_for_agent()

    assert isinstance(callbacks, dict)
    assert "before_model_callback" in callbacks
    assert "before_agent_callback" in callbacks
    assert "before_tool_callback" in callbacks
    assert "after_tool_callback" in callbacks


def test_callbacks_are_callable():
    """All returned callbacks should be callable."""
    from core.callbacks import create_callbacks_for_agent

    callbacks = create_callbacks_for_agent()

    for name, callback in callbacks.items():
        assert callable(callback), f"{name} should be callable"


def test_combined_before_model_callback():
    """Combined callback should run both rate limiting and validation."""
    from core.callbacks import create_before_model_callback

    callback = create_before_model_callback()
    context = SimpleContext()
    request = SimpleLlmRequest()

    callback(context, request)

    # Rate limiting should have initialized
    assert "timer_start" in context.state
    assert "request_count" in context.state


def test_combined_callback_validates_input():
    """Combined callback should detect dangerous patterns."""
    from core.callbacks import create_before_model_callback

    callback = create_before_model_callback()
    part = SimplePart(text="run rm -rf / now")
    content = SimpleContent(parts=[part])
    request = SimpleLlmRequest(contents=[content])
    context = SimpleContext()

    callback(context, request)

    assert "security_warning" in context.state
