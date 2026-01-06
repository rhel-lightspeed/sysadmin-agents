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
Tests for agent loader module and core utilities.

Tests agent creation from configuration files,
following the direct testing pattern from Google ADK samples.
"""

import logging
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Test Config Loading - Using agent_loader.get_agent_config
# =============================================================================


def test_get_agent_config_rca():
    """Should load RCA agent config from root_agent.yaml."""
    from core.agent_loader import get_agent_config

    config_path = Path(__file__).parent.parent / "agents" / "rca" / "root_agent.yaml"
    config = get_agent_config(config_path)

    # ADK Agent Config format uses flat structure
    assert "name" in config
    assert "instruction" in config
    assert config["name"] == "rca_agent"


def test_get_agent_config_performance():
    """Should load Performance agent config from root_agent.yaml."""
    from core.agent_loader import get_agent_config

    config_path = Path(__file__).parent.parent / "agents" / "performance" / "root_agent.yaml"
    config = get_agent_config(config_path)

    assert config["name"] == "performance_agent"


def test_get_agent_config_capacity():
    """Should load Capacity agent config from root_agent.yaml."""
    from core.agent_loader import get_agent_config

    config_path = Path(__file__).parent.parent / "agents" / "capacity" / "root_agent.yaml"
    config = get_agent_config(config_path)

    assert config["name"] == "capacity_agent"


def test_get_agent_config_upgrade():
    """Should load Upgrade agent config from root_agent.yaml."""
    from core.agent_loader import get_agent_config

    config_path = Path(__file__).parent.parent / "agents" / "upgrade" / "root_agent.yaml"
    config = get_agent_config(config_path)

    assert config["name"] == "upgrade_agent"


def test_get_agent_config_sysadmin():
    """Should load Sysadmin orchestrator config from root_agent.yaml."""
    from core.agent_loader import get_agent_config

    config_path = Path(__file__).parent.parent / "agents" / "sysadmin" / "root_agent.yaml"
    config = get_agent_config(config_path)

    assert config["name"] == "sysadmin"
    assert "instruction" in config


# =============================================================================
# Test MCP Utilities - Direct function testing
# =============================================================================


def test_get_mcp_env_returns_dict():
    """Should return environment dict."""
    from core.mcp import get_mcp_env

    env = get_mcp_env()

    assert isinstance(env, dict)
    assert "LINUX_MCP_LOG_LEVEL" in env


def test_get_mcp_env_has_log_level():
    """Should include log level in env."""
    from core.mcp import get_mcp_env

    env = get_mcp_env()

    assert env["LINUX_MCP_LOG_LEVEL"] in ("DEBUG", "INFO", "WARNING", "ERROR")


def test_create_mcp_toolset_returns_or_none():
    """Should return toolset or None (depending on installation)."""
    from core.mcp import create_mcp_toolset

    result = create_mcp_toolset()

    # May return None if packages not installed, or a toolset if they are
    assert result is None or result is not None


def test_verify_mcp_installation_returns_status():
    """Should return installation status dict."""
    from core.mcp import verify_mcp_installation

    status = verify_mcp_installation()

    assert isinstance(status, dict)
    assert "mcp_installed" in status
    assert "adk_installed" in status
    assert "ssh_key_exists" in status
    assert "linux_mcp_server_available" in status
    assert "errors" in status
    assert isinstance(status["errors"], list)


# =============================================================================
# Test Agent File Structure - Verification tests
# =============================================================================


def test_rca_agent_uses_create_agent_with_mcp():
    """RCA agent should use create_agent_with_mcp pattern."""
    rca_path = Path(__file__).parent.parent / "agents" / "rca" / "agent.py"
    content = rca_path.read_text()

    # Should use create_agent_with_mcp (ADK workaround for MCP tools)
    assert "create_agent_with_mcp" in content
    assert "root_agent.yaml" in content


def test_performance_agent_uses_create_agent_with_mcp():
    """Performance agent should use create_agent_with_mcp pattern."""
    perf_path = Path(__file__).parent.parent / "agents" / "performance" / "agent.py"
    content = perf_path.read_text()

    # Should use create_agent_with_mcp
    assert "create_agent_with_mcp" in content
    assert "root_agent.yaml" in content


def test_capacity_agent_uses_create_agent_with_mcp():
    """Capacity agent should use create_agent_with_mcp pattern."""
    cap_path = Path(__file__).parent.parent / "agents" / "capacity" / "agent.py"
    content = cap_path.read_text()

    # Should use create_agent_with_mcp
    assert "create_agent_with_mcp" in content
    assert "root_agent.yaml" in content


def test_upgrade_agent_uses_create_agent_with_mcp():
    """Upgrade agent should use create_agent_with_mcp pattern."""
    upgrade_path = Path(__file__).parent.parent / "agents" / "upgrade" / "agent.py"
    content = upgrade_path.read_text()

    # Should use create_agent_with_mcp
    assert "create_agent_with_mcp" in content
    assert "root_agent.yaml" in content


def test_sysadmin_agent_is_orchestrator():
    """Sysadmin agent should be orchestrator with sub-agents."""
    sysadmin_path = Path(__file__).parent.parent / "agents" / "sysadmin" / "agent.py"
    content = sysadmin_path.read_text()

    # Should create sub-agents and compose orchestrator
    assert "sub_agents" in content
    assert "root_agent.yaml" in content
    # Should create fresh sub-agent instances
    assert "create_agent_with_mcp" in content


def test_agent_config_files_exist():
    """All agents should have root_agent.yaml Agent Config files."""
    agents_dir = Path(__file__).parent.parent / "agents"
    agent_dirs = ["rca", "performance", "capacity", "upgrade", "sysadmin"]

    for agent_name in agent_dirs:
        config_path = agents_dir / agent_name / "root_agent.yaml"
        assert config_path.exists(), f"Missing root_agent.yaml for {agent_name}"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify ADK Agent Config structure (flat format)
        assert "name" in config, f"{agent_name} config missing 'name'"
        assert "instruction" in config, f"{agent_name} config missing 'instruction'"


def test_all_agents_have_root_agent():
    """All agent modules should export root_agent."""
    agents_dir = Path(__file__).parent.parent / "agents"
    agent_dirs = ["rca", "performance", "capacity", "upgrade", "sysadmin"]

    for agent_name in agent_dirs:
        agent_path = agents_dir / agent_name / "agent.py"
        content = agent_path.read_text()
        assert "root_agent" in content, f"{agent_name} should export root_agent"


# =============================================================================
# Test YAML Config Contents - ADK Agent Config format
# =============================================================================


def test_rca_config_has_output_key():
    """RCA config should have output_key for session state."""
    config_path = Path(__file__).parent.parent / "agents" / "rca" / "root_agent.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "output_key" in config
    assert config["output_key"] == "last_rca_report"


def test_performance_config_has_output_key():
    """Performance config should have output_key for session state."""
    config_path = Path(__file__).parent.parent / "agents" / "performance" / "root_agent.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "output_key" in config


def test_capacity_config_has_output_key():
    """Capacity config should have output_key for session state."""
    config_path = Path(__file__).parent.parent / "agents" / "capacity" / "root_agent.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "output_key" in config


def test_agent_configs_have_generate_content_config():
    """Agent configs should have generate_content_config with temperature."""
    agents_dir = Path(__file__).parent.parent / "agents"
    agent_dirs = ["rca", "performance", "capacity", "upgrade", "sysadmin"]

    for agent_name in agent_dirs:
        config_path = agents_dir / agent_name / "root_agent.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check for generation config
        assert "generate_content_config" in config, (
            f"{agent_name} should have generate_content_config"
        )
        assert "temperature" in config["generate_content_config"], (
            f"{agent_name} should have temperature"
        )


# =============================================================================
# Test Core Package Exports
# =============================================================================


def test_core_exports_callbacks():
    """Core package should export callback functions."""
    from core import (
        after_tool_callback,
        before_agent_callback,
        before_tool_callback,
        create_callbacks_for_agent,
    )

    assert callable(create_callbacks_for_agent)
    assert callable(before_agent_callback)
    assert callable(before_tool_callback)
    assert callable(after_tool_callback)


def test_core_exports_types():
    """Core package should export type definitions."""
    from core import (
        ResourceStatus,
        SafetyRating,
        Severity,
    )

    assert Severity.CRITICAL.value == "critical"
    assert SafetyRating.SAFE.value == "safe"
    assert ResourceStatus.HEALTHY.value == "healthy"


def test_core_exports_agent_loader():
    """Core package should export agent_loader functions."""
    from core.agent_loader import create_agent_with_mcp, get_agent_config

    assert callable(create_agent_with_mcp)
    assert callable(get_agent_config)


# =============================================================================
# Test Callbacks Integration
# =============================================================================


def test_create_callbacks_for_agent_returns_dict():
    """create_callbacks_for_agent should return callback dict."""
    from core.callbacks import create_callbacks_for_agent

    callbacks = create_callbacks_for_agent(include_safety=False)

    assert isinstance(callbacks, dict)
    assert "before_model_callback" in callbacks
    assert "before_agent_callback" in callbacks
    assert "before_tool_callback" in callbacks
    assert "after_tool_callback" in callbacks


def test_callbacks_are_callable():
    """All callbacks should be callable functions."""
    from core.callbacks import create_callbacks_for_agent

    callbacks = create_callbacks_for_agent(include_safety=False)

    for name, callback in callbacks.items():
        assert callable(callback), f"{name} should be callable"
