"""
Core configuration module for sysadmin-agents.

Provides centralized settings management, MCP utilities, and shared functions.

Module Organization:
-------------------
**Actively Used by Agents:**
- config.py: Settings and model constants
- mcp.py: MCP toolset creation
- agent_loader.py: create_agent_with_mcp() for agent creation with callbacks
- callbacks.py: Security callbacks (rate limiting, input validation)
- safety.py: Gemini-as-a-Judge safety screening

**Infrastructure Modules (for structured outputs and future use):**
- types.py: Pydantic models for structured agent outputs (RCAReport, etc.)
- artifacts.py: Artifact storage utilities
- state.py: Session state management utilities
- events.py: Event classification and logging

**Utilities:**
- utils.py: General utilities (config loading, logging setup)
"""

from core.agent_loader import (
    create_agent_with_mcp,
    get_agent_config,
)
from core.artifacts import (
    ArtifactFilenames,
    ArtifactHelper,
    ArtifactMetadata,
    MimeType,
    save_capacity_report,
    save_performance_report,
    save_rca_report,
)
from core.callbacks import (
    after_tool_callback,
    before_agent_callback,
    before_tool_callback,
    create_before_model_callback,
    create_callbacks_for_agent,
    rate_limit_callback,
)
from core.config import (
    MODEL_CLAUDE_SONNET,
    MODEL_GEMINI_2_0_FLASH,
    MODEL_GPT_4O,
    Settings,
    settings,
)
from core.events import (
    EventAccumulator,
    EventInfo,
    EventType,
    classify_event,
    format_event_summary,
    log_event,
)
from core.logging_config import (
    configure_from_environment,
    configure_logging,
    get_logger,
    set_adk_debug,
)
from core.mcp import (
    create_mcp_toolset,
    get_mcp_env,
    verify_mcp_installation,
)
from core.safety import (
    BLOCKED_RESPONSE,
    GeminiSafetyJudge,
    SafetyResult,
    SafetyVerdict,
    ThreatCategory,
    get_safety_judge,
    quick_screen_input,
    quick_screen_output,
)
from core.state import (
    InvestigationContext,
    StateKeys,
    StateManager,
    StatePrefix,
    get_investigation_context,
    initialize_session_state,
    save_investigation_context,
)
from core.tools import get_mcp_toolset, linux_mcp_tools
from core.types import (
    CapacityReport,
    CleanupRecommendation,
    DirectorySize,
    FilesystemUsage,
    HostInfo,
    PerformanceReport,
    ProcessInfo,
    RCAReport,
    Recommendation,
    ResourceStatus,
    ResourceUsage,
    SafetyRating,
    Severity,
    TimelineEvent,
)
from core.utils import (
    get_project_root,
    load_agent_config,
    load_config_for_agent,
    setup_logging,
)

__all__ = [
    # === ACTIVELY USED ===
    # Agent Loader (primary agent creation)
    "create_agent_with_mcp",
    "get_agent_config",
    # Settings
    "settings",
    "Settings",
    # Model constants
    "MODEL_GEMINI_2_0_FLASH",
    "MODEL_GPT_4O",
    "MODEL_CLAUDE_SONNET",
    # MCP utilities
    "get_mcp_env",
    "create_mcp_toolset",
    "verify_mcp_installation",
    # Callbacks
    "create_callbacks_for_agent",
    "create_before_model_callback",
    "before_agent_callback",
    "before_tool_callback",
    "after_tool_callback",
    "rate_limit_callback",
    # Safety (Gemini as a Judge)
    "GeminiSafetyJudge",
    "SafetyVerdict",
    "SafetyResult",
    "ThreatCategory",
    "get_safety_judge",
    "quick_screen_input",
    "quick_screen_output",
    "BLOCKED_RESPONSE",
    # Logging
    "configure_logging",
    "configure_from_environment",
    "get_logger",
    "set_adk_debug",
    # === INFRASTRUCTURE (for structured outputs) ===
    # Types (Pydantic models for structured agent outputs)
    "Severity",
    "SafetyRating",
    "ResourceStatus",
    "HostInfo",
    "TimelineEvent",
    "Recommendation",
    "RCAReport",
    "ResourceUsage",
    "ProcessInfo",
    "PerformanceReport",
    "FilesystemUsage",
    "DirectorySize",
    "CleanupRecommendation",
    "CapacityReport",
    # State Management
    "StateManager",
    "StatePrefix",
    "StateKeys",
    "InvestigationContext",
    "initialize_session_state",
    "get_investigation_context",
    "save_investigation_context",
    # Events
    "EventType",
    "EventInfo",
    "EventAccumulator",
    "classify_event",
    "log_event",
    "format_event_summary",
    # Artifacts
    "ArtifactHelper",
    "ArtifactFilenames",
    "ArtifactMetadata",
    "MimeType",
    "save_rca_report",
    "save_performance_report",
    "save_capacity_report",
    # Tools for Agent Config
    "get_mcp_toolset",
    "linux_mcp_tools",
    # === UTILITIES ===
    # Config utilities
    "load_agent_config",
    "load_config_for_agent",
    "get_project_root",
    "setup_logging",
]
