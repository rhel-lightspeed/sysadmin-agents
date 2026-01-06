"""
Shared type definitions for sysadmin-agents.

Provides Pydantic models for domain entities used across agents,
enabling structured outputs and session state persistence.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Severity and Status Enums
# =============================================================================


class Severity(str, Enum):
    """Severity levels for issues and recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SafetyRating(str, Enum):
    """Safety ratings for cleanup recommendations."""

    SAFE = "safe"
    MODERATE = "moderate"
    CAUTION = "caution"
    DANGEROUS = "dangerous"


class ResourceStatus(str, Enum):
    """Status levels for resource usage."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


# =============================================================================
# Common Types
# =============================================================================


class HostInfo(BaseModel):
    """Information about a target host."""

    hostname: str = Field(..., description="Hostname or IP address")
    os_type: str | None = Field(None, description="Operating system type (e.g., RHEL, Fedora)")
    os_version: str | None = Field(None, description="Operating system version")
    kernel: str | None = Field(None, description="Kernel version")
    uptime_seconds: int | None = Field(None, description="System uptime in seconds")


class TimelineEvent(BaseModel):
    """An event in an investigation timeline."""

    timestamp: datetime = Field(..., description="When the event occurred")
    event_type: str = Field(..., description="Type of event (log, metric, action)")
    source: str = Field(..., description="Source of the event (service, file, tool)")
    description: str = Field(..., description="Human-readable description")
    severity: Severity = Field(default=Severity.INFO, description="Event severity")
    raw_data: dict[str, Any] | None = Field(None, description="Raw data if available")


class Recommendation(BaseModel):
    """A recommendation for addressing an issue."""

    title: str = Field(..., description="Short title of the recommendation")
    description: str = Field(..., description="Detailed description")
    severity: Severity = Field(..., description="Priority/severity of this recommendation")
    command: str | None = Field(None, description="Command to execute (if applicable)")
    safety: SafetyRating = Field(default=SafetyRating.SAFE, description="Safety rating")
    impact: str | None = Field(None, description="Expected impact of this action")


# =============================================================================
# RCA Report Types
# =============================================================================


class RCAReport(BaseModel):
    """Root Cause Analysis report."""

    host: str = Field(..., description="Target host analyzed")
    summary: str = Field(..., description="Brief summary of the issue and root cause")
    root_cause: str = Field(..., description="Identified root cause")
    contributing_factors: list[str] = Field(default_factory=list, description="Secondary factors")
    timeline: list[TimelineEvent] = Field(default_factory=list, description="Chronological events")
    evidence: list[str] = Field(default_factory=list, description="Key findings from logs/metrics")
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="Recommended actions"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.now, description="When analysis was performed"
    )


# =============================================================================
# Performance Report Types
# =============================================================================


class ResourceUsage(BaseModel):
    """Resource usage metrics."""

    current_value: float = Field(..., description="Current usage value")
    max_value: float | None = Field(None, description="Maximum/total available")
    percent_used: float = Field(..., description="Percentage used (0-100)")
    status: ResourceStatus = Field(..., description="Health status")
    unit: str = Field(default="%", description="Unit of measurement")


class ProcessInfo(BaseModel):
    """Information about a running process."""

    pid: int = Field(..., description="Process ID")
    name: str = Field(..., description="Process name")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    state: str = Field(..., description="Process state (R, S, D, etc.)")
    user: str | None = Field(None, description="User running the process")
    command: str | None = Field(None, description="Full command line")


class PerformanceReport(BaseModel):
    """Performance Analysis report."""

    host: str = Field(..., description="Target host analyzed")
    summary: str = Field(..., description="Quick overview of system health")
    overall_status: ResourceStatus = Field(..., description="Overall health status")
    cpu: ResourceUsage = Field(..., description="CPU usage")
    memory: ResourceUsage = Field(..., description="Memory usage")
    swap: ResourceUsage | None = Field(None, description="Swap usage")
    load_average: tuple[float, float, float] | None = Field(
        None, description="Load average (1, 5, 15 min)"
    )
    bottleneck: str | None = Field(None, description="Identified bottleneck")
    top_processes: list[ProcessInfo] = Field(
        default_factory=list, description="Top resource consumers"
    )
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="Optimization recommendations"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.now, description="When analysis was performed"
    )


# =============================================================================
# Capacity Report Types
# =============================================================================


class FilesystemUsage(BaseModel):
    """Filesystem usage information."""

    mount_point: str = Field(..., description="Mount point path")
    device: str = Field(..., description="Device name")
    filesystem_type: str | None = Field(None, description="Filesystem type (ext4, xfs)")
    total_bytes: int = Field(..., description="Total size in bytes")
    used_bytes: int = Field(..., description="Used space in bytes")
    available_bytes: int = Field(..., description="Available space in bytes")
    percent_used: float = Field(..., description="Percentage used (0-100)")
    status: ResourceStatus = Field(..., description="Health status")


class DirectorySize(BaseModel):
    """Directory size information."""

    path: str = Field(..., description="Directory path")
    size_bytes: int = Field(..., description="Size in bytes")
    size_human: str = Field(..., description="Human-readable size (e.g., '2.5 GB')")
    category: str | None = Field(None, description="Category (logs, cache, containers)")


class CleanupRecommendation(BaseModel):
    """A cleanup action recommendation."""

    action: str = Field(..., description="What to clean up")
    path: str = Field(..., description="Target path")
    space_saved_bytes: int = Field(..., description="Estimated space savings")
    space_saved_human: str = Field(..., description="Human-readable savings")
    safety: SafetyRating = Field(..., description="Safety rating")
    command: str | None = Field(None, description="Cleanup command")
    notes: str | None = Field(None, description="Additional notes")


class CapacityReport(BaseModel):
    """Capacity and Disk Analysis report."""

    host: str = Field(..., description="Target host analyzed")
    summary: str = Field(..., description="Quick overview of disk status")
    filesystems: list[FilesystemUsage] = Field(default_factory=list, description="Filesystem usage")
    largest_directories: list[DirectorySize] = Field(
        default_factory=list, description="Largest directories"
    )
    cleanup_recommendations: list[CleanupRecommendation] = Field(
        default_factory=list, description="Cleanup recommendations"
    )
    total_recoverable_safe: int = Field(default=0, description="Safe to delete (bytes)")
    total_recoverable_caution: int = Field(default=0, description="Delete with caution (bytes)")
    analyzed_at: datetime = Field(
        default_factory=datetime.now, description="When analysis was performed"
    )


# =============================================================================
# Investigation Context Types
# =============================================================================

# NOTE: InvestigationContext is defined in core.state with helper methods.
# Import from there: from core.state import InvestigationContext
