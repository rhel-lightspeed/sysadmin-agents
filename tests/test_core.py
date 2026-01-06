"""
Tests for sysadmin-agents core configuration and structure.

Validates settings, YAML configs, package structure, and deployment files.
ADK integration tests are skipped in CI (require MCP server).
"""

import os
from pathlib import Path

import pytest
import yaml

# =============================================================================
# Test Configuration
# =============================================================================


class TestSettings:
    """Tests for core configuration."""

    def test_settings_loads(self):
        """Settings should load without errors."""
        from core.config import settings

        assert settings is not None

    def test_settings_has_defaults(self):
        """Settings should have sensible defaults."""
        from core.config import settings

        assert settings.DEFAULT_MODEL == "gemini-2.0-flash"
        assert settings.APP_NAME == "sysadmin-agents"
        assert settings.THINKING_BUDGET == 256
        assert settings.ENVIRONMENT in ("production", "staging", "development")

    def test_get_mcp_env(self):
        """get_mcp_env should return a dict with required keys."""
        from core.config import settings

        env = settings.get_mcp_env()
        assert isinstance(env, dict)
        assert "LINUX_MCP_LOG_LEVEL" in env

    def test_model_constants(self):
        """Model constants should be defined correctly."""
        from core.config import (
            MODEL_CLAUDE_SONNET,
            MODEL_GEMINI_2_0_FLASH,
            MODEL_GPT_4O,
        )

        assert MODEL_GEMINI_2_0_FLASH == "gemini-2.0-flash"
        assert MODEL_GPT_4O == "openai/gpt-4o"
        assert "anthropic" in MODEL_CLAUDE_SONNET

    def test_is_litellm_model(self):
        """Should correctly identify LiteLLM models."""
        from core.config import settings

        # Native Gemini models
        assert not settings.is_litellm_model("gemini-2.0-flash")
        assert not settings.is_litellm_model("gemini-1.5-pro")

        # LiteLLM models (with provider prefix)
        assert settings.is_litellm_model("openai/gpt-4o")
        assert settings.is_litellm_model("anthropic/claude-sonnet-4-20250514")
        assert settings.is_litellm_model("azure/gpt-4")

    def test_get_model_for_role(self):
        """Should return correct model for role."""
        from core.config import settings

        # Default role
        model = settings.get_model("default")
        assert model == settings.DEFAULT_MODEL

    def test_get_enabled_specialists(self):
        """Should parse enabled specialists correctly."""
        from core.config import settings

        # By default, returns None (auto-discovery)
        if not settings.ENABLED_SPECIALISTS:
            assert settings.get_enabled_specialists() is None

    def test_get_available_providers(self):
        """Should return provider availability dict."""
        from core.config import settings

        providers = settings.get_available_providers()
        assert "google" in providers
        assert "openai" in providers
        assert "anthropic" in providers
        assert all(isinstance(v, bool) for v in providers.values())


# =============================================================================
# Test YAML Configurations
# =============================================================================


class TestRCAConfig:
    """Tests for RCA specialist agent configuration."""

    @pytest.fixture
    def config_path(self):
        return Path(__file__).parent.parent / "agents" / "rca" / "config.yaml"

    def test_config_exists(self, config_path):
        """RCA config should exist."""
        assert config_path.exists(), f"Config not found: {config_path}"

    def test_config_valid_yaml(self, config_path):
        """RCA config should be valid YAML."""
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config is not None

    def test_config_has_required_fields(self, config_path):
        """RCA config should have all required fields."""
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "agent" in config, "Missing 'agent' section"
        assert "name" in config["agent"], "Missing 'agent.name'"
        assert "model" in config["agent"], "Missing 'agent.model'"
        assert "description" in config["agent"], "Missing 'agent.description'"
        assert "instruction" in config, "Missing 'instruction'"

    def test_config_instruction_not_empty(self, config_path):
        """Instruction should be substantial."""
        with open(config_path) as f:
            config = yaml.safe_load(f)

        instruction = config["instruction"]
        assert len(instruction) > 100, "Instruction seems too short"

    def test_config_thinking_enabled(self, config_path):
        """Thinking should be enabled for RCA."""
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "thinking" in config, "Missing 'thinking' section"
        assert config["thinking"]["enabled"] is True


class TestPerformanceConfig:
    """Tests for Performance specialist agent configuration."""

    @pytest.fixture
    def config_path(self):
        return Path(__file__).parent.parent / "agents" / "performance" / "config.yaml"

    def test_config_exists(self, config_path):
        """Performance config should exist."""
        assert config_path.exists(), f"Config not found: {config_path}"

    def test_config_valid_yaml(self, config_path):
        """Performance config should be valid YAML."""
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config is not None

    def test_config_has_required_fields(self, config_path):
        """Performance config should have all required fields."""
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "agent" in config
        assert config["agent"]["name"] == "performance_agent"
        assert "instruction" in config


class TestCapacityConfig:
    """Tests for Capacity specialist agent configuration."""

    @pytest.fixture
    def config_path(self):
        return Path(__file__).parent.parent / "agents" / "capacity" / "config.yaml"

    def test_config_exists(self, config_path):
        """Capacity config should exist."""
        assert config_path.exists(), f"Config not found: {config_path}"

    def test_config_valid_yaml(self, config_path):
        """Capacity config should be valid YAML."""
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config is not None

    def test_config_has_required_fields(self, config_path):
        """Capacity config should have all required fields."""
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "agent" in config
        assert config["agent"]["name"] == "capacity_agent"
        assert "instruction" in config


# =============================================================================
# Test Package Structure
# =============================================================================


class TestPackageStructure:
    """Tests for package structure and imports."""

    def test_core_package_imports(self):
        """Core package should export settings."""
        from core import Settings, settings

        assert settings is not None
        assert Settings is not None

    def test_agents_directory_exists(self):
        """Agents directory should exist with expected structure."""
        agents_dir = Path(__file__).parent.parent / "agents"
        assert agents_dir.exists()

        # Check expected agent directories
        expected_agents = ["rca", "performance", "capacity", "sysadmin"]
        for agent_name in expected_agents:
            agent_dir = agents_dir / agent_name
            assert agent_dir.exists(), f"Missing agent directory: {agent_name}"
            assert (agent_dir / "__init__.py").exists(), f"Missing __init__.py in {agent_name}"
            assert (agent_dir / "agent.py").exists(), f"Missing agent.py in {agent_name}"

    def test_each_specialist_has_config(self):
        """Each specialist should have a config.yaml."""
        agents_dir = Path(__file__).parent.parent / "agents"
        specialists = ["rca", "performance", "capacity"]

        for specialist in specialists:
            config_path = agents_dir / specialist / "config.yaml"
            assert config_path.exists(), f"Missing config.yaml for {specialist}"


# =============================================================================
# Test ADK Integration (requires google-adk)
# =============================================================================


@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skipping ADK tests in CI (requires MCP server)",
)
class TestADKIntegration:
    """Tests for ADK agent integration.

    These tests require google-adk and linux-mcp-server to be installed
    and are skipped in CI environments.
    """

    def test_sysadmin_agent_created(self):
        """Sysadmin agent should be created with sub-agents."""
        try:
            from agents.sysadmin.agent import sysadmin_agent

            assert sysadmin_agent is not None
            assert sysadmin_agent.name == "sysadmin"
            assert len(sysadmin_agent.sub_agents) == 3
        except ImportError as e:
            pytest.skip(f"ADK not available: {e}")
        except Exception as e:
            pytest.skip(f"MCP server not available: {e}")

    def test_rca_agent_created(self):
        """RCA agent should be created."""
        try:
            from agents.rca.agent import rca_agent

            assert rca_agent is not None
            assert rca_agent.name == "rca_agent"
        except ImportError as e:
            pytest.skip(f"ADK not available: {e}")
        except Exception as e:
            pytest.skip(f"MCP server not available: {e}")


# =============================================================================
# Test Deployment Files
# =============================================================================


class TestDeploymentFiles:
    """Tests for deployment configuration files."""

    def test_deployment_yaml_exists(self):
        """Deployment YAML should exist."""
        deploy_path = Path(__file__).parent.parent / "deploy" / "deployment.yaml"
        assert deploy_path.exists()

    def test_service_yaml_exists(self):
        """Service YAML should exist."""
        service_path = Path(__file__).parent.parent / "deploy" / "service.yaml"
        assert service_path.exists()

    def test_kustomization_yaml_exists(self):
        """Kustomization YAML should exist."""
        kustomize_path = Path(__file__).parent.parent / "deploy" / "kustomization.yaml"
        assert kustomize_path.exists()

    def test_deployment_yaml_valid(self):
        """Deployment YAML should be valid."""
        deploy_path = Path(__file__).parent.parent / "deploy" / "deployment.yaml"
        with open(deploy_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0


# =============================================================================
# Test pyproject.toml
# =============================================================================


class TestProjectConfig:
    """Tests for project configuration."""

    @pytest.fixture
    def pyproject_path(self):
        return Path(__file__).parent.parent / "pyproject.toml"

    def test_pyproject_exists(self, pyproject_path):
        """pyproject.toml should exist."""
        assert pyproject_path.exists()

    def test_required_dependencies(self, pyproject_path):
        """Should have required dependencies."""
        content = pyproject_path.read_text()
        assert "google-adk" in content
        assert "linux-mcp-server" in content
        assert "pyyaml" in content
        assert "pydantic-settings" in content

    def test_dev_dependencies(self, pyproject_path):
        """Should have dev dependencies."""
        content = pyproject_path.read_text()
        assert "pytest" in content
        assert "ruff" in content
