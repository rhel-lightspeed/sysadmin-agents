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

"""Tests for the state management module."""

import time

from core.state import (
    InvestigationContext,
    StateKeys,
    StateManager,
    StatePrefix,
    get_investigation_context,
    initialize_session_state,
    save_investigation_context,
)


class TestStatePrefix:
    """Tests for StatePrefix constants."""

    def test_prefix_values(self):
        """Should have correct prefix values."""
        assert StatePrefix.USER == "user:"
        assert StatePrefix.APP == "app:"
        assert StatePrefix.TEMP == "temp:"


class TestStateKeys:
    """Tests for StateKeys constants."""

    def test_session_keys(self):
        """Session keys should not have prefixes."""
        assert StateKeys.INVESTIGATION_CONTEXT == "investigation_context"
        assert StateKeys.SESSION_START == "session_start"
        assert StateKeys.LAST_HOST_INVESTIGATED == "last_host_investigated"

    def test_user_keys(self):
        """User keys should have user: prefix."""
        assert StateKeys.USER_ALLOWED_HOSTS == "user:allowed_hosts"
        assert StateKeys.USER_PREFERENCES == "user:preferences"

    def test_app_keys(self):
        """App keys should have app: prefix."""
        assert StateKeys.APP_GLOBAL_SETTINGS == "app:global_settings"

    def test_temp_keys(self):
        """Temp keys should have temp: prefix."""
        assert StateKeys.TEMP_RATE_LIMIT_START == "temp:timer_start"
        assert StateKeys.TEMP_SECURITY_WARNING == "temp:security_warning"


class TestStateManager:
    """Tests for StateManager class."""

    def test_session_state_operations(self):
        """Should handle session-level state operations."""
        state = {}
        manager = StateManager(state)

        # Set and get
        manager.set("task_status", "active")
        assert manager.get("task_status") == "active"

        # Has
        assert manager.has("task_status")
        assert not manager.has("nonexistent")

        # Default value
        assert manager.get("nonexistent", "default") == "default"

        # Delete
        manager.delete("task_status")
        assert not manager.has("task_status")

    def test_user_state_operations(self):
        """Should handle user-level state with prefix."""
        state = {}
        manager = StateManager(state)

        # Set and get
        manager.set_user("theme", "dark")
        assert manager.get_user("theme") == "dark"

        # Verify actual key has prefix
        assert "user:theme" in state
        assert state["user:theme"] == "dark"

        # Has
        assert manager.has_user("theme")
        assert not manager.has_user("nonexistent")

    def test_app_state_operations(self):
        """Should handle app-level state with prefix."""
        state = {}
        manager = StateManager(state)

        # Set and get
        manager.set_app("api_endpoint", "https://api.example.com")
        assert manager.get_app("api_endpoint") == "https://api.example.com"

        # Verify actual key has prefix
        assert "app:api_endpoint" in state

        # Has
        assert manager.has_app("api_endpoint")

    def test_temp_state_operations(self):
        """Should handle temporary state with prefix."""
        state = {}
        manager = StateManager(state)

        # Set and get
        manager.set_temp("cache_key", "cached_value")
        assert manager.get_temp("cache_key") == "cached_value"

        # Verify actual key has prefix
        assert "temp:cache_key" in state

        # Has
        assert manager.has_temp("cache_key")

    def test_get_all(self):
        """Should return all state."""
        state = {"key1": "value1", "user:pref": "pref_value"}
        manager = StateManager(state)

        all_state = manager.get_all()
        assert all_state == state

    def test_get_session_state(self):
        """Should return only session-level state."""
        state = {
            "session_key": "session_value",
            "user:pref": "user_value",
            "app:setting": "app_value",
            "temp:cache": "temp_value",
        }
        manager = StateManager(state)

        session_state = manager.get_session_state()
        assert session_state == {"session_key": "session_value"}

    def test_get_user_state(self):
        """Should return only user-level state without prefix."""
        state = {
            "session_key": "session_value",
            "user:theme": "dark",
            "user:language": "en",
        }
        manager = StateManager(state)

        user_state = manager.get_user_state()
        assert user_state == {"theme": "dark", "language": "en"}

    def test_get_app_state(self):
        """Should return only app-level state without prefix."""
        state = {
            "session_key": "session_value",
            "app:endpoint": "https://api.example.com",
            "app:version": "1.0",
        }
        manager = StateManager(state)

        app_state = manager.get_app_state()
        assert app_state == {"endpoint": "https://api.example.com", "version": "1.0"}

    def test_get_temp_state(self):
        """Should return only temporary state without prefix."""
        state = {
            "session_key": "session_value",
            "temp:timer": 123.456,
            "temp:count": 5,
        }
        manager = StateManager(state)

        temp_state = manager.get_temp_state()
        assert temp_state == {"timer": 123.456, "count": 5}


class TestInvestigationContext:
    """Tests for InvestigationContext dataclass."""

    def test_create_empty_context(self):
        """Should create empty context."""
        context = InvestigationContext()
        assert context.hosts_accessed == []
        assert context.tools_used == []
        assert context.warnings == []
        assert context.findings == []

    def test_add_host(self):
        """Should add hosts without duplicates."""
        context = InvestigationContext()

        context.add_host("server1")
        assert context.hosts_accessed == ["server1"]

        context.add_host("server2")
        assert context.hosts_accessed == ["server1", "server2"]

        # Duplicate should not be added
        context.add_host("server1")
        assert context.hosts_accessed == ["server1", "server2"]

    def test_add_tool_usage(self):
        """Should track tool usage."""
        context = InvestigationContext()

        context.add_tool_usage("get_disk_usage", 1234567890.0)
        assert len(context.tools_used) == 1
        assert context.tools_used[0]["tool"] == "get_disk_usage"
        assert context.tools_used[0]["time"] == 1234567890.0

    def test_add_warning(self):
        """Should add warnings."""
        context = InvestigationContext()

        context.add_warning("High disk usage")
        assert context.warnings == ["High disk usage"]

    def test_add_finding(self):
        """Should add findings."""
        context = InvestigationContext()

        context.add_finding("Root cause identified")
        assert context.findings == ["Root cause identified"]

    def test_to_dict(self):
        """Should convert to dictionary."""
        context = InvestigationContext(
            hosts_accessed=["server1"],
            tools_used=[{"tool": "get_cpu_info", "time": 123.0}],
            start_time=100.0,
            warnings=["Warning 1"],
            findings=["Finding 1"],
        )

        result = context.to_dict()
        assert result["hosts_accessed"] == ["server1"]
        assert result["tools_used"] == [{"tool": "get_cpu_info", "time": 123.0}]
        assert result["start_time"] == 100.0
        assert result["warnings"] == ["Warning 1"]
        assert result["findings"] == ["Finding 1"]

    def test_from_dict(self):
        """Should create from dictionary."""
        data = {
            "hosts_accessed": ["server1", "server2"],
            "tools_used": [{"tool": "get_memory_info", "time": 456.0}],
            "start_time": 200.0,
            "warnings": ["High memory"],
            "findings": ["OOM detected"],
        }

        context = InvestigationContext.from_dict(data)
        assert context.hosts_accessed == ["server1", "server2"]
        assert context.tools_used == [{"tool": "get_memory_info", "time": 456.0}]
        assert context.start_time == 200.0
        assert context.warnings == ["High memory"]
        assert context.findings == ["OOM detected"]

    def test_from_dict_with_defaults(self):
        """Should handle missing keys with defaults."""
        context = InvestigationContext.from_dict({})
        assert context.hosts_accessed == []
        assert context.tools_used == []
        assert context.start_time == 0.0


class TestStateInitialization:
    """Tests for state initialization functions."""

    def test_initialize_session_state(self):
        """Should initialize default state values."""
        state = {}
        initialize_session_state(state)

        assert StateKeys.INVESTIGATION_CONTEXT in state
        assert StateKeys.SESSION_START in state

        # Check investigation context structure
        context_data = state[StateKeys.INVESTIGATION_CONTEXT]
        assert "hosts_accessed" in context_data
        assert "tools_used" in context_data
        assert "start_time" in context_data

    def test_initialize_preserves_existing(self):
        """Should not overwrite existing state."""
        existing_context = {"hosts_accessed": ["existing_host"]}
        state = {
            StateKeys.INVESTIGATION_CONTEXT: existing_context,
            StateKeys.SESSION_START: 12345.0,
        }

        initialize_session_state(state)

        # Should preserve existing values
        assert state[StateKeys.INVESTIGATION_CONTEXT] == existing_context
        assert state[StateKeys.SESSION_START] == 12345.0

    def test_get_investigation_context(self):
        """Should get investigation context from state."""
        state = {
            StateKeys.INVESTIGATION_CONTEXT: {
                "hosts_accessed": ["server1"],
                "tools_used": [],
                "start_time": 100.0,
                "warnings": [],
                "findings": [],
            }
        }

        context = get_investigation_context(state)
        assert isinstance(context, InvestigationContext)
        assert context.hosts_accessed == ["server1"]
        assert context.start_time == 100.0

    def test_save_investigation_context(self):
        """Should save investigation context to state."""
        state = {}
        context = InvestigationContext(
            hosts_accessed=["server1", "server2"],
            start_time=time.time(),
        )

        save_investigation_context(state, context)

        assert StateKeys.INVESTIGATION_CONTEXT in state
        saved_data = state[StateKeys.INVESTIGATION_CONTEXT]
        assert saved_data["hosts_accessed"] == ["server1", "server2"]


class TestIntegration:
    """Integration tests for state module."""

    def test_core_exports_state(self):
        """Core module should export state utilities."""
        from core import (
            InvestigationContext,
            StateKeys,
            StateManager,
            StatePrefix,
            get_investigation_context,
            initialize_session_state,
            save_investigation_context,
        )

        assert StateManager is not None
        assert StatePrefix is not None
        assert StateKeys is not None
        assert InvestigationContext is not None
        assert callable(initialize_session_state)
        assert callable(get_investigation_context)
        assert callable(save_investigation_context)

    def test_full_workflow(self):
        """Should handle a full state management workflow."""
        # Simulate session state
        state = {}

        # Initialize state (like in before_agent_callback)
        initialize_session_state(state)

        # Get context and track some activity
        context = get_investigation_context(state)
        context.add_host("webserver01")
        context.add_tool_usage("get_disk_usage", time.time())
        context.add_warning("Disk usage at 85%")

        # Save context back
        save_investigation_context(state, context)

        # Use StateManager for other state operations
        manager = StateManager(state)
        manager.set("last_host", "webserver01")
        manager.set_user("preferred_view", "detailed")
        manager.set_temp("rate_timer", time.time())

        # Verify state structure
        assert manager.get("last_host") == "webserver01"
        assert manager.get_user("preferred_view") == "detailed"
        assert manager.has_temp("rate_timer")

        # Retrieve context again
        final_context = get_investigation_context(state)
        assert "webserver01" in final_context.hosts_accessed
        assert len(final_context.tools_used) == 1
        assert "Disk usage at 85%" in final_context.warnings
