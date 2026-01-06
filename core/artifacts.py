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
Artifact management utilities for ADK agents.

This module provides utilities for managing artifacts (binary data like files,
reports, images) following ADK best practices.

Artifacts Overview:
- Artifacts are named, versioned binary data stored outside session state
- They are represented as google.genai.types.Part with inline_data
- Storage is managed by an ArtifactService (InMemory or GCS)
- Artifacts can be session-scoped or user-scoped (with "user:" prefix)

Filename Conventions:
- Session-scoped: "report.pdf", "analysis.json" (tied to session)
- User-scoped: "user:preferences.json", "user:settings.yaml" (persists across sessions)

Example usage:
    from core.artifacts import ArtifactHelper, ArtifactFilenames

    # In a tool or callback
    helper = ArtifactHelper(tool_context)

    # Save a report
    version = await helper.save_text("analysis.txt", "Report content here")

    # Save JSON data
    version = await helper.save_json("metrics.json", {"cpu": 85, "memory": 70})

    # Load an artifact
    content = await helper.load_text("analysis.txt")
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# MIME Types for Common Artifact Types
# =============================================================================


class MimeType(str, Enum):
    """Common MIME types for artifacts."""

    # Text formats
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    TEXT_CSV = "text/csv"
    TEXT_MARKDOWN = "text/markdown"

    # Application formats
    JSON = "application/json"
    XML = "application/xml"
    PDF = "application/pdf"
    ZIP = "application/zip"
    GZIP = "application/gzip"
    TAR = "application/x-tar"

    # Image formats
    PNG = "image/png"
    JPEG = "image/jpeg"
    GIF = "image/gif"
    SVG = "image/svg+xml"

    # Log formats
    LOG = "text/x-log"
    SYSLOG = "text/x-syslog"


# =============================================================================
# Standard Artifact Filenames
# =============================================================================


class ArtifactFilenames:
    """
    Standard artifact filenames for sysadmin agents.

    Using consistent filenames makes it easier to find and manage artifacts.
    """

    # Session-scoped artifacts (tied to current session)
    RCA_REPORT = "rca_report.json"
    RCA_REPORT_PDF = "rca_report.pdf"
    RCA_REPORT_MD = "rca_report.md"

    PERFORMANCE_REPORT = "performance_report.json"
    PERFORMANCE_REPORT_PDF = "performance_report.pdf"

    CAPACITY_REPORT = "capacity_report.json"
    CAPACITY_REPORT_PDF = "capacity_report.pdf"

    SYSTEM_LOGS = "system_logs.txt"
    DIAGNOSTIC_DATA = "diagnostic_data.json"
    ANALYSIS_SUMMARY = "analysis_summary.md"

    # User-scoped artifacts (persist across sessions)
    USER_PREFERENCES = "user:preferences.json"
    USER_HOST_CONFIG = "user:host_config.json"
    USER_SAVED_REPORTS = "user:saved_reports.json"


# =============================================================================
# Artifact Metadata
# =============================================================================


@dataclass
class ArtifactMetadata:
    """Metadata for an artifact."""

    filename: str
    mime_type: str
    size_bytes: int
    version: int
    created_at: datetime
    is_user_scoped: bool

    @classmethod
    def from_artifact(
        cls,
        filename: str,
        data: bytes,
        mime_type: str,
        version: int,
    ) -> "ArtifactMetadata":
        """Create metadata from artifact data."""
        return cls(
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(data),
            version=version,
            created_at=datetime.now(),
            is_user_scoped=filename.startswith("user:"),
        )


# =============================================================================
# Artifact Helper
# =============================================================================


class ArtifactHelper:
    """
    Helper class for working with artifacts in callbacks and tools.

    Provides convenient methods for common artifact operations like
    saving/loading text, JSON, and binary data.

    Example:
        async def my_tool(tool_context: ToolContext) -> str:
            helper = ArtifactHelper(tool_context)

            # Save analysis results
            await helper.save_json("analysis.json", {"status": "ok"})

            # Load previous results
            data = await helper.load_json("analysis.json")
            return f"Previous analysis: {data}"
    """

    def __init__(self, context: Any):
        """
        Initialize with a context object.

        Args:
            context: CallbackContext or ToolContext with artifact methods
        """
        self._context = context

    # -------------------------------------------------------------------------
    # Service Availability Check
    # -------------------------------------------------------------------------

    def is_available(self) -> bool:
        """Check if artifact service is available."""
        # Check if context has artifact methods and they're functional
        return (
            hasattr(self._context, "save_artifact")
            and hasattr(self._context, "load_artifact")
            and hasattr(self._context, "list_artifacts")
        )

    # -------------------------------------------------------------------------
    # Text Artifacts
    # -------------------------------------------------------------------------

    async def save_text(
        self,
        filename: str,
        content: str,
        encoding: str = "utf-8",
    ) -> int:
        """
        Save text content as an artifact.

        Args:
            filename: Artifact filename
            content: Text content to save
            encoding: Text encoding (default: utf-8)

        Returns:
            Version number of saved artifact
        """
        from google.genai import types

        data = content.encode(encoding)
        artifact = types.Part.from_bytes(data=data, mime_type=MimeType.TEXT_PLAIN)

        version = await self._context.save_artifact(filename=filename, artifact=artifact)
        logger.info(f"Saved text artifact: {filename} (version {version}, {len(data)} bytes)")
        return version

    async def load_text(
        self,
        filename: str,
        version: int | None = None,
        encoding: str = "utf-8",
    ) -> str | None:
        """
        Load text content from an artifact.

        Args:
            filename: Artifact filename
            version: Specific version to load (None for latest)
            encoding: Text encoding (default: utf-8)

        Returns:
            Text content or None if not found
        """
        artifact = await self._context.load_artifact(filename=filename, version=version)

        if artifact is None or artifact.inline_data is None:
            logger.debug(f"Text artifact not found: {filename}")
            return None

        content = artifact.inline_data.data.decode(encoding)
        logger.debug(f"Loaded text artifact: {filename} ({len(content)} chars)")
        return content

    # -------------------------------------------------------------------------
    # JSON Artifacts
    # -------------------------------------------------------------------------

    async def save_json(
        self,
        filename: str,
        data: dict[str, Any] | list[Any],
        indent: int = 2,
    ) -> int:
        """
        Save JSON data as an artifact.

        Args:
            filename: Artifact filename
            data: JSON-serializable data
            indent: JSON indentation (default: 2)

        Returns:
            Version number of saved artifact
        """
        from google.genai import types

        json_str = json.dumps(data, indent=indent, default=str)
        json_bytes = json_str.encode("utf-8")
        artifact = types.Part.from_bytes(data=json_bytes, mime_type=MimeType.JSON)

        version = await self._context.save_artifact(filename=filename, artifact=artifact)
        logger.info(f"Saved JSON artifact: {filename} (version {version}, {len(json_bytes)} bytes)")
        return version

    async def load_json(
        self,
        filename: str,
        version: int | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Load JSON data from an artifact.

        Args:
            filename: Artifact filename
            version: Specific version to load (None for latest)

        Returns:
            Parsed JSON data or None if not found
        """
        artifact = await self._context.load_artifact(filename=filename, version=version)

        if artifact is None or artifact.inline_data is None:
            logger.debug(f"JSON artifact not found: {filename}")
            return None

        json_str = artifact.inline_data.data.decode("utf-8")
        data = json.loads(json_str)
        logger.debug(f"Loaded JSON artifact: {filename}")
        return data

    # -------------------------------------------------------------------------
    # Binary Artifacts
    # -------------------------------------------------------------------------

    async def save_binary(
        self,
        filename: str,
        data: bytes,
        mime_type: str,
    ) -> int:
        """
        Save binary data as an artifact.

        Args:
            filename: Artifact filename
            data: Binary data to save
            mime_type: MIME type of the data

        Returns:
            Version number of saved artifact
        """
        from google.genai import types

        artifact = types.Part.from_bytes(data=data, mime_type=mime_type)

        version = await self._context.save_artifact(filename=filename, artifact=artifact)
        logger.info(
            f"Saved binary artifact: {filename} (version {version}, {len(data)} bytes, {mime_type})"
        )
        return version

    async def load_binary(
        self,
        filename: str,
        version: int | None = None,
    ) -> tuple[bytes, str] | None:
        """
        Load binary data from an artifact.

        Args:
            filename: Artifact filename
            version: Specific version to load (None for latest)

        Returns:
            Tuple of (data, mime_type) or None if not found
        """
        artifact = await self._context.load_artifact(filename=filename, version=version)

        if artifact is None or artifact.inline_data is None:
            logger.debug(f"Binary artifact not found: {filename}")
            return None

        data = artifact.inline_data.data
        mime_type = artifact.inline_data.mime_type
        logger.debug(f"Loaded binary artifact: {filename} ({len(data)} bytes, {mime_type})")
        return (data, mime_type)

    # -------------------------------------------------------------------------
    # Markdown Artifacts (for reports)
    # -------------------------------------------------------------------------

    async def save_markdown(
        self,
        filename: str,
        content: str,
    ) -> int:
        """
        Save Markdown content as an artifact.

        Args:
            filename: Artifact filename
            content: Markdown content to save

        Returns:
            Version number of saved artifact
        """
        from google.genai import types

        data = content.encode("utf-8")
        artifact = types.Part.from_bytes(data=data, mime_type=MimeType.TEXT_MARKDOWN)

        version = await self._context.save_artifact(filename=filename, artifact=artifact)
        logger.info(f"Saved Markdown artifact: {filename} (version {version})")
        return version

    async def load_markdown(
        self,
        filename: str,
        version: int | None = None,
    ) -> str | None:
        """
        Load Markdown content from an artifact.

        Args:
            filename: Artifact filename
            version: Specific version to load (None for latest)

        Returns:
            Markdown content or None if not found
        """
        artifact = await self._context.load_artifact(filename=filename, version=version)

        if artifact is None or artifact.inline_data is None:
            logger.debug(f"Markdown artifact not found: {filename}")
            return None

        return artifact.inline_data.data.decode("utf-8")

    # -------------------------------------------------------------------------
    # Listing Artifacts
    # -------------------------------------------------------------------------

    async def list_all(self) -> list[str]:
        """
        List all artifact filenames.

        Returns:
            List of artifact filenames
        """
        try:
            artifacts = await self._context.list_artifacts()
            return list(artifacts) if artifacts else []
        except ValueError:
            logger.warning("Artifact service not configured")
            return []

    async def list_session_artifacts(self) -> list[str]:
        """
        List only session-scoped artifacts (no user: prefix).

        Returns:
            List of session-scoped artifact filenames
        """
        all_artifacts = await self.list_all()
        return [f for f in all_artifacts if not f.startswith("user:")]

    async def list_user_artifacts(self) -> list[str]:
        """
        List only user-scoped artifacts (with user: prefix).

        Returns:
            List of user-scoped artifact filenames
        """
        all_artifacts = await self.list_all()
        return [f for f in all_artifacts if f.startswith("user:")]

    # -------------------------------------------------------------------------
    # Existence Check
    # -------------------------------------------------------------------------

    async def exists(self, filename: str) -> bool:
        """
        Check if an artifact exists.

        Args:
            filename: Artifact filename to check

        Returns:
            True if artifact exists, False otherwise
        """
        artifact = await self._context.load_artifact(filename=filename)
        return artifact is not None


# =============================================================================
# Report Artifact Helpers
# =============================================================================


async def save_rca_report(
    context: Any,
    report_data: dict[str, Any],
    include_markdown: bool = True,
) -> dict[str, int]:
    """
    Save an RCA report as both JSON and optionally Markdown.

    Args:
        context: CallbackContext or ToolContext
        report_data: RCA report data dictionary
        include_markdown: Also save as Markdown (default: True)

    Returns:
        Dictionary mapping filenames to version numbers
    """
    helper = ArtifactHelper(context)
    versions = {}

    # Save JSON version
    json_version = await helper.save_json(ArtifactFilenames.RCA_REPORT, report_data)
    versions[ArtifactFilenames.RCA_REPORT] = json_version

    # Optionally save Markdown version
    if include_markdown:
        md_content = _format_rca_as_markdown(report_data)
        md_version = await helper.save_markdown(ArtifactFilenames.RCA_REPORT_MD, md_content)
        versions[ArtifactFilenames.RCA_REPORT_MD] = md_version

    return versions


def _format_rca_as_markdown(report: dict[str, Any]) -> str:
    """Format RCA report data as Markdown."""
    lines = ["# Root Cause Analysis Report", ""]

    if "summary" in report:
        lines.extend(["## Summary", "", report["summary"], ""])

    if "root_cause" in report:
        lines.extend(["## Root Cause", "", report["root_cause"], ""])

    if "timeline" in report:
        lines.extend(["## Timeline", ""])
        for event in report.get("timeline", []):
            time_str = event.get("time", "Unknown")
            description = event.get("description", "")
            lines.append(f"- **{time_str}**: {description}")
        lines.append("")

    if "recommendations" in report:
        lines.extend(["## Recommendations", ""])
        for rec in report.get("recommendations", []):
            lines.append(f"- {rec}")
        lines.append("")

    if "affected_systems" in report:
        lines.extend(["## Affected Systems", ""])
        for system in report.get("affected_systems", []):
            lines.append(f"- {system}")
        lines.append("")

    return "\n".join(lines)


async def save_performance_report(
    context: Any,
    report_data: dict[str, Any],
) -> int:
    """
    Save a performance report as JSON.

    Args:
        context: CallbackContext or ToolContext
        report_data: Performance report data dictionary

    Returns:
        Version number
    """
    helper = ArtifactHelper(context)
    return await helper.save_json(ArtifactFilenames.PERFORMANCE_REPORT, report_data)


async def save_capacity_report(
    context: Any,
    report_data: dict[str, Any],
) -> int:
    """
    Save a capacity report as JSON.

    Args:
        context: CallbackContext or ToolContext
        report_data: Capacity report data dictionary

    Returns:
        Version number
    """
    helper = ArtifactHelper(context)
    return await helper.save_json(ArtifactFilenames.CAPACITY_REPORT, report_data)
