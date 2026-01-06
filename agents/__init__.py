"""
Sysadmin Agents - Specialist agents for Linux/RHEL system administration.

This package provides focused specialist agents:

- **rca**: Root Cause Analysis - diagnoses system issues by correlating logs and events
- **performance**: Performance Analysis - identifies bottlenecks and resource issues
- **capacity**: Capacity Analysis - analyzes disk usage and storage planning
- **upgrade**: Upgrade Readiness - analyzes system readiness for OS upgrades
- **security**: Security Audit - analyzes security posture, login attempts, and audit logs
- **sysadmin**: Orchestrator - routes to specialists based on problem type

Each agent connects to linux-mcp-server for remote system access.
"""

# ADK pattern: export root_agent from the main sysadmin orchestrator
from .sysadmin.agent import root_agent

__all__ = ["root_agent"]
