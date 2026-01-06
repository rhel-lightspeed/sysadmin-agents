"""
Sysadmin Agent - The single entry point for Linux/RHEL system administration.

Users interact with this agent only. It automatically routes to specialists.
"""

from .agent import root_agent, sysadmin_agent

__all__ = ["sysadmin_agent", "root_agent"]
