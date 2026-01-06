"""
Sysadmin Agents - Specialist agents for Linux/RHEL system administration.

This package provides three focused specialist agents:

- **rca**: Root Cause Analysis - diagnoses system issues by correlating logs and events
- **performance**: Performance Analysis - identifies bottlenecks and resource issues
- **capacity**: Capacity Analysis - analyzes disk usage and storage planning

Each agent connects directly to linux-mcp-server for remote system access.
"""

# For ADK discovery, export root_agent from the main sysadmin orchestrator
from .sysadmin.agent import root_agent

__all__ = ["root_agent"]
