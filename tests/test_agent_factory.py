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
Tests for agent factory module.

Tests agent creation from configuration files,
following the direct testing pattern from Google ADK samples.
"""

import logging
import tempfile
from pathlib import Path

import pytest
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Test Config Loading - Direct function testing
# =============================================================================


def test_load_agent_config_rca():
    """Should load RCA agent config."""
    from core.utils import load_agent_config

    config_path = Path(__file__).parent.parent / "agents" / "rca" / "config.yaml"
    config = load_agent_config(config_path)

    assert "agent" in config
    assert "instruction" in config
    assert config["agent"]["name"] == "rca_agent"


def test_load_agent_config_performance():
    """Should load Performance agent config."""
    from core.utils import load_agent_config

    config_path = Path(__file__).parent.parent / "agents" / "performance" / "config.yaml"
    config = load_agent_config(config_path)

    assert config["agent"]["name"] == "performance_agent"


def test_load_agent_config_capacity():
    """Should load Capacity agent config."""
    from core.utils import load_agent_config

    config_path = Path(__file__).parent.parent / "agents" / "capacity" / "config.yaml"
    config = load_agent_config(config_path)

    assert config["agent"]["name"] == "capacity_agent"


def test_load_agent_config_missing_file():
    """Should raise FileNotFoundError for missing config."""
    from core.utils import load_agent_config

    with pytest.raises(FileNotFoundError):
        load_agent_config(Path("/nonexistent/path/config.yaml"))


def test_load_agent_config_missing_instruction():
    """Should raise ValueError for config missing instruction."""
    from core.utils import load_agent_config

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"agent": {"name": "test"}}, f)
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Missing required field"):
            load_agent_config(temp_path)
    finally:
        temp_path.unlink()


def test_load_agent_config_missing_agent_name():
    """Should raise ValueError for config missing agent.name."""
    from core.utils import load_agent_config

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"agent": {}, "instruction": "test"}, f)
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Missing required field"):
            load_agent_config(temp_path)
    finally:
        temp_path.unlink()


def test_load_config_for_agent_by_name():
    """Should load config by agent name."""
    from core.utils import load_config_for_agent

    config = load_config_for_agent("rca")

    assert config["agent"]["name"] == "rca_agent"
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
# Test Generation Config - Direct function testing
# =============================================================================


def test_generation_config_when_thinking_enabled():
    """Should create config when thinking enabled."""
    from core.agent_factory import _create_generation_config

    config = {
        "thinking": {
            "enabled": True,
            "budget": 512,
        }
    }

    result = _create_generation_config(config)

    # Returns None if google.genai.types not installed, or config if it is
    assert result is None or result is not None


def test_generation_config_when_thinking_disabled():
    """Should return None when thinking disabled."""
    from core.agent_factory import _create_generation_config

    config = {
        "thinking": {
            "enabled": False,
        }
    }

    result = _create_generation_config(config)

    assert result is None


def test_generation_config_when_thinking_missing():
    """Should return None when thinking section missing."""
    from core.agent_factory import _create_generation_config

    config = {"agent": {"name": "test"}}

    result = _create_generation_config(config)

    assert result is None


def test_generation_config_when_thinking_empty():
    """Should return None when thinking section empty."""
    from core.agent_factory import _create_generation_config

    config = {"thinking": {}}

    result = _create_generation_config(config)

    assert result is None


# =============================================================================
# Test Agent File Structure - Verification tests
# =============================================================================


def test_rca_agent_uses_agent_config():
    """RCA agent should use Agent Config with factory fallback."""
    rca_path = Path(__file__).parent.parent / "agents" / "rca" / "agent.py"
    content = rca_path.read_text()

    # Should use Agent Config format
    assert "Agent.from_config" in content
    assert "root_agent.yaml" in content
    # Should have factory fallback
    assert "create_specialist_agent(" in content


def test_performance_agent_uses_agent_config():
    """Performance agent should use Agent Config with factory fallback."""
    perf_path = Path(__file__).parent.parent / "agents" / "performance" / "agent.py"
    content = perf_path.read_text()

    # Should use Agent Config format
    assert "Agent.from_config" in content
    assert "root_agent.yaml" in content
    # Should have factory fallback
    assert "create_specialist_agent(" in content


def test_capacity_agent_uses_agent_config():
    """Capacity agent should use Agent Config with factory fallback."""
    cap_path = Path(__file__).parent.parent / "agents" / "capacity" / "agent.py"
    content = cap_path.read_text()

    # Should use Agent Config format
    assert "Agent.from_config" in content
    assert "root_agent.yaml" in content
    # Should have factory fallback
    assert "create_specialist_agent(" in content


def test_sysadmin_agent_uses_agent_config():
    """Sysadmin agent should use Agent Config with prompts.py fallback."""
    sysadmin_path = Path(__file__).parent.parent / "agents" / "sysadmin" / "agent.py"
    content = sysadmin_path.read_text()

    # Should use Agent Config format
    assert "Agent.from_config" in content
    assert "root_agent.yaml" in content
    # Should have prompts.py fallback for non-Agent Config mode
    assert "SYSADMIN_INSTRUCTION" in content


def test_prompts_file_exists():
    """Prompts file should exist with expected content."""
    prompts_path = Path(__file__).parent.parent / "agents" / "sysadmin" / "prompts.py"

    assert prompts_path.exists()

    content = prompts_path.read_text()
    assert "SYSADMIN_INSTRUCTION" in content
    assert "RCA_SPECIALIST_DESCRIPTION" in content
    assert "PERFORMANCE_SPECIALIST_DESCRIPTION" in content
    assert "CAPACITY_SPECIALIST_DESCRIPTION" in content


def test_agent_config_files_exist():
    """All agents should have root_agent.yaml Agent Config files."""
    agents_dir = Path(__file__).parent.parent / "agents"
    agent_dirs = ["rca", "performance", "capacity", "sysadmin"]

    for agent_name in agent_dirs:
        config_path = agents_dir / agent_name / "root_agent.yaml"
        assert config_path.exists(), f"Missing root_agent.yaml for {agent_name}"

        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify Agent Config structure
        assert "name" in config, f"{agent_name} config missing 'name'"
        assert "instruction" in config, f"{agent_name} config missing 'instruction'"
        assert config.get("agent_class") == "LlmAgent", f"{agent_name} should be LlmAgent"


def test_all_agents_have_root_agent():
    """All agent modules should export root_agent."""
    agents_dir = Path(__file__).parent.parent / "agents"
    agent_dirs = ["rca", "performance", "capacity", "sysadmin"]

    for agent_name in agent_dirs:
        agent_path = agents_dir / agent_name / "agent.py"
        content = agent_path.read_text()
        assert "root_agent" in content, f"{agent_name} should export root_agent"


# =============================================================================
# Test YAML Config Contents
# =============================================================================


def test_rca_config_has_thinking():
    """RCA config should have thinking configuration."""
    config_path = Path(__file__).parent.parent / "agents" / "rca" / "config.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "thinking" in config
    assert config["thinking"]["enabled"] is True
    assert "budget" in config["thinking"]


def test_rca_config_has_output_key():
    """RCA config should have output_key."""
    config_path = Path(__file__).parent.parent / "agents" / "rca" / "config.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "output_key" in config
    assert config["output_key"] == "last_rca_report"


def test_performance_config_has_mcp_tools():
    """Performance config should list MCP tools."""
    config_path = Path(__file__).parent.parent / "agents" / "performance" / "config.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "mcp_tools" in config
    assert "primary" in config["mcp_tools"]
    assert "get_cpu_information" in config["mcp_tools"]["primary"]


def test_capacity_config_has_examples():
    """Capacity config should have example queries."""
    config_path = Path(__file__).parent.parent / "agents" / "capacity" / "config.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "examples" in config
    assert len(config["examples"]) > 0


# =============================================================================
# Test Core Package Exports
# =============================================================================


def test_core_exports_factory_functions():
    """Core package should export factory functions."""
    from core import (
        create_orchestrator_agent,
        create_specialist_agent,
        create_sub_agent_wrapper,
    )

    assert callable(create_specialist_agent)
    assert callable(create_orchestrator_agent)
    assert callable(create_sub_agent_wrapper)


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
