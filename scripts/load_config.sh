#!/bin/bash
#
# Load Initial Configurations Script
#
# This script loads initial configurations (rules, queues) into Zato's
# Key-Value DB by invoking the configuration loader services.
#

set -e

ZATO_DIR="${ZATO_DIR:-$HOME/zato-inbound-orchestrator}"

echo "================================================"
echo "Zato Configuration Loader Script"
echo "================================================"
echo ""

# Check if Zato is running
if ! pgrep -f "zato.*server1" > /dev/null; then
    echo "Error: Zato server is not running"
    echo "Please start Zato first: zato start $ZATO_DIR/server1"
    exit 1
fi

echo "Loading SQS queue configurations..."
zato service invoke email.config.load-sqs-queues

echo "✓ SQS queues configured"
echo ""

echo "Loading email routing rules..."
zato service invoke email.rules.load-from-config

echo "✓ Email rules configured"
echo ""

echo "================================================"
echo "Configuration Loading Complete!"
echo "================================================"
echo ""
echo "Configurations loaded:"
echo "  ✓ SQS queue configurations"
echo "  ✓ Email routing rules"
echo ""
echo "To verify configurations:"
echo "  redis-cli KEYS email.rule.*"
echo "  redis-cli GET aws.sqs.queues"
echo ""
echo "To update configurations, edit the service payloads and re-run:"
echo "  zato service invoke email.config.load-sqs-queues --payload '{...}'"
echo "  zato service invoke email.rules.load-from-config --payload '{...}'"
echo "================================================"
