# Zato Services for InboundOrchestrator Migration

This directory contains Zato service implementations for the migration from the custom InboundOrchestrator architecture to Zato ESB.

## Directory Structure

```
zato_services/
├── email/              # Email processing services
│   ├── email_parser_service.py          # Parse raw emails
│   ├── postgres_intake_service.py       # Fetch emails from PostgreSQL
│   ├── rule_loader_service.py           # Load routing rules to KV DB
│   ├── rule_evaluator_service.py        # Evaluate emails against rules
│   ├── sqs_outbound_service.py          # Send emails to SQS queues
│   └── email_orchestrator_service.py    # Master orchestration service
├── config/             # Configuration services
│   └── sqs_config_loader.py             # Load SQS queue configurations
└── api/                # REST API services
    └── marketplaces_service.py          # Marketplaces API endpoint
```

## Services Overview

### Email Processing Services

#### 1. EmailParserService
- **Service Name:** `email.parser.parse-raw`
- **Purpose:** Parse raw email content into structured data
- **Input:** Raw email string
- **Output:** Structured email data dictionary

#### 2. PostgresEmailIntakeService
- **Service Name:** `email.intake.postgres-fetch`
- **Purpose:** Scheduled job to fetch unprocessed emails from PostgreSQL
- **Schedule:** Every 60 seconds (configured in Zato web admin)
- **Dependencies:** Requires `email_db` SQL connection

#### 3. RuleLoaderService
- **Service Name:** `email.rules.load-from-config`
- **Purpose:** Load email routing rules into Zato Key-Value DB
- **Input:** Optional rules array (uses defaults if not provided)
- **Storage:** Redis keys like `email.rule.<rule_name>`

#### 4. RuleEvaluatorService
- **Service Name:** `email.rules.evaluate`
- **Purpose:** Evaluate emails against routing rules
- **Input:** Email data dictionary
- **Output:** Matched rule name and action (queue name)

#### 5. SQSOutboundService
- **Service Name:** `email.outbound.sqs-send`
- **Purpose:** Send messages to AWS SQS queues
- **Input:** Email data and queue name
- **Output:** SQS message ID and success status
- **Dependencies:** Requires AWS credentials in KV DB

#### 6. EmailOrchestratorService
- **Service Name:** `email.orchestrator.process`
- **Purpose:** Master orchestration service coordinating the full flow
- **Flow:** Email → Rule Evaluation → SQS Routing → Statistics
- **Features:** Dry run mode, statistics tracking

### Configuration Services

#### SQSConfigLoaderService
- **Service Name:** `email.config.load-sqs-queues`
- **Purpose:** Load SQS queue configurations into KV DB
- **Storage:** 
  - `aws.sqs.queues` - Queue configurations
  - `aws.sqs.config` - AWS credentials and region

### API Services

#### MarketplacesAPIService
- **Service Name:** `api.marketplaces.list`
- **Purpose:** REST API for marketplaces
- **Endpoints:** GET /api/marketplaces, GET /api/marketplaces/{id}
- **Dependencies:** Requires `fulfillment_db` SQL connection

## Deployment Instructions

### 1. Set Up Zato Cluster

```bash
# Install Zato
pip install zato

# Create quickstart cluster
zato quickstart create ~/zato-inbound-orchestrator sqlite localhost 8000

# For production, use PostgreSQL ODB
zato create odb postgresql "host=localhost dbname=zato_odb user=zato" --odb-password "password"
```

### 2. Start Zato Components

```bash
# Start server
zato start ~/zato-inbound-orchestrator/server1

# Start web admin
zato start ~/zato-inbound-orchestrator/web-admin

# Access web admin at http://localhost:8183
```

### 3. Deploy Services

Copy service files to the Zato pickup directory for hot deployment:

```bash
# Copy email services
cp zato_services/email/*.py ~/zato-inbound-orchestrator/server1/pickup/incoming/

# Copy config services
cp zato_services/config/*.py ~/zato-inbound-orchestrator/server1/pickup/incoming/

# Copy API services
cp zato_services/api/*.py ~/zato-inbound-orchestrator/server1/pickup/incoming/
```

Services will be automatically deployed within seconds.

### 4. Configure Database Connections

Via Zato Web Admin (http://localhost:8183):

1. Navigate to **Connections → Outgoing → SQL**
2. Create connection `email_db`:
   - Type: PostgreSQL
   - Host: localhost
   - Database: email_db
   - Username: postgres
   - Password: [your password]

3. Create connection `fulfillment_db`:
   - Type: PostgreSQL
   - Host: localhost
   - Database: fulfillment_db
   - Username: postgres
   - Password: [your password]

### 5. Load Initial Configurations

Invoke configuration loader services:

```bash
# Load SQS queue configurations
zato service invoke email.config.load-sqs-queues

# Load routing rules
zato service invoke email.rules.load-from-config
```

### 6. Configure Scheduled Jobs

Via Zato Web Admin:

1. Navigate to **Scheduler → Create a new job**
2. Configure email intake job:
   - Name: `postgres-email-intake`
   - Service: `email.intake.postgres-fetch`
   - Type: Interval-based
   - Interval: 60 seconds
   - Active: Yes

### 7. Configure REST Channels

Via Zato Web Admin, for each API endpoint:

1. Navigate to **Connections → Channels → REST**
2. Create channel for `/api/marketplaces`:
   - Name: `marketplaces-list`
   - URL path: `/api/marketplaces`
   - Service: `api.marketplaces.list`
   - Method: GET
   - Data format: JSON

Repeat for other API endpoints.

## Testing Services

### Test Individual Services

```bash
# Test email parser
zato service invoke email.parser.parse-raw --payload '{"raw_email": "Subject: Test\n\nBody"}'

# Test rule evaluator
zato service invoke email.rules.evaluate --payload '{"subject": "URGENT", "sender": "test@example.com"}'

# Test orchestrator (dry run)
zato service invoke email.orchestrator.process --payload '{"subject": "Test", "dry_run": true}'
```

### View Service Logs

```bash
# View server logs
tail -f ~/zato-inbound-orchestrator/server1/logs/server.log
```

### Monitor Statistics

Statistics are stored in Redis with keys:
- `stats.email.total_processed`
- `stats.email.successful_routes`
- `stats.email.failed_routes`
- `stats.email.queue.<queue_name>`

Access via Redis CLI:

```bash
redis-cli
> GET stats.email.total_processed
> KEYS stats.email.*
```

## Configuration Reference

### Rule Format

Rules are stored in Redis as JSON:

```json
{
  "name": "urgent_emails",
  "description": "Route urgent emails to high priority queue",
  "condition": "priority == 'urgent' or 'URGENT' in subject",
  "action": "high_priority",
  "priority": 100,
  "enabled": true
}
```

### SQS Queue Format

Queue configurations in Redis:

```json
{
  "high_priority": {
    "url": "https://sqs.us-east-1.amazonaws.com/123456789012/high-priority",
    "description": "High priority emails"
  }
}
```

### AWS Configuration

AWS credentials and region:

```json
{
  "region": "us-east-1",
  "access_key": "",
  "secret_key": ""
}
```

Note: Leave credentials empty to use IAM roles in production.

## Migration Phases

See [ai/migration/migrationplanchecklist.md](../../ai/migration/migrationplanchecklist.md) for the complete migration plan and progress tracking.

## Troubleshooting

### Services Not Deploying

- Check Zato server logs: `tail -f ~/zato-inbound-orchestrator/server1/logs/server.log`
- Verify Python syntax: `python -m py_compile <service_file>.py`
- Check pickup directory permissions

### Database Connection Errors

- Verify PostgreSQL is running
- Check connection settings in web admin
- Test connection: `zato service invoke <service_name>`

### SQS Send Failures

- Verify AWS credentials are configured
- Check SQS queue URLs are correct
- Verify IAM permissions for SQS

### Rule Evaluation Issues

- Check rule conditions syntax
- Verify rules are enabled in KV DB
- Use Redis CLI to inspect: `redis-cli KEYS email.rule.*`

## Additional Resources

- [Zato Documentation](https://zato.io/docs)
- [Migration Plan](../../ai/migration/migrationplan.md)
- [Migration Checklist](../../ai/migration/migrationplanchecklist.md)
