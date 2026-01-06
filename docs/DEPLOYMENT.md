# Deployment Guide

This guide covers deploying Sysadmin Agents using the pre-built container image.

## Architecture

```mermaid
flowchart TB
    subgraph Cluster [OpenShift/Kubernetes Cluster]
        subgraph Pod [sysadmin-agents Pod]
            subgraph Container [Container]
                FastAPI[FastAPI - ADK API + Web UI]
                MCP[linux-mcp-server - 19 tools]
                FastAPI <-->|stdio| MCP
            end
        end
        
        subgraph Config [Configuration]
            ConfigMap[ConfigMap - .env file]
            Secret1[Secret - GOOGLE_API_KEY]
            Secret2[Secret - SSH Key]
        end
        
        ConfigMap -->|mount| Container
        Secret1 -->|env| Container
        Secret2 -->|mount| Container
    end
    
    subgraph Targets [Target Systems]
        RHEL1[RHEL Server 1]
        RHEL2[RHEL Server 2]
        RHELn[RHEL Server n]
    end
    
    MCP -->|SSH| RHEL1
    MCP -->|SSH| RHEL2
    MCP -->|SSH| RHELn
```

<details>
<summary><strong>View ASCII diagram</strong> (for terminals without Mermaid support)</summary>

```
┌─────────────────────────────────────────────────────────────────────┐
│                      OpenShift/Kubernetes                           │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  sysadmin-agents Pod                          │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  Container                                              │  │  │
│  │  │  ┌────────────────┐   stdio   ┌───────────────────────┐ │  │  │
│  │  │  │ FastAPI        │◄─────────►│ linux-mcp-server      │ │  │  │
│  │  │  └────────────────┘           └───────────┬───────────┘ │  │  │
│  │  └──────────────────────────────────────────┼──────────────┘  │  │
│  └──────────────────────────────────────────────┼────────────────┘  │
│  ConfigMap ─► /opt/app-root/config/.env         │ SSH              │
│  Secret ────► GOOGLE_API_KEY, SSH Key           │                  │
└─────────────────────────────────────────────────┼──────────────────┘
                              ┌───────────────────┼───────────────────┐
                              ▼                   ▼                   ▼
                         ┌────────┐          ┌────────┐          ┌────────┐
                         │ RHEL 1 │          │ RHEL 2 │          │ RHEL n │
                         └────────┘          └────────┘          └────────┘
```

</details>

## Prerequisites

- OpenShift cluster or Kubernetes cluster
- `oc` or `kubectl` CLI installed
- [Gemini API key](https://aistudio.google.com/apikey)
- SSH key for remote RHEL hosts

## Deployment Options

### Option 1: Quick Deploy with Script

```bash
# Login to OpenShift
oc login https://api.your-cluster.example.com:6443

# Create namespace and secrets
oc create namespace sysadmin-agents
oc create secret generic gemini-api-key \
  --from-literal=GOOGLE_API_KEY='your-gemini-api-key' \
  -n sysadmin-agents
oc create secret generic ssh-private-key \
  --from-file=id_ed25519=~/.ssh/id_ed25519 \
  -n sysadmin-agents

# Deploy using script
./scripts/deploy.sh sysadmin-agents ghcr.io/your-org/sysadmin-agents:latest
```

### Option 2: Manual Deployment

#### 1. Create Namespace

```bash
oc apply -f deploy/namespace.yaml
# Or: oc create namespace sysadmin-agents
```

#### 2. Create Secrets

**Gemini API Key (Required):**
```bash
oc create secret generic gemini-api-key \
  --from-literal=GOOGLE_API_KEY='your-gemini-api-key' \
  -n sysadmin-agents
```

**SSH Private Key (Required for MCP):**
```bash
oc create secret generic ssh-private-key \
  --from-file=id_ed25519=~/.ssh/id_ed25519 \
  -n sysadmin-agents
```

**SSH Credentials (Optional):**
```bash
oc create secret generic ssh-credentials \
  --from-literal=username='your-ssh-username' \
  -n sysadmin-agents
```

#### 3. Apply ConfigMap

Edit `deploy/configmap.yaml` with your settings, then:

```bash
oc apply -f deploy/configmap.yaml -n sysadmin-agents
```

#### 4. Deploy Application

```bash
# Update image in deployment.yaml or use sed
oc apply -f deploy/deployment.yaml -n sysadmin-agents
oc apply -f deploy/service.yaml -n sysadmin-agents
oc apply -f deploy/route.yaml -n sysadmin-agents
```

Or use Kustomize:
```bash
oc apply -k deploy/ -n sysadmin-agents
```

#### 5. Verify Deployment

```bash
# Check pod status
oc get pods -n sysadmin-agents

# Check logs
oc logs -f deployment/sysadmin-agents -n sysadmin-agents

# Get route URL
oc get route sysadmin-agents -n sysadmin-agents -o jsonpath='{.spec.host}'
```

### Option 3: Build from Source in OpenShift

If you prefer to build the image inside OpenShift:

```bash
# Create ImageStream and BuildConfig
oc apply -f - <<EOF
apiVersion: image.openshift.io/v1
kind: ImageStream
metadata:
  name: sysadmin-agents
  namespace: sysadmin-agents
---
apiVersion: build.openshift.io/v1
kind: BuildConfig
metadata:
  name: sysadmin-agents
  namespace: sysadmin-agents
spec:
  output:
    to:
      kind: ImageStreamTag
      name: sysadmin-agents:latest
  source:
    type: Binary
  strategy:
    type: Docker
    dockerStrategy:
      dockerfilePath: Containerfile
EOF

# Start build from local source
oc start-build sysadmin-agents --from-dir=. -n sysadmin-agents --follow

# Update deployment to use internal image
oc set image deployment/sysadmin-agents \
  agents=image-registry.openshift-image-registry.svc:5000/sysadmin-agents/sysadmin-agents:latest \
  -n sysadmin-agents
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key | Required |
| `LINUX_MCP_SSH_KEY_PATH` | Path to SSH key | `/opt/app-root/src/.ssh/id_ed25519` |
| `LINUX_MCP_USER` | SSH username | - |
| `LINUX_MCP_ALLOWED_LOG_PATHS` | Allowed log paths | `/var/log/messages,/var/log/secure` |
| `LINUX_MCP_LOG_LEVEL` | MCP server log level | `INFO` |
| `PORT` | Server port | `8000` |
| `ALLOWED_ORIGINS` | CORS origins | `*` |
| `SERVE_WEB_UI` | Enable Web UI | `true` |
| `SESSION_SERVICE_URI` | Session storage | `sqlite+aiosqlite:///./sessions.db` |
| `DEFAULT_MODEL` | LLM model | `gemini-2.0-flash` |

### ConfigMap

The ConfigMap provides a `.env` file that's loaded at container startup:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sysadmin-agents-config
data:
  .env: |
    LINUX_MCP_USER=admin
    LINUX_MCP_LOG_LEVEL=INFO
    ALLOWED_ORIGINS=*
    SERVE_WEB_UI=true
```

## Access

### Web UI

Open the route URL in your browser:
```
https://sysadmin-agents-sysadmin-agents.apps.your-cluster.example.com/dev-ui/
```

### API

```bash
# Test API
curl -s https://your-route/list-apps

# Create session
curl -X POST https://your-route/apps/agents/users/user/sessions/my-session \
  -H "Content-Type: application/json" -d '{}'

# Send query
curl -X POST https://your-route/run \
  -H "Content-Type: application/json" \
  -d '{
    "appName": "agents",
    "userId": "user",
    "sessionId": "my-session",
    "newMessage": {
      "role": "user",
      "parts": [{"text": "Check disk usage on myserver.example.com"}]
    }
  }'
```

## Operations

### Updating the Image

```bash
# Update to new version
oc set image deployment/sysadmin-agents \
  agents=ghcr.io/your-org/sysadmin-agents:v1.2.0 \
  -n sysadmin-agents

# Or trigger a rollout after pushing new image with same tag
oc rollout restart deployment/sysadmin-agents -n sysadmin-agents
```

### Scaling

```bash
# Scale replicas (note: SQLite session storage doesn't scale well)
oc scale deployment/sysadmin-agents --replicas=3 -n sysadmin-agents
```

For multi-replica deployments, consider using PostgreSQL for session storage:
```bash
oc set env deployment/sysadmin-agents \
  SESSION_SERVICE_URI='postgresql+asyncpg://user:pass@postgres:5432/sessions' \
  -n sysadmin-agents
```

### Viewing Logs

```bash
# Stream logs
oc logs -f deployment/sysadmin-agents -n sysadmin-agents

# View recent logs
oc logs deployment/sysadmin-agents -n sysadmin-agents --tail=100
```

## Troubleshooting

### Pod Not Starting

```bash
oc describe pod -l app=sysadmin-agents -n sysadmin-agents
```

Common issues:
- **ImagePullBackOff**: Check image name and registry credentials
- **CrashLoopBackOff**: Check logs for startup errors
- **Pending**: Check resource quotas and node availability

### API Key Invalid

```
google.genai.errors.ClientError: 400 INVALID_ARGUMENT. API key not valid.
```

Update the secret with a valid API key:
```bash
oc delete secret gemini-api-key -n sysadmin-agents
oc create secret generic gemini-api-key \
  --from-literal=GOOGLE_API_KEY='your-valid-key' \
  -n sysadmin-agents
oc rollout restart deployment/sysadmin-agents -n sysadmin-agents
```

### SSH Connection Issues

Check that:
1. SSH key is mounted correctly: `oc exec deployment/sysadmin-agents -- ls -la /opt/app-root/src/.ssh/`
2. SSH key has correct permissions (should be 0400)
3. Target hosts are reachable from the cluster
4. `LINUX_MCP_USER` is set correctly

### ConfigMap Not Loading

Check the mount:
```bash
oc exec deployment/sysadmin-agents -- cat /opt/app-root/config/.env
```

Check container logs for: `Loaded configuration from: /opt/app-root/config/.env`

## Cleanup

```bash
# Delete all resources
oc delete -k deploy/ -n sysadmin-agents

# Delete namespace (removes everything)
oc delete namespace sysadmin-agents
```
