# Adding New Specialist Agents

This guide explains how to add a new specialist agent to sysadmin-agents.

## Overview

The foundation makes adding new specialists simple:

1. Create a directory with config.yaml
2. The dispatcher auto-discovers it
3. Your agent is now a tool the dispatcher can use

## ADK Best Practices Used

This project implements Google ADK best practices:

- **Session State**: Agents can remember context via `ToolContext`
- **Safety Guardrails**: Input validation and tool argument checking
- **Multi-Model Support**: Use Gemini, GPT-4, or Claude via LiteLLM
- **output_key**: Auto-save agent responses to session state

## Step-by-Step Guide

### 1. Create the Specialist Directory

```bash
mkdir -p agents/specialists/<agent_name>
```

### 2. Create config.yaml

This file drives all agent configuration:

```yaml
# agents/specialists/<agent_name>/config.yaml

agent:
  name: "<agent_name>_agent"
  # Models: gemini-2.0-flash, openai/gpt-4o, anthropic/claude-sonnet-4-20250514
  model: "gemini-2.0-flash"
  description: |
    Brief description of what this specialist does.

# Thinking configuration for complex reasoning
thinking:
  enabled: true
  budget: 256  # Token budget for thinking (higher = more reasoning)

# Auto-save responses to session state (optional)
output_key: "last_<agent_name>_report"

instruction: |
  You are an expert Linux system administrator specializing in <specialty>.
  
  ## Your Role
  Describe what this agent does.
  
  ## Your Approach
  1. First step...
  2. Second step...
  
  ## Using Session State (ToolContext)
  You can access session state via ToolContext in your tools:
  - `tool_context.state["last_host_investigated"]` - Last host accessed
  - `tool_context.state["investigation_context"]` - Current investigation details
  
  ## Guidelines
  - Always specify the `host` parameter when calling MCP tools
  - Explain your reasoning
  - Be thorough
  
  ## Output Format
  Structure your responses as...

# MCP tools this agent primarily uses
mcp_tools:
  primary:
    - get_system_information
    - get_cpu_information
  secondary:
    - list_processes

# Example queries
examples:
  - "Example query 1 for host server-01"
  - "Example query 2 for host server-02"
```

### 3. Create agent.py (Optional)

For simple agents, just the config.yaml is enough! The foundation will auto-create the agent.

For custom behavior, create an agent.py:

```python
# agents/specialists/<agent_name>/agent.py

from pathlib import Path
from agents.base.agent_template import SpecialistAgent


class MyAgent(SpecialistAgent):
    """Custom specialist agent with additional features."""
    
    def __init__(self):
        config_path = Path(__file__).parent / "config.yaml"
        super().__init__(config_path)
    
    # Override methods for custom behavior if needed


# Create the agent instance
_agent = MyAgent()
my_agent = _agent.agent
```

### 4. Create __init__.py

```python
# agents/specialists/<agent_name>/__init__.py

"""Brief description of this specialist."""

from agents.specialists.<agent_name>.agent import my_agent

__all__ = ["my_agent"]
```

### 5. Test Your Agent

```bash
# Run ADK web
adk web --port 8000

# The dispatcher will auto-discover your agent!
# Test by asking queries that match your specialist's domain
```

## Multi-Model Support

You can use different models for different specialists:

### Google Gemini (Native)
```yaml
agent:
  model: "gemini-2.0-flash"           # Fast, good for most tasks
  model: "gemini-2.0-flash-thinking"  # Better reasoning
  model: "gemini-1.5-pro"             # Larger context
```

### OpenAI (via LiteLLM)
```yaml
agent:
  model: "openai/gpt-4o"       # Best for complex reasoning
  model: "openai/gpt-4o-mini"  # Faster, cheaper
```

### Anthropic (via LiteLLM)
```yaml
agent:
  model: "anthropic/claude-sonnet-4-20250514"  # Great reasoning
  model: "anthropic/claude-opus-4-20250514"    # Highest capability
```

Required environment variables:
```bash
# .env
GOOGLE_API_KEY=your-google-key        # Required for Gemini
OPENAI_API_KEY=your-openai-key        # Required for GPT models
ANTHROPIC_API_KEY=your-anthropic-key  # Required for Claude models
```

## Session State Patterns

Agents can access and modify session state for context-aware interactions.

### Reading State (in tools or callbacks)

```python
from google.adk.tools.tool_context import ToolContext
from core.session import StateKeys

def my_tool(host: str, tool_context: ToolContext) -> dict:
    """Tool that uses session state."""
    
    # Read from state
    last_host = tool_context.state.get(StateKeys.LAST_HOST_INVESTIGATED)
    allowed_hosts = tool_context.state.get(StateKeys.ALLOWED_HOSTS, [])
    
    # Use state in logic
    if allowed_hosts and host not in allowed_hosts:
        return {"error": f"Host {host} not in allowed list"}
    
    # Update state
    tool_context.state[StateKeys.LAST_HOST_INVESTIGATED] = host
    
    return {"result": "..."}
```

### Available State Keys

```python
from core.session import StateKeys

# Investigation context
StateKeys.LAST_HOST_INVESTIGATED    # Last host accessed
StateKeys.CURRENT_INVESTIGATION     # Current investigation details
StateKeys.INVESTIGATION_HISTORY     # List of past investigations

# User preferences
StateKeys.USER_PREFERENCES          # User-specific settings
StateKeys.VERBOSITY_LEVEL           # Output verbosity

# Agent outputs (set via output_key)
StateKeys.LAST_RCA_REPORT           # Last RCA analysis
StateKeys.LAST_PERFORMANCE_REPORT   # Last performance analysis
StateKeys.LAST_SECURITY_REPORT      # Last security audit

# Access control
StateKeys.ALLOWED_HOSTS             # Hosts this session can access
StateKeys.HOST_ACCESS_LOG           # Audit log of host access
```

### Auto-Saving with output_key

Add `output_key` to your config to automatically save the agent's final response:

```yaml
# config.yaml
output_key: "last_my_agent_report"
```

This saves the agent's response to `session.state["last_my_agent_report"]`.

## Safety Guardrails

The dispatcher includes two types of guardrails:

### 1. Input Guardrails (before_model_callback)

Validates user input before it reaches the LLM:

```python
from core.callbacks import create_input_guardrail

# Custom blocked patterns
my_guardrail = create_input_guardrail(
    blocked_patterns=[
        r"\bdrop\s+database",
        r"\btruncate\s+table",
    ],
    sensitive_patterns=[
        r"\bdelete\s+from",
    ]
)
```

### 2. Tool Guardrails (before_tool_callback)

Validates tool arguments before execution:

```python
from core.callbacks import create_tool_guardrail

# Custom tool validation
my_tool_guardrail = create_tool_guardrail(
    host_aware_tools=["get_system_information", "run_command"],
    require_allowed_hosts=True,  # Enforce host access list
)
```

### Environment-Based Guardrails

Guardrails adjust based on environment:

```bash
# .env
ENVIRONMENT=production   # Strict guardrails
ENVIRONMENT=staging      # Moderate guardrails
ENVIRONMENT=development  # Permissive (logging only)
```

## MCP Tools Reference

Your specialist can use these tools from linux-mcp-server:

### System Information
- `get_system_information` - OS, kernel, hostname, uptime
- `get_cpu_information` - CPU details, load averages
- `get_memory_information` - RAM, swap usage
- `get_disk_usage` - Filesystem usage
- `get_hardware_information` - Hardware details

### Services
- `list_services` - All systemd services
- `get_service_status` - Specific service status
- `get_service_logs` - Service logs

### Processes
- `list_processes` - Running processes
- `get_process_info` - Process details

### Logs
- `get_journal_logs` - Systemd journal
- `get_audit_logs` - Audit logs
- `read_log_file` - Specific log files

### Network
- `get_network_interfaces` - Network interfaces
- `get_network_connections` - Active connections
- `get_listening_ports` - Listening ports

### Storage
- `list_block_devices` - Block devices
- `list_directories` - Directory listings

All tools accept optional `host` parameter for remote execution.

## Best Practices

### 1. Clear Purpose
Each specialist should have a focused domain. Don't try to do everything.

### 2. Detailed Instructions
The instruction in config.yaml is crucial. Include:
- Role definition
- Step-by-step approach
- Output format
- Guidelines

### 3. Good Examples
Include example queries to help users understand what to ask.

### 4. Host Parameter
Always remind the agent to use the `host` parameter for MCP tools.

### 5. Use Thinking for Complex Tasks
Enable thinking with appropriate budget:
```yaml
thinking:
  enabled: true
  budget: 256  # Simple tasks
  budget: 512  # Complex analysis (RCA, security audit)
```

### 6. Choose the Right Model
- **Fast tasks**: `gemini-2.0-flash`, `openai/gpt-4o-mini`
- **Complex reasoning**: `openai/gpt-4o`, `anthropic/claude-sonnet-4-20250514`
- **Maximum capability**: `gemini-1.5-pro`, `anthropic/claude-opus-4-20250514`

## Example: Performance Specialist

```yaml
# agents/specialists/performance/config.yaml

agent:
  name: "performance_agent"
  model: "gemini-2.0-flash"
  description: |
    Performance Analysis specialist. Identifies bottlenecks,
    analyzes resource usage, and recommends optimizations.

thinking:
  enabled: true
  budget: 384  # Medium complexity

output_key: "last_performance_report"

instruction: |
  You are an expert Linux performance analyst.
  
  ## Your Role
  Analyze system performance and identify optimization opportunities.
  
  ## Your Approach
  1. Check CPU usage and load averages
  2. Analyze memory usage and swap activity
  3. Review disk I/O and utilization
  4. Identify resource-hungry processes
  5. Look for performance patterns
  
  ## Guidelines
  - Always specify the `host` parameter
  - Compare current metrics to thresholds
  - Identify the top resource consumers
  - Provide specific recommendations
  
  ## Output Format
  ```
  ## Performance Summary
  Current state overview
  
  ## Resource Usage
  - CPU: X%
  - Memory: X%
  - Disk: X%
  
  ## Top Consumers
  Processes using the most resources
  
  ## Bottlenecks
  Identified performance issues
  
  ## Recommendations
  Specific actions to improve performance
  ```

mcp_tools:
  primary:
    - get_cpu_information
    - get_memory_information
    - get_disk_usage
    - list_processes
  secondary:
    - get_process_info
    - get_network_connections

examples:
  - "Why is the server slow? Host: web-prod-01"
  - "What's consuming CPU on db-server-1?"
  - "Check memory usage on worker-node-3"
```

## Contributing Your Specialist

1. Create feature branch: `feature/agent-<name>`
2. Implement specialist following this guide
3. Add tests in `tests/test_<name>_agent.py`
4. Submit pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.
