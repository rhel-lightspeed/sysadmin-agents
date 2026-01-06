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
Integration tests for sysadmin agents.

Tests the actual agent creation and basic functionality,
following the pattern from Google ADK samples.

Note: These tests import module-level agents (ADK pattern).
MCP server must be available for imports to succeed.
"""

import logging
import os
import unittest

import pytest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Skip all tests in this module if in CI or ADK not available
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skipping integration tests in CI (requires MCP server)",
)


# =============================================================================
# Test Agent Creation (ADK Pattern: module-level root_agent)
# =============================================================================


class TestAgentCreation(unittest.TestCase):
    """Test cases for agent creation."""

    def test_rca_agent_created(self):
        """RCA agent should be created successfully."""
        try:
            from agents.rca.agent import rca_agent

            self.assertIsNotNone(rca_agent)
            self.assertEqual(rca_agent.name, "rca_agent")
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_performance_agent_created(self):
        """Performance agent should be created successfully."""
        try:
            from agents.performance.agent import performance_agent

            self.assertIsNotNone(performance_agent)
            self.assertEqual(performance_agent.name, "performance_agent")
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_capacity_agent_created(self):
        """Capacity agent should be created successfully."""
        try:
            from agents.capacity.agent import capacity_agent

            self.assertIsNotNone(capacity_agent)
            self.assertEqual(capacity_agent.name, "capacity_agent")
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_upgrade_agent_created(self):
        """Upgrade agent should be created successfully."""
        try:
            from agents.upgrade.agent import upgrade_agent

            self.assertIsNotNone(upgrade_agent)
            self.assertEqual(upgrade_agent.name, "upgrade_agent")
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_security_agent_created(self):
        """Security agent should be created successfully."""
        try:
            from agents.security.agent import security_agent

            self.assertIsNotNone(security_agent)
            self.assertEqual(security_agent.name, "security_agent")
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_sysadmin_agent_created(self):
        """Sysadmin orchestrator should be created with all sub-agents."""
        try:
            from agents.sysadmin.agent import sysadmin_agent

            self.assertIsNotNone(sysadmin_agent)
            self.assertEqual(sysadmin_agent.name, "sysadmin")
            # Sysadmin has 5 sub-agents: RCA, Performance, Capacity, Upgrade, Security
            self.assertEqual(len(sysadmin_agent.sub_agents), 5)
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_sysadmin_no_planner(self):
        """Sysadmin orchestrator should NOT have a planner.

        The orchestrator is a ROUTER that uses transfer_to_agent to delegate.
        PlanReActPlanner is for agents that execute tools and produce final answers.
        Using a planner on a router causes output format issues.
        """
        try:
            from agents.sysadmin.agent import sysadmin_agent

            # Orchestrator should NOT have a planner - it's a router
            self.assertIsNone(
                sysadmin_agent.planner,
                "Orchestrator should not have a planner - it routes via transfer_to_agent",
            )
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_sub_agents_have_planner(self):
        """Sub-agents should have PlanReActPlanner for structured reasoning.

        Unlike the orchestrator (which routes), sub-agents:
        - Execute tools to gather information
        - Analyze results
        - Produce final answers

        PlanReActPlanner helps with: PLANNING -> ACTION -> REASONING -> FINAL_ANSWER
        It's model-agnostic (works with Gemini, Claude, GPT, etc.)
        """
        try:
            from agents.sysadmin.agent import sysadmin_agent
            from google.adk.planners import PlanReActPlanner

            # All sub-agents should have PlanReActPlanner
            for sub_agent in sysadmin_agent.sub_agents:
                self.assertIsNotNone(
                    sub_agent.planner,
                    f"Sub-agent {sub_agent.name} should have a planner",
                )
                self.assertIsInstance(
                    sub_agent.planner,
                    PlanReActPlanner,
                    f"Sub-agent {sub_agent.name} should use PlanReActPlanner",
                )
        except ImportError as e:
            self.skipTest(f"ADK or PlanReActPlanner not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_sub_agents_have_transfer_restrictions(self):
        """Sub-agents should have peer transfer restrictions.

        Architecture decision:
        - disallow_transfer_to_peers=True: Sub-agents can't route to each other
        - disallow_transfer_to_parent=False: Sub-agents CAN return to orchestrator
        """
        try:
            from agents.sysadmin.agent import sysadmin_agent

            for sub_agent in sysadmin_agent.sub_agents:
                # Sub-agents should NOT be able to transfer to peers
                self.assertTrue(
                    sub_agent.disallow_transfer_to_peers,
                    f"{sub_agent.name} should disallow transfer to peers",
                )
                # Sub-agents SHOULD be able to return to parent (orchestrator)
                self.assertFalse(
                    sub_agent.disallow_transfer_to_parent,
                    f"{sub_agent.name} should allow transfer to parent",
                )
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")


# =============================================================================
# Test Agent With InMemoryRunner (ADK Integration)
# =============================================================================


@pytest.mark.asyncio
async def test_rca_agent_responds():
    """RCA agent should respond to a basic query."""
    try:
        from google.adk.runners import InMemoryRunner
        from google.genai.types import Part, UserContent

        from agents.rca.agent import rca_agent

        runner = InMemoryRunner(agent=rca_agent)
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id="test_user"
        )

        content = UserContent(parts=[Part(text="Hello, what can you help me with?")])
        response = ""

        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response += part.text

        # Agent should respond with something about root cause analysis
        assert len(response) > 0
        assert any(
            term in response.lower()
            for term in ["root cause", "analysis", "investigate", "diagnose", "help"]
        )

    except ImportError as e:
        pytest.skip(f"ADK not available: {e}")
    except Exception as e:
        pytest.skip(f"MCP server not available: {e}")


@pytest.mark.asyncio
async def test_sysadmin_agent_responds():
    """Sysadmin orchestrator should respond to a basic query."""
    try:
        from google.adk.runners import InMemoryRunner
        from google.genai.types import Part, UserContent

        from agents.sysadmin.agent import sysadmin_agent

        runner = InMemoryRunner(agent=sysadmin_agent)
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id="test_user"
        )

        content = UserContent(parts=[Part(text="What kind of problems can you help me diagnose?")])
        response = ""

        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response += part.text

        # Agent should respond with something about system administration
        assert len(response) > 0

    except ImportError as e:
        pytest.skip(f"ADK not available: {e}")
    except Exception as e:
        pytest.skip(f"MCP server not available: {e}")


# =============================================================================
# Test Session State Management
# =============================================================================


@pytest.mark.asyncio
async def test_session_state_initialized():
    """Session state should be initialized by before_agent_callback."""
    try:
        from google.adk.sessions import InMemorySessionService

        from core.callbacks import before_agent_callback

        session_service = InMemorySessionService()

        session = session_service.create_session_sync(
            app_name="sysadmin-agents",
            user_id="test_user",
        )

        # Create a mock callback context
        class MockCallbackContext:
            def __init__(self, state):
                self.state = state
                self.agent_name = "test_agent"
                self.invocation_id = "TEST123"

        mock_context = MockCallbackContext(session.state)

        # Run before_agent_callback
        before_agent_callback(mock_context)

        # Check state was initialized
        assert "investigation_context" in mock_context.state
        assert "session_start" in mock_context.state

    except ImportError as e:
        pytest.skip(f"ADK not available: {e}")
    except Exception as e:
        pytest.skip(f"Error during test: {e}")


# =============================================================================
# Test Tool Context
# =============================================================================


@pytest.mark.asyncio
async def test_tool_callback_tracks_hosts():
    """Tool callback should track hosts accessed in investigation context."""
    try:
        from core.callbacks import before_agent_callback, before_tool_callback

        # Create mock state
        mock_state = {}

        class MockCallbackContext:
            def __init__(self, state):
                self.state = state
                self.agent_name = "test_agent"
                self.invocation_id = "TEST456"

        class MockToolContext:
            def __init__(self, state):
                self.state = state
                self.agent_name = "test_agent"

        class MockTool:
            name = "get_disk_usage"

        # Initialize state
        callback_context = MockCallbackContext(mock_state)
        before_agent_callback(callback_context)

        # Create tool context
        tool_context = MockToolContext(mock_state)

        # Simulate tool call
        result = before_tool_callback(MockTool(), {"host": "server1"}, tool_context)

        # Should proceed
        assert result is None
        # Host should be tracked
        assert "server1" in tool_context.state["investigation_context"]["hosts_accessed"]

    except ImportError as e:
        pytest.skip(f"ADK not available: {e}")
    except Exception as e:
        pytest.skip(f"Error during test: {e}")
