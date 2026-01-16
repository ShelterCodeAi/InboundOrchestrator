#!/bin/bash
#
# Zato ESB Installation and Setup Script
# 
# This script automates the installation and initial configuration of Zato ESB
# for the InboundOrchestrator migration.
#

set -e  # Exit on error

ZATO_DIR="${ZATO_DIR:-$HOME/zato-inbound-orchestrator}"
ZATO_VERSION="${ZATO_VERSION:-latest}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

echo "================================================"
echo "Zato ESB Installation Script"
echo "================================================"
echo "Target directory: $ZATO_DIR"
echo "Python version: $PYTHON_VERSION"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists python3; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

if ! command_exists pip3; then
    echo "Error: pip3 is not installed"
    exit 1
fi

echo "✓ Prerequisites check passed"
echo ""

# Install Zato
echo "Installing Zato..."
pip3 install zato

echo "✓ Zato installed successfully"
echo ""

# Create quickstart cluster
echo "Creating Zato quickstart cluster..."

if [ -d "$ZATO_DIR" ]; then
    echo "Warning: $ZATO_DIR already exists. Skipping cluster creation."
else
    zato quickstart create "$ZATO_DIR" sqlite localhost 8000
    echo "✓ Zato cluster created at $ZATO_DIR"
fi

echo ""

# Create PostgreSQL ODB (optional, for production)
read -p "Do you want to configure PostgreSQL ODB for production? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Configuring PostgreSQL ODB..."
    read -p "Enter PostgreSQL host [localhost]: " PG_HOST
    PG_HOST=${PG_HOST:-localhost}
    
    read -p "Enter PostgreSQL database name [zato_odb]: " PG_DB
    PG_DB=${PG_DB:-zato_odb}
    
    read -p "Enter PostgreSQL user [zato]: " PG_USER
    PG_USER=${PG_USER:-zato}
    
    read -sp "Enter PostgreSQL password: " PG_PASSWORD
    echo ""
    
    # Create ODB
    zato create odb postgresql "host=$PG_HOST dbname=$PG_DB user=$PG_USER" --odb-password "$PG_PASSWORD"
    
    echo "✓ PostgreSQL ODB configured"
fi

echo ""

# Start Zato components
echo "Starting Zato components..."

zato start "$ZATO_DIR/server1"
zato start "$ZATO_DIR/web-admin"

echo "✓ Zato components started"
echo ""

# Display access information
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "Zato Web Admin: http://localhost:8183"
echo "Server status: zato info $ZATO_DIR/server1"
echo "Server logs: tail -f $ZATO_DIR/server1/logs/server.log"
echo ""
echo "Next steps:"
echo "1. Access the web admin and configure database connections"
echo "2. Deploy Zato services from zato_services/ directory"
echo "3. Configure scheduled jobs for email intake"
echo "4. Load initial configurations (rules, queues)"
echo ""
echo "See zato_services/README.md for detailed deployment instructions"
echo "================================================"
