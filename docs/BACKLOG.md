# Project Backlog

This document lists all planned work items. Create these as GitHub Issues when the repository is set up.

## Priority 1: Foundation (Complete)

- [x] `init-project` - Project structure, pyproject.toml, README
- [x] `mcp-integration` - MCP client for linux-mcp-server
- [x] `base-agent` - Agent template with YAML-driven config
- [x] `deploy-openshift` - OpenShift deployment manifests
- [x] `docs` - CONTRIBUTING.md, ADDING_AGENTS.md, DEPLOYMENT.md
- [x] `ci-pipeline` - GitHub Actions for lint, test, validate

## Priority 2: Core Agents

### ✅ [COMPLETED] Performance Analysis Agent

Implemented in `agents/specialists/performance/`

Based on real-world use case: "Why is my system slow?" from Fedora Magazine article.

---

### ✅ [COMPLETED] Capacity Planning Agent  

Implemented in `agents/specialists/capacity/`

Based on real-world use case: "Where'd my disk space go?" from Fedora Magazine article.

---

### Issue: [AGENT] Incident Triage Agent
**Labels:** `agent`, `priority-high`

**Description:**
Create an agent that performs initial assessment and triage of system incidents.

**Responsibilities:**
- Gather initial system state
- Assess incident severity (P1-P4)
- Identify affected services and dependencies
- Recommend immediate actions
- Escalate if necessary

**MCP Tools:**
- get_system_information
- list_services, get_service_status
- get_journal_logs
- get_network_connections

---

### Issue: [AGENT] Security Audit Agent
**Labels:** `agent`, `priority-high`

**Description:**
Create an agent that performs security assessments and compliance checks.

**Responsibilities:**
- Check for security misconfigurations
- Review audit logs for suspicious activity
- Verify service configurations
- Check listening ports and connections
- Assess compliance with security baselines

**MCP Tools:**
- get_audit_logs
- get_listening_ports
- get_network_connections
- list_services
- read_log_file (/var/log/secure)

---

## Priority 3: Additional Agents

### Issue: [AGENT] Log Analysis Agent
**Labels:** `agent`, `priority-medium`

**Description:**
Create an agent that analyzes logs for patterns, anomalies, and insights.

**Responsibilities:**
- Search logs for specific patterns
- Identify error trends
- Correlate events across log sources
- Summarize log activity

**MCP Tools:**
- get_journal_logs
- read_log_file
- get_service_logs

---

### Issue: [AGENT] Capacity Planning Agent
**Labels:** `agent`, `priority-medium`

**Description:**
Create an agent that analyzes resource usage trends for capacity planning.

**Responsibilities:**
- Analyze current resource utilization
- Identify growth trends
- Predict capacity needs
- Recommend scaling actions

**MCP Tools:**
- get_disk_usage
- get_memory_information
- get_cpu_information
- list_block_devices

---

### Issue: [AGENT] Service Health Agent
**Labels:** `agent`, `priority-medium`

**Description:**
Create an agent that monitors and reports on service health status.

**Responsibilities:**
- Check status of critical services
- Analyze service logs for issues
- Verify service dependencies
- Report on service uptime

**MCP Tools:**
- list_services
- get_service_status
- get_service_logs

---

## Priority 4: Good First Issues

### Issue: Add example queries to README
**Labels:** `good first issue`, `documentation`

Add more example queries for each agent type to help users get started.

---

### Issue: Add JSON output formatter utility
**Labels:** `good first issue`, `enhancement`

Create a utility function that formats agent outputs as structured JSON for integration with other tools.

---

### Issue: Add Markdown report generator
**Labels:** `good first issue`, `enhancement`

Create a utility that generates formatted Markdown reports from agent analysis.

---

### Issue: Improve error messages for SSH connection failures
**Labels:** `good first issue`, `enhancement`

Add better error handling and user-friendly messages when SSH connections fail.

---

### Issue: Add host validation before running tools
**Labels:** `good first issue`, `enhancement`

Add validation to ensure the `host` parameter is provided when required.

---

## Priority 5: Infrastructure

### Issue: Add pre-commit hooks
**Labels:** `infrastructure`

Set up pre-commit with ruff, yaml validation, and other checks.

---

### Issue: Add integration tests with mock MCP server
**Labels:** `testing`, `infrastructure`

Create integration tests that mock the MCP server responses.

---

### Issue: Add OpenShift Helm chart
**Labels:** `infrastructure`, `enhancement`

Create a Helm chart as an alternative to Kustomize for deployment.

---

### Issue: Add Prometheus metrics endpoint
**Labels:** `infrastructure`, `enhancement`

Expose metrics for monitoring agent usage and performance.

---

## How to Create Issues

When creating these issues on GitHub:

1. Use the appropriate issue template
2. Add the labels listed
3. Link related issues
4. Add to project board if available

## Contributing

Want to work on one of these? Comment on the issue to claim it!

