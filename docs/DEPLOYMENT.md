# Deployment Guide

This guide covers deploying Sysadmin Agents to OpenShift.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  OpenShift Cluster                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              sysadmin-agents Pod                        ││
│  │                                                          ││
│  │  ┌────────────────────────────────────────────────────┐ ││
│  │  │           ADK Web Server (Port 8000)               │ ││
│  │  │                                                     │ ││
│  │  │  Dispatcher → Specialists → linux-mcp-server       │ ││
│  │  └────────────────────────────────────────────────────┘ ││
│  │                          │                               ││
│  │                          │ SSH                           ││
│  └──────────────────────────┼──────────────────────────────┘│
│                             │                                │
└─────────────────────────────┼────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         ┌────────┐      ┌────────┐      ┌────────┐
         │ RHEL 1 │      │ RHEL 2 │      │ RHEL n │
         └────────┘      └────────┘      └────────┘
```

## Prerequisites

- OpenShift cluster access
- `oc` CLI installed
- Gemini API key
- SSH key for remote RHEL hosts

## Quick Start

```bash
# Login to OpenShift
oc login https://api.your-cluster.example.com:6443

# Deploy
./scripts/deploy.sh adk-web
```

## Manual Setup

### 1. Create Namespace

```bash
oc create namespace adk-web
```

### 2. Create Secrets

**Gemini API Key:**
```bash
oc create secret generic gemini-api-key \
  --from-literal=GOOGLE_API_KEY='your-gemini-api-key' \
  -n adk-web
```

**SSH Private Key:**
```bash
oc create secret generic ssh-private-key \
  --from-file=id_ed25519=~/.ssh/id_ed25519 \
  -n adk-web
```

**SSH Username (Optional):**
```bash
oc create secret generic ssh-credentials \
  --from-literal=username='your-ssh-username' \
  -n adk-web
```

### 3. Deploy

```bash
# Sync agent code to ConfigMap
./scripts/sync-agents.sh adk-web

# Apply manifests
oc apply -f deploy/deployment.yaml -n adk-web
oc apply -f deploy/service.yaml -n adk-web
oc apply -f deploy/route.yaml -n adk-web
```

### 4. Verify

```bash
# Check pod status
oc get pods -n adk-web

# Get route URL
oc get route sysadmin-agents -n adk-web
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Gemini API key | Yes |
| `LINUX_MCP_SSH_KEY_PATH` | Path to SSH key | Yes |
| `LINUX_MCP_USER` | SSH username | No |
| `DEFAULT_MODEL` | LLM model | No |
| `THINKING_BUDGET` | Reasoning tokens | No |

### ConfigMap Structure

The agent code is deployed via ConfigMap:

```
sysadmin-agents-code/
├── agents/__init__.py
├── agents/dispatcher/...
├── agents/base/...
├── agents/specialists/rca/...
└── core/...
```

## Updating Agents

```bash
# Sync changes
./scripts/sync-agents.sh adk-web

# Restart to pick up changes
oc rollout restart deployment/sysadmin-agents -n adk-web
```

## Scaling

```bash
# Scale replicas
oc scale deployment/sysadmin-agents --replicas=3 -n adk-web
```

## Troubleshooting

### Pod Not Starting

```bash
oc describe pod -l app=sysadmin-agents -n adk-web
```

Common issues:
- Missing secrets
- Image pull errors
- Resource quota

### Agent Errors

```bash
oc logs -f deployment/sysadmin-agents -n adk-web
```

### SSH Connection Issues

- Verify SSH key is mounted correctly
- Check SSH key permissions (0400)
- Test network connectivity to target hosts
