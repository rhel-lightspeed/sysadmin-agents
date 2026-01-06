#!/bin/bash
# Sync agent and core code to OpenShift ConfigMaps
# Usage: ./scripts/sync-agents.sh [namespace]

set -euo pipefail

NAMESPACE="${1:-adk-web}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Syncing sysadmin-agents to namespace: $NAMESPACE"

# Check if oc is available
if ! command -v oc &> /dev/null; then
    echo "Error: 'oc' command not found. Please install OpenShift CLI."
    exit 1
fi

# Check if logged in
if ! oc whoami &> /dev/null; then
    echo "Error: Not logged into OpenShift. Run 'oc login' first."
    exit 1
fi

cd "$PROJECT_ROOT"

# ============================================================================
# Create agents ConfigMap
# ============================================================================
echo "Creating agents ConfigMap..."

# Delete existing ConfigMap if it exists
oc delete configmap sysadmin-agents-code -n "$NAMESPACE" --ignore-not-found

# Build the configmap with all agent files
AGENT_FILES=""

# Main agents __init__.py
AGENT_FILES="$AGENT_FILES --from-file=__init__.py=agents/__init__.py"

# Dispatcher
AGENT_FILES="$AGENT_FILES --from-file=dispatcher/__init__.py=agents/dispatcher/__init__.py"
AGENT_FILES="$AGENT_FILES --from-file=dispatcher/agent.py=agents/dispatcher/agent.py"
AGENT_FILES="$AGENT_FILES --from-file=dispatcher/config.yaml=agents/dispatcher/config.yaml"

# Base
AGENT_FILES="$AGENT_FILES --from-file=base/__init__.py=agents/base/__init__.py"
AGENT_FILES="$AGENT_FILES --from-file=base/mcp_client.py=agents/base/mcp_client.py"
AGENT_FILES="$AGENT_FILES --from-file=base/agent_template.py=agents/base/agent_template.py"
AGENT_FILES="$AGENT_FILES --from-file=base/tool_wrapper.py=agents/base/tool_wrapper.py"

# Specialists
AGENT_FILES="$AGENT_FILES --from-file=specialists/__init__.py=agents/specialists/__init__.py"

# RCA Specialist
AGENT_FILES="$AGENT_FILES --from-file=specialists/rca/__init__.py=agents/specialists/rca/__init__.py"
AGENT_FILES="$AGENT_FILES --from-file=specialists/rca/agent.py=agents/specialists/rca/agent.py"
AGENT_FILES="$AGENT_FILES --from-file=specialists/rca/config.yaml=agents/specialists/rca/config.yaml"

eval "oc create configmap sysadmin-agents-code $AGENT_FILES -n $NAMESPACE"

echo "Agents ConfigMap created."

# ============================================================================
# Create core ConfigMap
# ============================================================================
echo "Creating core ConfigMap..."

oc delete configmap sysadmin-core-code -n "$NAMESPACE" --ignore-not-found

oc create configmap sysadmin-core-code \
    --from-file=__init__.py=core/__init__.py \
    --from-file=config.py=core/config.py \
    --from-file=session.py=core/session.py \
    -n "$NAMESPACE"

echo "Core ConfigMap created."

# ============================================================================
# Restart deployment
# ============================================================================
echo "Restarting deployment..."
oc rollout restart deployment/sysadmin-agents -n "$NAMESPACE" 2>/dev/null || true

echo ""
echo "Done! Code synced to OpenShift."
echo "Run 'oc get pods -n $NAMESPACE' to check status."
