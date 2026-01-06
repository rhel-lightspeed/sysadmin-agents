# Sysadmin Agents

Enterprise-grade AI agents for Linux/RHEL system administration, powered by [Google ADK](https://google.github.io/adk-docs/) and [linux-mcp-server](https://github.com/rhel-lightspeed/linux-mcp-server).

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            ADK Web Interface                                  │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         Sysadmin Agent                                  │  │
│  │                     (PlanReActPlanner)                                  │  │
│  │           "Describe your problem, I'll handle everything"               │  │
│  └───────────────────────────────┬────────────────────────────────────────┘  │
│                                  │ auto-routes                               │
│    ┌─────────────────────────────┼─────────────────────────────┐             │
│    ▼                ▼            ▼            ▼                ▼             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │   RCA    │  │  Perf    │  │ Capacity │  │ Upgrade  │                      │
│  │Specialist│  │Specialist│  │Specialist│  │Specialist│                      │
│  │          │  │          │  │          │  │          │                      │
│  │Root Cause│  │Bottleneck│  │Disk Usage│  │ Readiness│                      │
│  │ Analysis │  │  Finder  │  │ Analysis │  │  Check   │                      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       │             │             │             │                            │
│       └─────────────┴─────────────┴─────────────┘                            │
│                           │                                                  │
│              ┌────────────▼────────────┐                                     │
│              │    linux-mcp-server     │                                     │
│              │       (20+ tools)       │                                     │
│              └────────────┬────────────┘                                     │
└───────────────────────────┼──────────────────────────────────────────────────┘
                            │ SSH
                ┌───────────┼───────────┐
                ▼           ▼           ▼
           ┌────────┐  ┌────────┐  ┌────────┐
           │ RHEL 1 │  │ RHEL 2 │  │ RHEL n │
           └────────┘  └────────┘  └────────┘
```

## How It Works

The **Sysadmin Agent** is the single entry point. Users describe their problem naturally, and the agent:

1. **Analyzes** the request to understand what's needed
2. **Routes** to the appropriate specialist(s) automatically
3. **Executes** investigations using linux-mcp-server tools
4. **Synthesizes** findings into actionable recommendations

No need to think about which agent to use - just describe the problem.

## Agents

| Agent | Purpose | Auto-routes to |
|-------|---------|----------------|
| **sysadmin** | Main entry point | Automatically selects specialists |
| **rca** | Root Cause Analysis | Incidents, outages, crash investigation |
| **performance** | Performance Analysis | Slow systems, high CPU/memory |
| **capacity** | Capacity Planning | Disk space, storage analysis |
| **upgrade** | Upgrade Readiness | OS upgrade assessment, pre-flight checks |

## Quick Start

### Prerequisites

- Python 3.10+
- [Gemini API Key](https://aistudio.google.com/apikey)
- SSH key-based access to target RHEL/Linux hosts

### Installation

```bash
git clone https://github.com/your-org/sysadmin-agents.git
cd sysadmin-agents

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

Set environment variables:

```bash
# Required
export GOOGLE_API_KEY=your-gemini-api-key

# SSH access for linux-mcp-server
export LINUX_MCP_USER=your-ssh-username
export LINUX_MCP_SSH_KEY_PATH=~/.ssh/id_ed25519
```

### Run the Agents

```bash
# Start ADK web interface
adk web --port 8000 agents
```

Open http://localhost:8000 and select the **sysadmin** agent.

## Example Queries

Just describe your problem to the sysadmin agent:

```
My server webserver.example.com has been running slow. Can you check it out?
```

```
We had an outage on dbserver.example.com yesterday. Help me understand what happened.
```

```
The disk is almost full on storage.example.com. Find what's using the space.
```

```
Is my Fedora 42 system ready to upgrade to Fedora 43? Check everything.
```

## Use Cases

These agents are designed to address real-world sysadmin scenarios, inspired by the 
[linux-mcp-server Fedora Magazine article](https://fedoramagazine.org/talk-to-your-fedora-system-with-the-linux-mcp-server/).

> **Note**: All examples below were tested against a real RHEL 9.3 system via the ADK API.

### 🐢 "Why is my system so slow?"

**Agent**: `performance_agent`

When your system lags during important moments (video calls, demos), the performance agent:

1. **Gathers resource metrics** - CPU, memory, load averages, swap usage
2. **Identifies top consumers** - Processes sorted by resource usage
3. **Checks for bottlenecks** - CPU-bound, memory pressure, I/O wait, network saturation
4. **Reviews logs** - OOM killer activity, service errors
5. **Provides recommendations** - Immediate fixes and long-term improvements

**Example prompt**:
```
Check system performance on myserver.example.com - analyze CPU, memory, 
and identify any performance bottlenecks.
```

**Tools called** (verified):
- `transfer_to_agent` → `performance_agent`
- `get_system_information` - OS version, kernel, uptime
- `get_cpu_information` - Load averages, CPU model, utilization
- `get_memory_information` - RAM/swap usage
- `get_disk_usage` - Filesystem utilization
- `list_processes` - Top CPU/memory consumers

**Example output**:
```
## Resource Usage
- CPU: 2.8% user, 8.3% system, 88.9% idle. Load average: 0.00, 0.02, 0.00
- Memory: 20.7% used, no swap usage
- Disk: Root partition at 10% utilization

## Bottleneck Identified
No significant performance bottlenecks. CPU, memory, and disk I/O are within 
acceptable ranges.

## Recommendations
1. Monitor regularly for early issue detection
2. Optimize rhcd process if CPU usage increases
3. Review SSH configuration for security
```

---

### 💾 "Where did my disk space go?"

**Agent**: `capacity_agent`

When your disk fills up mysteriously, the capacity agent:

1. **Analyzes all filesystems** - Identifies which are running low
2. **Finds largest directories** - Recursive deep-dive, not just top-level
3. **Categorizes space usage** - Containers, caches, logs, trash
4. **Provides cleanup commands** - With safety ratings (SAFE/MODERATE/CAUTION/DANGEROUS)
5. **Calculates recoverable space** - Shows what you can safely delete

**Example prompt**:
```
Analyze disk usage on myserver.example.com. Find the largest directories 
and identify cleanup opportunities with safety assessments.
```

**Tools called** (verified):
- `transfer_to_agent` → `capacity_agent`
- `get_disk_usage` - All mounted filesystems
- `list_directories` (recursive) - /, /usr, /var, /var/cache
- `list_files` - Log files in /var/log
- `get_journal_logs` - Disk-related warnings
- `list_block_devices` - Physical storage layout

**Example output**:
```
## Disk Usage Overview
| Filesystem | Size | Used | Available | Use% |
|------------|------|------|-----------|------|
| /dev/nvme0n1p4 | 30G | 2.8G | 27G | 10% |

## Largest Space Consumers
| Path | Size | Category |
|------|------|----------|
| /var/cache/dnf | 346 MB | Package Cache |
| /var/log/messages | 5.4 MB | Logs |

## Cleanup Recommendations
| Action | Space Saved | Safety | Command |
|--------|-------------|--------|---------|
| Clean DNF Cache | ~346 MB | SAFE | `dnf clean packages` |

## Total Recoverable Space: ~346 MB
```

---

### 🔍 "What caused the outage?"

**Agent**: `rca_agent`

When investigating incidents and crashes, the RCA agent:

1. **Gathers system context** - Uptime, recent reboots, load
2. **Collects evidence** - Logs, service status, resource metrics
3. **Builds timeline** - Chronological sequence of events
4. **Correlates events** - Connects related issues across log sources
5. **Identifies root cause** - Distinguishes primary cause from symptoms
6. **Provides remediation** - Immediate fixes and prevention measures

**Example prompt**:
```
Investigate any recent issues or errors on myserver.example.com. 
Check system logs and services for problems.
```

**Tools called** (verified):
- `transfer_to_agent` → `rca_agent`
- `get_system_information` - Uptime, OS version
- `get_journal_logs` (priority=warning, 200 lines) - System warnings/errors
- `get_service_status` (rhcd) - Problem service status
- `get_audit_logs` - SELinux denials (requires root)

**Example output**:
```
## Root Cause
SELinux policy preventing /usr/sbin/rhcd from establishing outbound connections 
on TCP port 443.

## Evidence
- Kernel: Speculative Return Stack Overflow warnings
- SELinux: Repeated denials for rhcd → port 443
- SSH: kex_exchange_identification errors (possible intrusion attempts)
- rhcd service: "connection lost unexpectedly: pingresp not received"

## Recommendations
1. Use `sealert -l <alert_id>` to analyze SELinux denials
2. Create custom SELinux policy module for rhcd
3. Review SSH logs in /var/log/secure
4. Consider fail2ban for brute-force protection
```

---

### ⬆️ "Am I ready to upgrade?"

**Agent**: `upgrade_agent`

Before major OS upgrades (Fedora 42→43, RHEL 9.4→9.5), the upgrade agent:

1. **Identifies current system** - OS version, kernel, architecture
2. **Checks disk space** - Minimum requirements for root, /boot, /var
3. **Reviews system health** - Memory, CPU, running processes
4. **Checks critical services** - NetworkManager, sshd, databases
5. **Scans logs for issues** - Pre-existing problems to fix first
6. **Provides manual checks** - Commands for package health, third-party repos

**Example prompt**:
```
Check if myserver.example.com is ready for an OS upgrade. 
Assess disk space, system health, and identify any blockers.
```

**Tools called** (verified):
- `transfer_to_agent` → `upgrade_agent`
- `get_system_information` - Current OS version
- `get_disk_usage` - Space for upgrade
- `get_memory_information` - RAM availability
- `get_cpu_information` - CPU resources
- `list_processes` - Running processes
- `get_service_status` (NetworkManager, sshd) - Critical services
- `get_journal_logs` (priority=error) - Pre-existing errors
- `get_network_interfaces` - Network configuration
- `list_block_devices` - Storage layout

**Example output**:
```
# Upgrade Readiness Report

## System Identification
- Distribution: Red Hat Enterprise Linux 9.3 (Plow)
- Kernel: 5.14.0-362.18.1.el9_3.x86_64
- Target Upgrade: RHEL 9.y (latest)

## Pre-flight Checks
| Filesystem | Size | Used | Available | Status |
|------------|------|------|-----------|--------|
| / | 30G | 2.8G | 27G | ✅ Ready |
| /boot | 536M | 162M | 375M | ⚠️ Warning |
| /boot/efi | 200M | 7.0M | 193M | ❌ Blocking |

## Potential Issues Found
| Issue | Severity | Recommendation |
|-------|----------|----------------|
| /boot/efi low space | HIGH | Free up space before upgrade |
| setroubleshoot high CPU | MEDIUM | Resolve SELinux issues first |

## Overall Readiness: NOT READY ❌
```

**Manual verification commands provided**:
```bash
sudo dnf check           # Package dependency issues
dnf repolist            # Third-party repos to verify
sestatus                # SELinux status
cat /etc/os-release     # Exact OS version
```

---

### 🏥 "Give me a complete health check"

**Agent**: `sysadmin` (orchestrator)

For comprehensive system assessment, the orchestrator uses multiple specialists:

**Example prompt**:
```
Run a complete health check on myserver.example.com - check performance, 
disk space, any issues in logs, and whether it's ready for the next OS upgrade.
```

**Routing behavior** (verified):
1. **sysadmin** → Routes to `performance_agent` for resource analysis
2. **performance_agent** → Completes, routes to `capacity_agent`
3. **capacity_agent** → Completes, routes to `rca_agent` 
4. **rca_agent** → Completes, routes back to `sysadmin`
5. **sysadmin** → Synthesizes all findings

The orchestrator correctly chains specialist agents based on the multi-faceted request.

---

## API Testing with curl

You can test agents directly via the ADK REST API:

### 1. Create a session

```bash
SESSION_ID=$(curl -s -X POST http://127.0.0.1:8000/apps/sysadmin/users/user/sessions \
  -H "Content-Type: application/json" | jq -r '.id')
echo "Session ID: $SESSION_ID"
```

### 2. Send a query via SSE

```bash
curl -s -X POST http://127.0.0.1:8000/run_sse \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "sysadmin",
    "user_id": "user", 
    "session_id": "'"$SESSION_ID"'",
    "new_message": {
      "role": "user",
      "parts": [{"text": "Check system performance on myserver.example.com"}]
    }
  }' --no-buffer
```

The response is a Server-Sent Events stream with JSON payloads containing:
- `functionCall` - MCP tool invocations
- `functionResponse` - Tool results  
- `text` - Agent analysis and recommendations

## Project Structure

```
sysadmin-agents/
├── agents/
│   ├── sysadmin/              # Main orchestrator agent
│   │   ├── agent.py           # Routes to specialists
│   │   └── root_agent.yaml    # ADK Agent Config
│   ├── rca/                   # Root Cause Analysis
│   │   ├── agent.py           # Agent loader
│   │   └── root_agent.yaml    # Instructions & prompts
│   ├── performance/           # Performance Analysis
│   │   ├── agent.py
│   │   └── root_agent.yaml
│   ├── capacity/              # Capacity Planning
│   │   ├── agent.py
│   │   └── root_agent.yaml
│   └── upgrade/               # Upgrade Readiness
│       ├── agent.py
│       └── root_agent.yaml
├── core/                      # Shared infrastructure
│   ├── config.py              # Pydantic settings
│   ├── mcp.py                 # MCP connection utilities
│   ├── callbacks.py           # ADK callbacks (rate limiting, validation)
│   ├── safety.py              # Gemini-as-a-Judge safety screening
│   ├── events.py              # Event processing utilities
│   ├── state.py               # Session state management
│   └── agent_loader.py        # YAML config loader
├── deploy/                    # OpenShift manifests
├── scripts/                   # Test and utility scripts
├── docs/                      # Documentation
└── tests/                     # Tests
```

## MCP Tools Available

Each agent has access to these linux-mcp-server tools:

| Category | Tools |
|----------|-------|
| **System** | get_system_information, get_uptime, get_cpu_info |
| **Memory** | get_memory_information |
| **Disk** | get_disk_usage, get_block_devices, list_directory |
| **Processes** | list_processes, get_process_info |
| **Services** | list_services, get_service_status, get_service_logs |
| **Logs** | get_journal_logs, read_file |
| **Network** | get_network_interfaces, get_network_connections |

## Adding New Agents

This project uses [ADK Agent Config](https://google.github.io/adk-docs/agents/config/) patterns 
with a hybrid approach for MCP tools (see [Known Limitations](#mcp-tools-note)).

1. Create directory: `agents/<name>/`

2. Add `__init__.py`:

```python
"""My Specialist Agent."""
from .agent import my_agent, root_agent

__all__ = ["my_agent", "root_agent"]
```

3. Add `root_agent.yaml` for instructions and configuration:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/google/adk-python/refs/heads/main/src/google/adk/agents/config_schemas/AgentConfig.json
name: my_agent
model: gemini-2.0-flash
description: |
  What this agent does (used for routing decisions).

output_key: last_my_report  # Persists output to session state

generate_content_config:
  temperature: 0.1

instruction: |
  Detailed instructions for the LLM.
  
  ## Your Approach
  ...

# NOTE: MCP tools are added programmatically in agent.py
# This avoids serialization issues with McpToolset in ADK Agent Config
```

4. Add `agent.py` using `create_agent_with_mcp`:

```python
import logging
from pathlib import Path
from core.agent_loader import create_agent_with_mcp

logger = logging.getLogger(__name__)
CONFIG_PATH = Path(__file__).parent / "root_agent.yaml"

# Creates agent from YAML config with MCP tools added programmatically
my_agent = create_agent_with_mcp(CONFIG_PATH)
logger.info(f"My agent created: {my_agent.name}")

# Alias for ADK web discovery
root_agent = my_agent
```

5. To add as a sub-agent to the orchestrator, import it in `agents/sysadmin/agent.py`:

```python
from agents.my_agent.agent import my_agent
# Then add to sub_agents list
```

6. Restart ADK web - your agent appears automatically!

### MCP Tools Note

McpToolset is [listed but "not fully supported"](https://google.github.io/adk-docs/agents/config/) 
in ADK Agent Config YAML, causing serialization errors in the web UI. This project uses 
`create_agent_with_mcp()` as a workaround that:

- Uses **YAML for instructions/config** (Agent Config pattern)
- Creates agents **programmatically with MCP tools** (avoids serialization issues)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check .
ruff format .

# Run tests
pytest tests/ -v
```

## OpenShift Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment instructions.

## Contributing

We welcome contributions! See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

Check [docs/BACKLOG.md](docs/BACKLOG.md) for planned features.

## License

Apache-2.0
