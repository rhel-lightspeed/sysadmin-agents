#!/bin/bash
# Deploy sysadmin-agents to OpenShift/Kubernetes
# 
# Usage: 
#   ./scripts/deploy.sh                    # Deploy to default namespace
#   ./scripts/deploy.sh my-namespace       # Deploy to custom namespace
#   ./scripts/deploy.sh my-namespace myregistry.io/image:tag  # Custom image
#
# Prerequisites:
#   1. Logged into cluster: oc login ...
#   2. Secrets created (see deploy/secrets.yaml.example)

set -euo pipefail

NAMESPACE="${1:-sysadmin-agents}"
IMAGE="${2:-ghcr.io/your-org/sysadmin-agents:latest}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Deploying Sysadmin Agents"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Image:     $IMAGE"
echo ""

# Check if oc/kubectl is available
if command -v oc &> /dev/null; then
    CLI="oc"
elif command -v kubectl &> /dev/null; then
    CLI="kubectl"
else
    echo "Error: Neither 'oc' nor 'kubectl' found. Please install one."
    exit 1
fi

# Check if logged in
if ! $CLI auth can-i get pods &> /dev/null; then
    echo "Error: Not logged into cluster. Run '$CLI login' first."
    exit 1
fi

# Create namespace if it doesn't exist
if ! $CLI get namespace "$NAMESPACE" &> /dev/null; then
    echo "Creating namespace $NAMESPACE..."
    $CLI create namespace "$NAMESPACE"
fi

# Check for required secrets
echo ""
echo "Checking secrets..."

if ! $CLI get secret gemini-api-key -n "$NAMESPACE" &> /dev/null; then
    echo ""
    echo "⚠️  Secret 'gemini-api-key' not found."
    echo "   Create it with:"
    echo "   $CLI create secret generic gemini-api-key \\"
    echo "     --from-literal=GOOGLE_API_KEY='your-api-key' \\"
    echo "     -n $NAMESPACE"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Secret 'gemini-api-key' exists"
fi

if ! $CLI get secret ssh-private-key -n "$NAMESPACE" &> /dev/null; then
    echo ""
    echo "⚠️  Secret 'ssh-private-key' not found (optional for MCP)."
    echo "   Create it with:"
    echo "   $CLI create secret generic ssh-private-key \\"
    echo "     --from-file=id_ed25519=~/.ssh/id_ed25519 \\"
    echo "     -n $NAMESPACE"
    echo ""
else
    echo "✓ Secret 'ssh-private-key' exists"
fi

# Update image in deployment
echo ""
echo "Applying manifests..."
cd "$PROJECT_ROOT/deploy"

# Apply ConfigMap first
$CLI apply -f configmap.yaml -n "$NAMESPACE"

# Apply deployment with image override
sed "s|image: ghcr.io/your-org/sysadmin-agents:latest|image: $IMAGE|g" deployment.yaml | \
    $CLI apply -f - -n "$NAMESPACE"

# Apply service
$CLI apply -f service.yaml -n "$NAMESPACE"

# Apply route (OpenShift only)
if $CLI api-resources | grep -q "routes.route.openshift.io"; then
    $CLI apply -f route.yaml -n "$NAMESPACE"
    ROUTE_TYPE="route"
else
    echo "Note: Routes not available (not OpenShift). Use kubectl port-forward or create Ingress."
    ROUTE_TYPE="none"
fi

# Wait for deployment
echo ""
echo "Waiting for deployment to be ready..."
$CLI rollout status deployment/sysadmin-agents -n "$NAMESPACE" --timeout=300s

# Get access URL
echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="

if [ "$ROUTE_TYPE" = "route" ]; then
    ROUTE_URL=$($CLI get route sysadmin-agents -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
    if [ -n "$ROUTE_URL" ]; then
        echo "Access URL: https://$ROUTE_URL"
    fi
else
    echo "Access via port-forward:"
    echo "  $CLI port-forward -n $NAMESPACE svc/sysadmin-agents 8000:8000"
    echo "  Then open: http://localhost:8000"
fi
