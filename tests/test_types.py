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
Tests for shared type definitions.

Validates Pydantic models used for structured agent outputs,
following the direct testing pattern from Google ADK samples.
"""

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Test Enums - Direct value testing
# =============================================================================


def test_severity_critical():
    """Severity.CRITICAL should have value 'critical'."""
    from core.types import Severity

    assert Severity.CRITICAL.value == "critical"


def test_severity_high():
    """Severity.HIGH should have value 'high'."""
    from core.types import Severity

    assert Severity.HIGH.value == "high"


def test_severity_medium():
    """Severity.MEDIUM should have value 'medium'."""
    from core.types import Severity

    assert Severity.MEDIUM.value == "medium"


def test_severity_low():
    """Severity.LOW should have value 'low'."""
    from core.types import Severity

    assert Severity.LOW.value == "low"


def test_severity_info():
    """Severity.INFO should have value 'info'."""
    from core.types import Severity

    assert Severity.INFO.value == "info"


def test_safety_rating_safe():
    """SafetyRating.SAFE should have value 'safe'."""
    from core.types import SafetyRating

    assert SafetyRating.SAFE.value == "safe"


def test_safety_rating_moderate():
    """SafetyRating.MODERATE should have value 'moderate'."""
    from core.types import SafetyRating

    assert SafetyRating.MODERATE.value == "moderate"


def test_safety_rating_caution():
    """SafetyRating.CAUTION should have value 'caution'."""
    from core.types import SafetyRating

    assert SafetyRating.CAUTION.value == "caution"


def test_safety_rating_dangerous():
    """SafetyRating.DANGEROUS should have value 'dangerous'."""
    from core.types import SafetyRating

    assert SafetyRating.DANGEROUS.value == "dangerous"


def test_resource_status_healthy():
    """ResourceStatus.HEALTHY should have value 'healthy'."""
    from core.types import ResourceStatus

    assert ResourceStatus.HEALTHY.value == "healthy"


def test_resource_status_warning():
    """ResourceStatus.WARNING should have value 'warning'."""
    from core.types import ResourceStatus

    assert ResourceStatus.WARNING.value == "warning"


def test_resource_status_critical():
    """ResourceStatus.CRITICAL should have value 'critical'."""
    from core.types import ResourceStatus

    assert ResourceStatus.CRITICAL.value == "critical"


# =============================================================================
# Test HostInfo - Direct model testing
# =============================================================================


def test_host_info_minimal():
    """Should create HostInfo with just hostname."""
    from core.types import HostInfo

    host = HostInfo(hostname="server1.example.com")

    assert host.hostname == "server1.example.com"
    assert host.os_type is None
    assert host.os_version is None
    assert host.kernel is None
    assert host.uptime_seconds is None


def test_host_info_full():
    """Should create HostInfo with all fields."""
    from core.types import HostInfo

    host = HostInfo(
        hostname="rhel9.example.com",
        os_type="RHEL",
        os_version="9.2",
        kernel="5.14.0-362.el9.x86_64",
        uptime_seconds=86400,
    )

    assert host.hostname == "rhel9.example.com"
    assert host.os_type == "RHEL"
    assert host.os_version == "9.2"
    assert host.kernel == "5.14.0-362.el9.x86_64"
    assert host.uptime_seconds == 86400


# =============================================================================
# Test TimelineEvent - Direct model testing
# =============================================================================


def test_timeline_event_basic():
    """Should create TimelineEvent with required fields."""
    from core.types import Severity, TimelineEvent

    event = TimelineEvent(
        timestamp=datetime(2025, 1, 5, 14, 32, 0),
        event_type="log",
        source="sshd",
        description="Failed login attempt from 192.168.1.100",
        severity=Severity.HIGH,
    )

    assert event.event_type == "log"
    assert event.source == "sshd"
    assert event.severity == Severity.HIGH
    assert "Failed login" in event.description


def test_timeline_event_default_severity():
    """Should default to INFO severity."""
    from core.types import Severity, TimelineEvent

    event = TimelineEvent(
        timestamp=datetime.now(),
        event_type="metric",
        source="prometheus",
        description="CPU usage at 45%",
    )

    assert event.severity == Severity.INFO


def test_timeline_event_with_raw_data():
    """Should store raw_data when provided."""
    from core.types import TimelineEvent

    raw = {"pid": 1234, "signal": "SIGKILL"}
    event = TimelineEvent(
        timestamp=datetime.now(),
        event_type="process",
        source="kernel",
        description="Process killed",
        raw_data=raw,
    )

    assert event.raw_data == raw
    assert event.raw_data["pid"] == 1234


# =============================================================================
# Test Recommendation - Direct model testing
# =============================================================================


def test_recommendation_basic():
    """Should create Recommendation with required fields."""
    from core.types import Recommendation, SafetyRating, Severity

    rec = Recommendation(
        title="Clear package cache",
        description="Remove old package cache files to free disk space",
        severity=Severity.MEDIUM,
    )

    assert rec.title == "Clear package cache"
    assert rec.severity == Severity.MEDIUM
    assert rec.safety == SafetyRating.SAFE  # Default


def test_recommendation_with_command():
    """Should store command when provided."""
    from core.types import Recommendation, SafetyRating, Severity

    rec = Recommendation(
        title="Clear DNF cache",
        description="Remove DNF package cache",
        severity=Severity.LOW,
        command="dnf clean all",
        safety=SafetyRating.SAFE,
        impact="Frees approximately 500 MB",
    )

    assert rec.command == "dnf clean all"
    assert rec.impact == "Frees approximately 500 MB"


# =============================================================================
# Test RCAReport - Direct model testing
# =============================================================================


def test_rca_report_minimal():
    """Should create minimal RCAReport."""
    from core.types import RCAReport

    report = RCAReport(
        host="webserver01",
        summary="OOM killed nginx worker process",
        root_cause="Memory exhaustion due to traffic spike",
    )

    assert report.host == "webserver01"
    assert report.root_cause == "Memory exhaustion due to traffic spike"
    assert report.timeline == []
    assert report.recommendations == []
    assert report.contributing_factors == []


def test_rca_report_full():
    """Should create full RCAReport with all fields."""
    from core.types import RCAReport, Recommendation, Severity, TimelineEvent

    report = RCAReport(
        host="dbserver01",
        summary="Database connection exhaustion",
        root_cause="Connection pool leak in application",
        contributing_factors=["No connection timeout", "No monitoring alerts"],
        timeline=[
            TimelineEvent(
                timestamp=datetime(2025, 1, 5, 14, 30),
                event_type="log",
                source="postgresql",
                description="Connection count exceeded max_connections",
                severity=Severity.CRITICAL,
            ),
            TimelineEvent(
                timestamp=datetime(2025, 1, 5, 14, 32),
                event_type="log",
                source="application",
                description="Database connection failed",
                severity=Severity.HIGH,
            ),
        ],
        evidence=[
            "PostgreSQL logs show connection limit reached at 14:30",
            "Application logs show 500 errors starting at 14:32",
        ],
        recommendations=[
            Recommendation(
                title="Implement connection pooling",
                description="Use PgBouncer for connection pooling",
                severity=Severity.HIGH,
            )
        ],
    )

    assert len(report.timeline) == 2
    assert len(report.recommendations) == 1
    assert len(report.contributing_factors) == 2
    assert len(report.evidence) == 2


# =============================================================================
# Test PerformanceReport - Direct model testing
# =============================================================================


def test_performance_report():
    """Should create PerformanceReport."""
    from core.types import PerformanceReport, ResourceStatus, ResourceUsage

    report = PerformanceReport(
        host="appserver01",
        summary="System healthy with moderate CPU usage",
        overall_status=ResourceStatus.HEALTHY,
        cpu=ResourceUsage(
            current_value=45.0,
            max_value=100.0,
            percent_used=45.0,
            status=ResourceStatus.HEALTHY,
        ),
        memory=ResourceUsage(
            current_value=12.0,
            max_value=16.0,
            percent_used=75.0,
            status=ResourceStatus.HEALTHY,
        ),
    )

    assert report.host == "appserver01"
    assert report.overall_status == ResourceStatus.HEALTHY
    assert report.cpu.percent_used == 45.0
    assert report.memory.percent_used == 75.0


def test_resource_usage():
    """Should create ResourceUsage with all fields."""
    from core.types import ResourceStatus, ResourceUsage

    usage = ResourceUsage(
        current_value=14.5,
        max_value=16.0,
        percent_used=90.6,
        status=ResourceStatus.WARNING,
        unit="GB",
    )

    assert usage.current_value == 14.5
    assert usage.max_value == 16.0
    assert usage.percent_used == 90.6
    assert usage.status == ResourceStatus.WARNING
    assert usage.unit == "GB"


def test_process_info():
    """Should create ProcessInfo."""
    from core.types import ProcessInfo

    proc = ProcessInfo(
        pid=12345,
        name="python",
        cpu_percent=25.5,
        memory_percent=10.2,
        state="R",
        user="appuser",
        command="python /app/server.py",
    )

    assert proc.pid == 12345
    assert proc.name == "python"
    assert proc.cpu_percent == 25.5
    assert proc.state == "R"
    assert proc.user == "appuser"


# =============================================================================
# Test CapacityReport - Direct model testing
# =============================================================================


def test_capacity_report():
    """Should create CapacityReport."""
    from core.types import (
        CapacityReport,
        CleanupRecommendation,
        FilesystemUsage,
        ResourceStatus,
        SafetyRating,
    )

    report = CapacityReport(
        host="storage01",
        summary="Root filesystem at 85% capacity",
        filesystems=[
            FilesystemUsage(
                mount_point="/",
                device="/dev/sda1",
                filesystem_type="xfs",
                total_bytes=100 * 1024**3,
                used_bytes=85 * 1024**3,
                available_bytes=15 * 1024**3,
                percent_used=85.0,
                status=ResourceStatus.WARNING,
            )
        ],
        cleanup_recommendations=[
            CleanupRecommendation(
                action="Clear package cache",
                path="/var/cache/dnf",
                space_saved_bytes=2 * 1024**3,
                space_saved_human="2 GB",
                safety=SafetyRating.SAFE,
                command="dnf clean all",
            )
        ],
        total_recoverable_safe=2 * 1024**3,
    )

    assert report.host == "storage01"
    assert len(report.filesystems) == 1
    assert report.filesystems[0].percent_used == 85.0
    assert len(report.cleanup_recommendations) == 1
    assert report.total_recoverable_safe == 2 * 1024**3


def test_filesystem_usage():
    """Should create FilesystemUsage."""
    from core.types import FilesystemUsage, ResourceStatus

    fs = FilesystemUsage(
        mount_point="/var/log",
        device="/dev/sdb1",
        filesystem_type="ext4",
        total_bytes=50 * 1024**3,
        used_bytes=45 * 1024**3,
        available_bytes=5 * 1024**3,
        percent_used=90.0,
        status=ResourceStatus.CRITICAL,
    )

    assert fs.mount_point == "/var/log"
    assert fs.device == "/dev/sdb1"
    assert fs.filesystem_type == "ext4"
    assert fs.status == ResourceStatus.CRITICAL


def test_directory_size():
    """Should create DirectorySize."""
    from core.types import DirectorySize

    dir_size = DirectorySize(
        path="/var/log/journal",
        size_bytes=5 * 1024**3,
        size_human="5 GB",
        category="logs",
    )

    assert dir_size.path == "/var/log/journal"
    assert dir_size.size_bytes == 5 * 1024**3
    assert dir_size.size_human == "5 GB"
    assert dir_size.category == "logs"


def test_cleanup_recommendation():
    """Should create CleanupRecommendation."""
    from core.types import CleanupRecommendation, SafetyRating

    rec = CleanupRecommendation(
        action="Prune container images",
        path="/var/lib/containers",
        space_saved_bytes=10 * 1024**3,
        space_saved_human="10 GB",
        safety=SafetyRating.MODERATE,
        command="podman system prune -a",
        notes="Will remove unused images",
    )

    assert rec.action == "Prune container images"
    assert rec.safety == SafetyRating.MODERATE
    assert rec.command == "podman system prune -a"
    assert rec.notes == "Will remove unused images"


# =============================================================================
# Test InvestigationContext - Direct model testing
# =============================================================================

# NOTE: InvestigationContext moved to core.state module
# Tests for it are in test_state.py
