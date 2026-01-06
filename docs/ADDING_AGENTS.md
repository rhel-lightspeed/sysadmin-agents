# Adding New Specialist Agents

This guide explains how to add a new specialist agent to sysadmin-agents.

## Overview

Adding a new agent involves creating three files in the `agents/` directory:

1. `root_agent.yaml` - Agent configuration and instructions
2. `agent.py` - Python module that creates the agent
3. `__init__.py` - Package exports

The orchestrator (`sysadmin` agent) can then route to your new specialist.

## Project Structure

Agents live directly in the `agents/` directory (not in a `specialists/` subdirectory):

```
agents/
├── sysadmin/           # Main orchestrator
├── rca/                # Root Cause Analysis specialist
├── performance/        # Performance Analysis specialist
├── capacity/           # Capacity Planning specialist
├── upgrade/            # Upgrade Readiness specialist
├── security/           # Security Audit specialist
└── your_agent/         # Your new agent goes here!
    ├── __init__.py
    ├── agent.py
    └── root_agent.yaml
```

## Step-by-Step Guide

### 1. Create the Agent Directory

```bash
mkdir -p agents/my_agent
```

### 2. Create `root_agent.yaml`

This file defines your agent's configuration and instructions using the [ADK Agent Config](https://google.github.io/adk-docs/agents/config/) format:

```yaml
# agents/my_agent/root_agent.yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/google/adk-python/refs/heads/main/src/google/adk/agents/config_schemas/AgentConfig.json

agent_class: LlmAgent
name: my_agent
model: gemini-2.0-flash
description: |
  Brief description of what this specialist does.
  This is used by the orchestrator for routing decisions.

# Auto-save the agent's response to session state (optional)
output_key: last_my_agent_report

# Generation config for more deterministic outputs
generate_content_config:
  temperature: 0.1

instruction: |
  You are an expert Linux/RHEL system administrator specializing in <YOUR SPECIALTY>.
  
  ## Your Role
  Describe what this agent does and when it should be used.
  
  ## Your Approach
  1. First step in your investigation...
  2. Second step...
  3. Third step...
  
  ## Important Guidelines
  1. **Always specify the `host` parameter** when calling MCP tools
  2. Be thorough in your analysis
  3. Provide actionable recommendations
  
  ## Output Format
  Structure your responses as:
  
  ```
  ## Summary
  Quick overview of findings
  
  ## Analysis
  Detailed findings
  
  ## Recommendations
  1. Action item 1
  2. Action item 2
  ```

# NOTE: MCP tools are added programmatically in agent.py
# This avoids serialization issues with McpToolset in ADK Agent Config
```

### 3. Create `agent.py`

This file creates the agent using `create_agent_with_mcp()`:

```python
# agents/my_agent/agent.py

"""
My Specialist Agent.

Brief description of what this agent does.
"""

import logging
from pathlib import Path

from core.agent_loader import create_agent_with_mcp

logger = logging.getLogger(__name__)

# Path to the configuration file
CONFIG_PATH = Path(__file__).parent / "root_agent.yaml"

# Create the agent with MCP tools
# - use_planner=True: Enables PlanReActPlanner for structured reasoning
#   (recommended for agents that execute tools and produce analysis)
root_agent = create_agent_with_mcp(CONFIG_PATH, use_planner=True)

# Alias for convenience
my_agent = root_agent

logger.info(f"My agent created: {root_agent.name}")
```

### 4. Create `__init__.py`

```python
# agents/my_agent/__init__.py

"""My Specialist Agent."""

from .agent import my_agent, root_agent

__all__ = ["my_agent", "root_agent"]
```

### 5. Add to the Orchestrator (Optional)

If you want the main `sysadmin` agent to route to your new specialist:

1. Edit `agents/sysadmin/agent.py` to create your sub-agent:

```python
# Add import and create sub-agent
my_sub = create_agent_with_mcp(
    agents_dir / "my_agent" / "root_agent.yaml",
    use_planner=True,
    disallow_transfer_to_peers=True,  # Only orchestrator routes
)

# Add to sub_agents list in the orchestrator
sub_agents=[rca_sub, performance_sub, capacity_sub, upgrade_sub, security_sub, my_sub],
```

2. Update `agents/sysadmin/root_agent.yaml` to include routing instructions for your agent.

### 6. Test Your Agent

```bash
# Start ADK web
adk web --port 8000 agents

# Your agent should appear in the dropdown
# Test queries that match your specialist's domain
```

## Key Function: `create_agent_with_mcp()`

This function from `core/agent_loader.py` handles the complexity of:

- Loading configuration from YAML
- Adding MCP tools from `linux-mcp-server`
- Optionally enabling `PlanReActPlanner`
- Applying callbacks for safety and state management

```python
def create_agent_with_mcp(
    config_path: Path,
    use_planner: bool = False,        # Enable PlanReActPlanner
    disallow_transfer_to_peers: bool = False,  # For sub-agents
) -> LlmAgent:
```

## MCP Tools Available

Your agent has access to these tools from `linux-mcp-server`:

| Category | Tools |
|----------|-------|
| **System** | `get_system_information`, `get_cpu_information`, `get_memory_information`, `get_hardware_information` |
| **Storage** | `get_disk_usage`, `list_block_devices`, `list_directories` |
| **Processes** | `list_processes`, `get_process_info` |
| **Services** | `list_services`, `get_service_status`, `get_service_logs` |
| **Logs** | `get_journal_logs`, `get_audit_logs`, `read_log_file`, `read_file` |
| **Network** | `get_network_interfaces`, `get_network_connections`, `get_listening_ports` |

All tools accept an optional `host` parameter for remote execution via SSH.

## Multi-Model Support

You can use different models in your `root_agent.yaml`:

```yaml
# Google Gemini (default)
model: gemini-2.0-flash

# OpenAI (via LiteLLM, requires OPENAI_API_KEY)
model: openai/gpt-4o

# Anthropic (via LiteLLM, requires ANTHROPIC_API_KEY)
model: anthropic/claude-sonnet-4-20250514
```

## Best Practices

1. **Clear Purpose**: Each specialist should have a focused domain
2. **Detailed Instructions**: The `instruction` field is crucial - include role, approach, and output format
3. **Host Parameter**: Always remind the agent to specify `host` for MCP tools
4. **Use Planner**: Set `use_planner=True` for agents that execute tools
5. **Output Key**: Use `output_key` to save results to session state

## Example: Real Performance Agent

See the actual implementation at `agents/performance/` for a complete example:

- [`agents/performance/root_agent.yaml`](../agents/performance/root_agent.yaml) - Full instruction set with thresholds, patterns, and output format
- [`agents/performance/agent.py`](../agents/performance/agent.py) - Simple agent creation

## Contributing

1. Create feature branch: `feature/agent-<name>`
2. Implement agent following this guide
3. Add tests in `tests/test_<name>_agent.py`
4. Submit pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.
