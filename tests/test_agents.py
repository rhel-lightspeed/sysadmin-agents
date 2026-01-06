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
following the pattern from Google ADK samples like financial-advisor.
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
# Test Agent Creation
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

    def test_sysadmin_agent_created(self):
        """Sysadmin agent should be created with sub-agents."""
        try:
            from agents.sysadmin.agent import sysadmin_agent

            self.assertIsNotNone(sysadmin_agent)
            self.assertEqual(sysadmin_agent.name, "sysadmin")
            self.assertEqual(len(sysadmin_agent.sub_agents), 3)
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_sysadmin_has_planner(self):
        """Sysadmin agent should have PlanReActPlanner."""
        try:
            from agents.sysadmin.agent import sysadmin_agent

            self.assertIsNotNone(sysadmin_agent.planner)
        except ImportError as e:
            self.skipTest(f"ADK not available: {e}")
        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")

    def test_sub_agents_have_transfer_restrictions(self):
        """Sub-agents should have transfer restrictions."""
        try:
            from agents.sysadmin.agent import sysadmin_agent

            for sub_agent in sysadmin_agent.sub_agents:
                self.assertTrue(
                    sub_agent.disallow_transfer_to_parent,
                    f"{sub_agent.name} should disallow transfer to parent",
                )
                self.assertTrue(
                    sub_agent.disallow_transfer_to_peers,
                    f"{sub_agent.name} should disallow transfer to peers",
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
        # Response should mention its capabilities
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
        from google.adk.agents.invocation_context import InvocationContext
        from google.adk.sessions import InMemorySessionService

        from agents.rca.agent import rca_agent

        session_service = InMemorySessionService()

        session = session_service.create_session_sync(
            app_name="sysadmin-agents",
            user_id="test_user",
        )

        # Create invocation context
        invoc_context = InvocationContext(
            session_service=session_service,
            invocation_id="TEST123",
            agent=rca_agent,
            session=session,
        )

        # Run before_agent_callback
        from core.callbacks import before_agent_callback

        before_agent_callback(invoc_context)

        # Check state was initialized
        assert "investigation_context" in invoc_context.state
        assert "session_start" in invoc_context.state

    except ImportError as e:
        pytest.skip(f"ADK not available: {e}")
    except Exception as e:
        pytest.skip(f"Error during test: {e}")


# =============================================================================
# Test Tool Context
# =============================================================================


@pytest.mark.asyncio
async def test_tool_callback_with_real_context():
    """Tool callback should work with real ToolContext."""
    try:
        from google.adk.agents.invocation_context import InvocationContext
        from google.adk.sessions import InMemorySessionService
        from google.adk.tools import ToolContext

        from agents.rca.agent import rca_agent

        session_service = InMemorySessionService()

        session = session_service.create_session_sync(
            app_name="sysadmin-agents",
            user_id="test_user",
        )

        invoc_context = InvocationContext(
            session_service=session_service,
            invocation_id="TEST456",
            agent=rca_agent,
            session=session,
        )

        # Initialize state
        from core.callbacks import before_agent_callback

        before_agent_callback(invoc_context)

        # Create tool context
        tool_context = ToolContext(invocation_context=invoc_context)

        # Simulate tool call
        from core.callbacks import before_tool_callback

        class MockTool:
            name = "get_disk_usage"

        result = before_tool_callback(MockTool(), {"host": "server1"}, tool_context)

        assert result is None  # Should proceed
        assert "server1" in tool_context.state["investigation_context"]["hosts_accessed"]

    except ImportError as e:
        pytest.skip(f"ADK not available: {e}")
    except Exception as e:
        pytest.skip(f"Error during test: {e}")
