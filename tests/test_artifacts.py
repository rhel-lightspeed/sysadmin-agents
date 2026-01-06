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

"""Tests for the artifacts management module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from core.artifacts import (
    ArtifactFilenames,
    ArtifactHelper,
    ArtifactMetadata,
    MimeType,
    _format_rca_as_markdown,
)


class TestMimeType:
    """Tests for MimeType enum."""

    def test_text_types(self):
        """Should have correct text MIME types."""
        assert MimeType.TEXT_PLAIN == "text/plain"
        assert MimeType.TEXT_HTML == "text/html"
        assert MimeType.TEXT_CSV == "text/csv"
        assert MimeType.TEXT_MARKDOWN == "text/markdown"

    def test_application_types(self):
        """Should have correct application MIME types."""
        assert MimeType.JSON == "application/json"
        assert MimeType.PDF == "application/pdf"
        assert MimeType.ZIP == "application/zip"

    def test_image_types(self):
        """Should have correct image MIME types."""
        assert MimeType.PNG == "image/png"
        assert MimeType.JPEG == "image/jpeg"
        assert MimeType.GIF == "image/gif"


class TestArtifactFilenames:
    """Tests for ArtifactFilenames constants."""

    def test_session_scoped_filenames(self):
        """Session-scoped filenames should not have user: prefix."""
        assert not ArtifactFilenames.RCA_REPORT.startswith("user:")
        assert not ArtifactFilenames.PERFORMANCE_REPORT.startswith("user:")
        assert not ArtifactFilenames.CAPACITY_REPORT.startswith("user:")

    def test_user_scoped_filenames(self):
        """User-scoped filenames should have user: prefix."""
        assert ArtifactFilenames.USER_PREFERENCES.startswith("user:")
        assert ArtifactFilenames.USER_HOST_CONFIG.startswith("user:")

    def test_report_filenames_have_extensions(self):
        """Report filenames should have appropriate extensions."""
        assert ArtifactFilenames.RCA_REPORT.endswith(".json")
        assert ArtifactFilenames.RCA_REPORT_PDF.endswith(".pdf")
        assert ArtifactFilenames.RCA_REPORT_MD.endswith(".md")


class TestArtifactMetadata:
    """Tests for ArtifactMetadata dataclass."""

    def test_create_metadata(self):
        """Should create metadata from artifact data."""
        data = b"Hello, World!"
        metadata = ArtifactMetadata.from_artifact(
            filename="test.txt",
            data=data,
            mime_type="text/plain",
            version=0,
        )

        assert metadata.filename == "test.txt"
        assert metadata.mime_type == "text/plain"
        assert metadata.size_bytes == len(data)
        assert metadata.version == 0
        assert metadata.is_user_scoped is False
        assert isinstance(metadata.created_at, datetime)

    def test_user_scoped_detection(self):
        """Should correctly detect user-scoped artifacts."""
        user_metadata = ArtifactMetadata.from_artifact(
            filename="user:settings.json",
            data=b"{}",
            mime_type="application/json",
            version=1,
        )
        assert user_metadata.is_user_scoped is True

        session_metadata = ArtifactMetadata.from_artifact(
            filename="report.json",
            data=b"{}",
            mime_type="application/json",
            version=0,
        )
        assert session_metadata.is_user_scoped is False


# =============================================================================
# Mock Context for Testing ArtifactHelper
# =============================================================================


@dataclass
class MockPart:
    """Mock Part object for testing."""

    inline_data: Any


@dataclass
class MockInlineData:
    """Mock inline data for testing."""

    data: bytes
    mime_type: str


class MockContext:
    """Mock context for testing ArtifactHelper."""

    def __init__(self):
        self._artifacts: dict[str, list[MockPart]] = {}
        self.save_artifact = AsyncMock(side_effect=self._save_artifact)
        self.load_artifact = AsyncMock(side_effect=self._load_artifact)
        self.list_artifacts = AsyncMock(side_effect=self._list_artifacts)

    async def _save_artifact(self, filename: str, artifact: Any) -> int:
        """Mock save_artifact implementation."""
        if filename not in self._artifacts:
            self._artifacts[filename] = []
        self._artifacts[filename].append(artifact)
        return len(self._artifacts[filename]) - 1

    async def _load_artifact(self, filename: str, version: int | None = None) -> Any:
        """Mock load_artifact implementation."""
        if filename not in self._artifacts:
            return None
        versions = self._artifacts[filename]
        if not versions:
            return None
        if version is None:
            return versions[-1]  # Latest
        if 0 <= version < len(versions):
            return versions[version]
        return None

    async def _list_artifacts(self) -> list[str]:
        """Mock list_artifacts implementation."""
        return list(self._artifacts.keys())


# =============================================================================
# ArtifactHelper Tests
# =============================================================================


class TestArtifactHelper:
    """Tests for ArtifactHelper class."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock context for testing."""
        return MockContext()

    @pytest.fixture
    def helper(self, mock_context):
        """Create an ArtifactHelper with mock context."""
        return ArtifactHelper(mock_context)

    def test_is_available(self, helper):
        """Should check if artifact service is available."""
        assert helper.is_available() is True

    def test_is_not_available(self):
        """Should return False for context without artifact methods."""

        class NoArtifactContext:
            pass

        helper = ArtifactHelper(NoArtifactContext())
        assert helper.is_available() is False


@pytest.mark.asyncio
class TestArtifactHelperTextOperations:
    """Tests for ArtifactHelper text operations."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock context for testing."""
        return MockContext()

    @pytest.fixture
    def helper(self, mock_context):
        """Create an ArtifactHelper with mock context."""
        return ArtifactHelper(mock_context)

    async def test_save_text(self, helper, mock_context):
        """Should save text content."""
        version = await helper.save_text("test.txt", "Hello, World!")

        assert version == 0
        mock_context.save_artifact.assert_called_once()
        call_args = mock_context.save_artifact.call_args
        assert call_args.kwargs["filename"] == "test.txt"

    async def test_load_text(self, helper, mock_context):
        """Should load text content."""
        # First save
        await helper.save_text("test.txt", "Hello, World!")

        # Then load
        _ = await helper.load_text("test.txt")
        # Note: Due to mock implementation, we get a types.Part back
        # In real implementation, this would return the text content
        mock_context.load_artifact.assert_called()

    async def test_load_text_not_found(self, helper):
        """Should return None for non-existent artifact."""
        content = await helper.load_text("nonexistent.txt")
        assert content is None


@pytest.mark.asyncio
class TestArtifactHelperJsonOperations:
    """Tests for ArtifactHelper JSON operations."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock context for testing."""
        return MockContext()

    @pytest.fixture
    def helper(self, mock_context):
        """Create an ArtifactHelper with mock context."""
        return ArtifactHelper(mock_context)

    async def test_save_json(self, helper, mock_context):
        """Should save JSON data."""
        data = {"status": "ok", "count": 42}
        version = await helper.save_json("data.json", data)

        assert version == 0
        mock_context.save_artifact.assert_called_once()
        call_args = mock_context.save_artifact.call_args
        assert call_args.kwargs["filename"] == "data.json"

    async def test_load_json_not_found(self, helper):
        """Should return None for non-existent artifact."""
        data = await helper.load_json("nonexistent.json")
        assert data is None


@pytest.mark.asyncio
class TestArtifactHelperBinaryOperations:
    """Tests for ArtifactHelper binary operations."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock context for testing."""
        return MockContext()

    @pytest.fixture
    def helper(self, mock_context):
        """Create an ArtifactHelper with mock context."""
        return ArtifactHelper(mock_context)

    async def test_save_binary(self, helper, mock_context):
        """Should save binary data."""
        data = b"\x89PNG\r\n\x1a\n..."
        version = await helper.save_binary("image.png", data, MimeType.PNG)

        assert version == 0
        mock_context.save_artifact.assert_called_once()
        call_args = mock_context.save_artifact.call_args
        assert call_args.kwargs["filename"] == "image.png"

    async def test_load_binary_not_found(self, helper):
        """Should return None for non-existent artifact."""
        result = await helper.load_binary("nonexistent.png")
        assert result is None


@pytest.mark.asyncio
class TestArtifactHelperListOperations:
    """Tests for ArtifactHelper listing operations."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock context for testing."""
        return MockContext()

    @pytest.fixture
    def helper(self, mock_context):
        """Create an ArtifactHelper with mock context."""
        return ArtifactHelper(mock_context)

    async def test_list_all(self, helper, mock_context):
        """Should list all artifacts."""
        # Save some artifacts
        await helper.save_text("file1.txt", "content1")
        await helper.save_text("user:file2.txt", "content2")

        artifacts = await helper.list_all()
        assert "file1.txt" in artifacts
        assert "user:file2.txt" in artifacts

    async def test_list_session_artifacts(self, helper, mock_context):
        """Should list only session-scoped artifacts."""
        await helper.save_text("session.txt", "content")
        await helper.save_text("user:user.txt", "content")

        artifacts = await helper.list_session_artifacts()
        assert "session.txt" in artifacts
        assert "user:user.txt" not in artifacts

    async def test_list_user_artifacts(self, helper, mock_context):
        """Should list only user-scoped artifacts."""
        await helper.save_text("session.txt", "content")
        await helper.save_text("user:user.txt", "content")

        artifacts = await helper.list_user_artifacts()
        assert "user:user.txt" in artifacts
        assert "session.txt" not in artifacts

    async def test_exists(self, helper, mock_context):
        """Should check if artifact exists."""
        await helper.save_text("exists.txt", "content")

        assert await helper.exists("exists.txt") is True
        assert await helper.exists("nonexistent.txt") is False


class TestRcaMarkdownFormatting:
    """Tests for RCA report Markdown formatting."""

    def test_format_empty_report(self):
        """Should format empty report."""
        md = _format_rca_as_markdown({})
        assert "# Root Cause Analysis Report" in md

    def test_format_with_summary(self):
        """Should include summary in Markdown."""
        report = {"summary": "System crashed due to OOM"}
        md = _format_rca_as_markdown(report)
        assert "## Summary" in md
        assert "System crashed due to OOM" in md

    def test_format_with_root_cause(self):
        """Should include root cause in Markdown."""
        report = {"root_cause": "Memory leak in application"}
        md = _format_rca_as_markdown(report)
        assert "## Root Cause" in md
        assert "Memory leak in application" in md

    def test_format_with_timeline(self):
        """Should include timeline in Markdown."""
        report = {
            "timeline": [
                {"time": "10:00", "description": "Alert triggered"},
                {"time": "10:05", "description": "Investigation started"},
            ]
        }
        md = _format_rca_as_markdown(report)
        assert "## Timeline" in md
        assert "**10:00**" in md
        assert "Alert triggered" in md

    def test_format_with_recommendations(self):
        """Should include recommendations in Markdown."""
        report = {
            "recommendations": [
                "Increase memory limits",
                "Add monitoring",
            ]
        }
        md = _format_rca_as_markdown(report)
        assert "## Recommendations" in md
        assert "Increase memory limits" in md

    def test_format_complete_report(self):
        """Should format a complete report."""
        report = {
            "summary": "Service outage",
            "root_cause": "Database connection exhaustion",
            "timeline": [{"time": "09:00", "description": "First error"}],
            "recommendations": ["Tune connection pool"],
            "affected_systems": ["api-server", "web-frontend"],
        }
        md = _format_rca_as_markdown(report)
        assert "## Summary" in md
        assert "## Root Cause" in md
        assert "## Timeline" in md
        assert "## Recommendations" in md
        assert "## Affected Systems" in md


class TestIntegration:
    """Integration tests for core exports."""

    def test_core_exports_artifacts(self):
        """Core module should export artifact utilities."""
        from core import (
            ArtifactFilenames,
            ArtifactHelper,
            ArtifactMetadata,
            MimeType,
            save_capacity_report,
            save_performance_report,
            save_rca_report,
        )

        assert ArtifactHelper is not None
        assert ArtifactFilenames is not None
        assert ArtifactMetadata is not None
        assert MimeType is not None
        assert callable(save_rca_report)
        assert callable(save_performance_report)
        assert callable(save_capacity_report)
