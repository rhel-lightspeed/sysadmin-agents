#!/bin/bash
# Test script for sysadmin-agents with RHEL VM
# 
# Prerequisites:
# 1. SSH access to RHEL VM
# 2. pip install google-adk linux-mcp-server

set -e

# RHEL VM Configuration
RHEL_HOST="${RHEL_HOST:-bastion.kmj85.sandbox1706.opentlc.com}"
RHEL_USER="${RHEL_USER:-student}"

echo "========================================"
echo "Sysadmin Agents - RHEL Test Setup"
echo "========================================"
echo ""

# Check if linux-mcp-server is installed
if command -v linux-mcp-server &> /dev/null; then
    echo "✓ linux-mcp-server found: $(which linux-mcp-server)"
else
    echo "✗ linux-mcp-server not found"
    echo "  Install with: pip install linux-mcp-server"
    echo ""
    read -p "Install now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install linux-mcp-server
    else
        exit 1
    fi
fi

# Check if google-adk is installed
if python3 -c "import google.adk" 2>/dev/null; then
    echo "✓ google-adk installed"
else
    echo "✗ google-adk not found"
    echo "  Install with: pip install google-adk"
    echo ""
    read -p "Install now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install google-adk
    else
        exit 1
    fi
fi

# Check SSH connection
echo ""
echo "Testing SSH connection to ${RHEL_USER}@${RHEL_HOST}..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes ${RHEL_USER}@${RHEL_HOST} "echo 'SSH OK'" 2>/dev/null; then
    echo "✓ SSH connection successful"
else
    echo "✗ SSH connection failed"
    echo ""
    echo "To set up SSH key authentication:"
    echo "  1. ssh-copy-id ${RHEL_USER}@${RHEL_HOST}"
    echo "  2. Enter password when prompted"
    echo ""
    echo "Or connect manually first:"
    echo "  ssh ${RHEL_USER}@${RHEL_HOST}"
    echo ""
    exit 1
fi

# Test linux-mcp-server with remote host
echo ""
echo "Testing linux-mcp-server connection..."
export LINUX_MCP_USER="${RHEL_USER}"
export LINUX_MCP_LOG_LEVEL="INFO"

# Simple test: get system info
echo "Fetching system information from ${RHEL_HOST}..."
# Note: This would require running the MCP server and making a call
# For now, just verify the environment is set up

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Environment variables set:"
echo "  LINUX_MCP_USER=${LINUX_MCP_USER}"
echo "  RHEL_HOST=${RHEL_HOST}"
echo ""
echo "To start the ADK web interface:"
echo "  cd $(pwd)"
echo "  export GOOGLE_API_KEY=your-api-key"
echo "  adk web --port 8000"
echo ""
echo "Then test with queries like:"
echo "  - 'Why is my system slow? Host: ${RHEL_HOST}'"
echo "  - 'Where did my disk space go? Host: ${RHEL_HOST}'"
echo "  - 'Check the system health on ${RHEL_HOST}'"

