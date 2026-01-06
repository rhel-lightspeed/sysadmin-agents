"""
Configuration management using Pydantic Settings.

Environment variables and .env file are used for configuration.
Prompts and agent-specific settings are in YAML files.

Supports multi-model configuration via LiteLLM for flexibility.
"""

import os
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# =============================================================================
# Model Constants (for easy reference)
# =============================================================================

# Gemini Models
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"
MODEL_GEMINI_2_0_FLASH_THINKING = "gemini-2.0-flash-thinking-exp"
MODEL_GEMINI_1_5_PRO = "gemini-1.5-pro"

# OpenAI Models (via LiteLLM)
MODEL_GPT_4O = "openai/gpt-4o"
MODEL_GPT_4O_MINI = "openai/gpt-4o-mini"
MODEL_GPT_4_TURBO = "openai/gpt-4-turbo"

# Anthropic Models (via LiteLLM)
MODEL_CLAUDE_SONNET = "anthropic/claude-sonnet-4-20250514"
MODEL_CLAUDE_OPUS = "anthropic/claude-opus-4-20250514"
MODEL_CLAUDE_3_5_SONNET = "anthropic/claude-3-5-sonnet-20241022"


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables or .env file.

    Multi-Model Support:
        - DEFAULT_MODEL: Used when no model specified in agent config
        - Models starting with 'openai/' or 'anthropic/' use LiteLLM
        - Plain model names (e.g., 'gemini-2.0-flash') use native ADK
    """

    # ==========================================================================
    # LLM Configuration
    # ==========================================================================
    GOOGLE_API_KEY: str = ""
    DEFAULT_MODEL: str = MODEL_GEMINI_2_0_FLASH

    # Optional: API keys for multi-model support via LiteLLM
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Model selection for different agent roles
    DISPATCHER_MODEL: str = ""  # Empty = use DEFAULT_MODEL
    SPECIALIST_MODEL: str = ""  # Empty = use DEFAULT_MODEL

    # Thinking configuration for complex reasoning
    THINKING_BUDGET: int = 256
    INCLUDE_THOUGHTS: bool = True

    # ==========================================================================
    # Environment
    # ==========================================================================
    ENVIRONMENT: Literal["production", "staging", "development"] = "production"

    # ==========================================================================
    # MCP Server Configuration (linux-mcp-server)
    # ==========================================================================
    LINUX_MCP_SSH_KEY_PATH: str = "~/.ssh/id_ed25519"
    LINUX_MCP_USER: str = ""
    LINUX_MCP_KEY_PASSPHRASE: str = ""
    LINUX_MCP_ALLOWED_LOG_PATHS: str = "/var/log/messages,/var/log/secure"
    LINUX_MCP_LOG_LEVEL: str = "INFO"

    # ==========================================================================
    # Session Configuration
    # ==========================================================================
    SESSION_TTL_SECONDS: int = 3600
    APP_NAME: str = "sysadmin-agents"

    # ==========================================================================
    # SSL Configuration
    # ==========================================================================
    VERIFY_SSL: str = "/etc/ssl/certs/ca-bundle.crt"

    # ==========================================================================
    # Observability (Optional)
    # ==========================================================================
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    ENABLE_OBSERVABILITY: bool = False

    # ==========================================================================
    # Agent Discovery
    # ==========================================================================
    # Comma-separated list of specialist agents to enable
    # Empty means auto-discover all agents in specialists/
    ENABLED_SPECIALISTS: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def get_mcp_env(self) -> dict:
        """Get environment variables for linux-mcp-server.

        Returns:
            Dictionary of environment variables to pass to MCP server.
        """
        env = {
            "LINUX_MCP_LOG_LEVEL": self.LINUX_MCP_LOG_LEVEL,
        }

        # Expand ~ in SSH key path
        ssh_key_path = os.path.expanduser(self.LINUX_MCP_SSH_KEY_PATH)
        if os.path.exists(ssh_key_path):
            env["LINUX_MCP_SSH_KEY_PATH"] = ssh_key_path

        if self.LINUX_MCP_USER:
            env["LINUX_MCP_USER"] = self.LINUX_MCP_USER

        if self.LINUX_MCP_KEY_PASSPHRASE:
            env["LINUX_MCP_KEY_PASSPHRASE"] = self.LINUX_MCP_KEY_PASSPHRASE

        if self.LINUX_MCP_ALLOWED_LOG_PATHS:
            env["LINUX_MCP_ALLOWED_LOG_PATHS"] = self.LINUX_MCP_ALLOWED_LOG_PATHS

        return env

    def get_enabled_specialists(self) -> list[str] | None:
        """Get list of enabled specialist agents.

        Returns:
            List of agent names, or None for auto-discovery.
        """
        if not self.ENABLED_SPECIALISTS:
            return None
        return [s.strip() for s in self.ENABLED_SPECIALISTS.split(",") if s.strip()]

    def get_model(self, role: str = "default") -> str:
        """Get the appropriate model for a given role.

        Supports role-based model selection for different agent types.

        Args:
            role: One of 'default', 'dispatcher', 'specialist'

        Returns:
            Model identifier string
        """
        if role == "dispatcher" and self.DISPATCHER_MODEL:
            return self.DISPATCHER_MODEL
        elif role == "specialist" and self.SPECIALIST_MODEL:
            return self.SPECIALIST_MODEL
        return self.DEFAULT_MODEL

    def is_litellm_model(self, model: str) -> bool:
        """Check if a model requires LiteLLM wrapper.

        Models with provider prefixes (openai/, anthropic/) need LiteLLM.

        Args:
            model: Model identifier string

        Returns:
            True if model needs LiteLLM wrapper
        """
        litellm_prefixes = ["openai/", "anthropic/", "azure/", "cohere/", "huggingface/"]
        return any(model.startswith(prefix) for prefix in litellm_prefixes)

    def get_available_providers(self) -> dict[str, bool]:
        """Check which LLM providers have API keys configured.

        Returns:
            Dictionary mapping provider names to availability
        """
        return {
            "google": bool(self.GOOGLE_API_KEY),
            "openai": bool(self.OPENAI_API_KEY),
            "anthropic": bool(self.ANTHROPIC_API_KEY),
        }


# Global settings instance
settings = Settings()
