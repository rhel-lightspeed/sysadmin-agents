"""
Logging configuration for sysadmin-agents.

Provides structured logging with consistent formatting across all modules,
following ADK logging best practices.

ADK Logging Philosophy:
- Uses Python's standard logging module
- Hierarchical loggers based on module path (e.g., google_adk.google.adk.agents)
- Developer-configured, not framework-configured
- DEBUG for development, INFO/WARNING for production

Log Levels:
- DEBUG: Full LLM prompts, API responses, internal state transitions
- INFO: Agent initialization, session events, tool execution
- WARNING: Deprecated features, non-critical errors
- ERROR: Failed API calls, unhandled exceptions

Example usage:
    from core.logging_config import configure_logging, get_logger

    # Configure at application entry point
    configure_logging(level="DEBUG", format_style="detailed")

    # Get logger in your module
    logger = get_logger(__name__)
    logger.info("Agent started")
"""

import logging
import os
import sys
from typing import Literal

# =============================================================================
# Log Formats
# =============================================================================

# Default format - good for general use
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# Detailed format - includes function name and line number for debugging
DETAILED_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"

# Simple format - minimal output for quick debugging
SIMPLE_FORMAT = "%(levelname)s: %(message)s"

# JSON format - for structured logging in production
JSON_FORMAT = (
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
    '"logger": "%(name)s", "message": "%(message)s"}'
)

# ADK-style format - matches ADK's default output
ADK_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

FormatStyle = Literal["default", "detailed", "simple", "json", "adk"]

# =============================================================================
# Noisy Loggers to Quiet
# =============================================================================

# These loggers are typically too verbose at DEBUG level
NOISY_LOGGERS = [
    "httpx",
    "httpcore",
    "urllib3",
    "google.auth",
    "google.api_core",
    "grpc",
    "asyncio",
]

# ADK loggers that can be individually configured
ADK_LOGGERS = [
    "google_adk",
    "google_adk.google.adk.agents",
    "google_adk.google.adk.models",
    "google_adk.google.adk.runners",
    "google_adk.google.adk.tools",
    "google_adk.google.adk.sessions",
]

# =============================================================================
# Configuration Functions
# =============================================================================


def configure_logging(
    level: str = "INFO",
    format_style: FormatStyle = "default",
    log_file: str | None = None,
    quiet_noisy: bool = True,
    adk_level: str | None = None,
) -> None:
    """
    Configure application-wide logging following ADK best practices.

    This should be called at the application entry point before
    initializing any agents.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               DEBUG is recommended for development, INFO/WARNING for production.
        format_style: One of 'default', 'detailed', 'simple', 'json', or 'adk'.
        log_file: Optional path to log file. If provided, logs go to both
                  console and file.
        quiet_noisy: If True, set noisy library loggers to WARNING level.
        adk_level: Optional separate log level for ADK loggers. If None,
                   uses the same level as the main configuration.

    Example:
        # Development - see everything including LLM prompts
        configure_logging(level="DEBUG", format_style="detailed")

        # Production - only important events
        configure_logging(level="INFO", format_style="adk", quiet_noisy=True)

        # Debug ADK specifically
        configure_logging(level="WARNING", adk_level="DEBUG")
    """
    # Select format
    formats = {
        "default": DEFAULT_FORMAT,
        "detailed": DETAILED_FORMAT,
        "simple": SIMPLE_FORMAT,
        "json": JSON_FORMAT,
        "adk": ADK_FORMAT,
    }
    log_format = formats.get(format_style, DEFAULT_FORMAT)

    # Get log level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create handlers
    handlers: list[logging.Handler] = []

    # Console handler (always)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers,
        force=True,  # Override any existing configuration
    )

    # Quiet noisy loggers
    if quiet_noisy:
        for noisy_logger in NOISY_LOGGERS:
            logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # Configure ADK loggers separately if requested
    if adk_level:
        adk_log_level = getattr(logging, adk_level.upper(), log_level)
        for adk_logger in ADK_LOGGERS:
            logging.getLogger(adk_logger).setLevel(adk_log_level)

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={level}, format={format_style}")
    if adk_level:
        logger.info(f"ADK loggers set to: {adk_level}")


def configure_from_environment() -> None:
    """
    Configure logging from environment variables.

    Environment variables:
        LOG_LEVEL: Logging level (default: INFO)
        LOG_FORMAT: Format style (default: default)
        LOG_FILE: Optional log file path
        ADK_LOG_LEVEL: Optional separate level for ADK loggers

    Example:
        export LOG_LEVEL=DEBUG
        export LOG_FORMAT=detailed
        python main.py
    """
    level = os.environ.get("LOG_LEVEL", "INFO")
    format_style = os.environ.get("LOG_FORMAT", "default")
    log_file = os.environ.get("LOG_FILE")
    adk_level = os.environ.get("ADK_LOG_LEVEL")

    # Validate format style
    valid_formats = ["default", "detailed", "simple", "json", "adk"]
    if format_style not in valid_formats:
        format_style = "default"

    configure_logging(
        level=level,
        format_style=format_style,  # type: ignore
        log_file=log_file,
        adk_level=adk_level,
    )


def set_adk_debug(enable: bool = True) -> None:
    """
    Enable or disable DEBUG level for ADK loggers.

    This is useful for temporarily enabling detailed ADK logging
    to see LLM prompts and responses.

    Args:
        enable: If True, set ADK loggers to DEBUG. If False, set to INFO.
    """
    level = logging.DEBUG if enable else logging.INFO
    for adk_logger in ADK_LOGGERS:
        logging.getLogger(adk_logger).setLevel(level)

    logger = logging.getLogger(__name__)
    logger.info(f"ADK debug logging {'enabled' if enable else 'disabled'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    This is a convenience function that ensures consistent logger naming.

    Args:
        name: Logger name (typically __name__ of the calling module).

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)


# Module-level logger for this file
logger = get_logger(__name__)
