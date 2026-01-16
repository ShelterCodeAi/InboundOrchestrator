#!/bin/bash
#
# Deploy Zato Services Script
#
# This script deploys all Zato services from the zato_services directory
# to the Zato server's pickup/incoming directory for hot deployment.
#

set -e

ZATO_DIR="${ZATO_DIR:-$HOME/zato-inbound-orchestrator}"
SERVER_DIR="$ZATO_DIR/server1"
PICKUP_DIR="$SERVER_DIR/pickup/incoming"
SERVICES_DIR="$(dirname "$0")/../zato_services"

echo "================================================"
echo "Zato Services Deployment Script"
echo "================================================"
echo "Zato directory: $ZATO_DIR"
echo "Services directory: $SERVICES_DIR"
echo "Pickup directory: $PICKUP_DIR"
echo ""

# Check if Zato server directory exists
if [ ! -d "$SERVER_DIR" ]; then
    echo "Error: Zato server directory not found at $SERVER_DIR"
    echo "Please install Zato first using scripts/install_zato.sh"
    exit 1
fi

# Create pickup directory if it doesn't exist
mkdir -p "$PICKUP_DIR"

# Deploy services
echo "Deploying Zato services..."

# Deploy email services
echo "  Deploying email services..."
cp "$SERVICES_DIR/email"/*.py "$PICKUP_DIR/"

# Deploy config services
echo "  Deploying config services..."
cp "$SERVICES_DIR/config"/*.py "$PICKUP_DIR/"

# Deploy API services
echo "  Deploying API services..."
cp "$SERVICES_DIR/api"/*.py "$PICKUP_DIR/"

echo "✓ Services deployed successfully"
echo ""

# Wait for services to be picked up
echo "Waiting for Zato to deploy services (10 seconds)..."
sleep 10

echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo ""
echo "Services deployed to: $PICKUP_DIR"
echo ""
echo "To verify deployment:"
echo "  zato service list"
echo ""
echo "To view server logs:"
echo "  tail -f $SERVER_DIR/logs/server.log"
echo ""
echo "Next steps:"
echo "1. Configure database connections in web admin"
echo "2. Load initial configurations using scripts/load_config.sh"
echo "3. Configure scheduled jobs in web admin"
echo "================================================"
