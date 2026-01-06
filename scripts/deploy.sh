#!/bin/bash
# Deploy sysadmin-agents to OpenShift
# Usage: ./scripts/deploy.sh [namespace]

set -euo pipefail

NAMESPACE="${1:-adk-web}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Deploying sysadmin-agents to namespace: $NAMESPACE"

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

# Check if namespace exists
if ! oc get namespace "$NAMESPACE" &> /dev/null; then
    echo "Creating namespace $NAMESPACE..."
    oc create namespace "$NAMESPACE"
fi

# Check for required secrets
echo "Checking required secrets..."

if ! oc get secret gemini-api-key -n "$NAMESPACE" &> /dev/null; then
    echo ""
    echo "WARNING: Secret 'gemini-api-key' not found."
    echo "Create it with:"
    echo "  oc create secret generic gemini-api-key \\"
    echo "    --from-literal=GOOGLE_API_KEY='your-api-key' \\"
    echo "    -n $NAMESPACE"
    echo ""
fi

if ! oc get secret ssh-private-key -n "$NAMESPACE" &> /dev/null; then
    echo ""
    echo "WARNING: Secret 'ssh-private-key' not found."
    echo "Create it with:"
    echo "  oc create secret generic ssh-private-key \\"
    echo "    --from-file=id_ed25519=~/.ssh/id_ed25519 \\"
    echo "    -n $NAMESPACE"
    echo ""
fi

# Sync agent code first
echo "Syncing agent code..."
"$SCRIPT_DIR/sync-agents.sh" "$NAMESPACE"

# Apply Kubernetes resources
echo "Applying deployment manifests..."
cd "$PROJECT_ROOT/deploy"

oc apply -f deployment.yaml -n "$NAMESPACE"
oc apply -f service.yaml -n "$NAMESPACE"
oc apply -f route.yaml -n "$NAMESPACE"

# Wait for deployment
echo "Waiting for deployment to be ready..."
oc rollout status deployment/sysadmin-agents -n "$NAMESPACE" --timeout=300s

# Get route URL
ROUTE_URL=$(oc get route sysadmin-agents -n "$NAMESPACE" -o jsonpath='{.spec.host}')

echo ""
echo "Deployment complete!"
echo "Access the agents at: https://$ROUTE_URL"

