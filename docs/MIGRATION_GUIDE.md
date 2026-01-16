# Zato ESB Migration Guide

This guide provides step-by-step instructions for migrating from the current InboundOrchestrator architecture to Zato ESB.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Migration Phases](#migration-phases)
3. [Step-by-Step Instructions](#step-by-step-instructions)
4. [Testing and Validation](#testing-and-validation)
5. [Rollback Procedure](#rollback-procedure)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Ubuntu 20.04+ or equivalent Linux distribution
- Python 3.8 or higher
- PostgreSQL 12+ (for production)
- Redis (for Zato Key-Value DB)
- AWS account with SQS access
- 4GB+ RAM recommended
- 20GB+ free disk space

### Required Permissions

- Sudo access for system package installation
- AWS credentials with SQS permissions
- PostgreSQL database creation permissions

### Software Dependencies

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Install PostgreSQL
sudo apt-get install -y postgresql postgresql-contrib

# Install Redis
sudo apt-get install -y redis-server

# Install build essentials
sudo apt-get install -y build-essential libpq-dev
```

## Migration Phases

The migration follows a 6-phase approach as detailed in [migrationplan.md](migrationplan.md):

1. **Phase 1**: Infrastructure Setup (Week 1-2)
2. **Phase 2**: Email Intake Migration (Week 3-4)
3. **Phase 3**: Rule Engine Migration (Week 5-6)
4. **Phase 4**: SQS Integration Migration (Week 7-8)
5. **Phase 5**: Orchestration Service (Week 9-10)
6. **Phase 6**: API Migration (Week 11-12)

## Step-by-Step Instructions

### Phase 1: Infrastructure Setup

#### 1.1 Install Zato ESB

Run the automated installation script:

```bash
cd /path/to/InboundOrchestrator
./scripts/install_zato.sh
```

Or manually:

```bash
# Install Zato via pip
pip3 install zato

# Create quickstart cluster
zato quickstart create ~/zato-inbound-orchestrator sqlite localhost 8000

# For production, configure PostgreSQL ODB
zato create odb postgresql "host=localhost dbname=zato_odb user=zato" --odb-password "your_password"
```

#### 1.2 Start Zato Components

```bash
# Start Zato server
zato start ~/zato-inbound-orchestrator/server1

# Start web admin
zato start ~/zato-inbound-orchestrator/web-admin

# Verify server is running
zato info ~/zato-inbound-orchestrator/server1
```

#### 1.3 Access Web Admin

1. Open browser to http://localhost:8183
2. Login with credentials displayed during quickstart creation
3. Verify cluster status in dashboard

### Phase 2: Email Intake Migration

#### 2.1 Deploy Zato Services

Run the deployment script:

```bash
./scripts/deploy_services.sh
```

Or manually:

```bash
# Copy services to pickup directory
cp zato_services/email/*.py ~/zato-inbound-orchestrator/server1/pickup/incoming/
cp zato_services/config/*.py ~/zato-inbound-orchestrator/server1/pickup/incoming/
cp zato_services/api/*.py ~/zato-inbound-orchestrator/server1/pickup/incoming/

# Wait for hot deployment (services auto-deploy within seconds)
```

#### 2.2 Configure Database Connections

In Zato Web Admin:

1. Navigate to **Connections → Outgoing → SQL**
2. Click **Create a new SQL connection**
3. Configure `email_db` connection:
   - **Name**: `email_db`
   - **Type**: PostgreSQL
   - **Host**: localhost (or your DB host)
   - **Port**: 5432
   - **Database**: email_db
   - **Username**: postgres
   - **Password**: [your password]
   - **Pool size**: 10
4. Click **OK** to save
5. Test connection by clicking **Ping**

Repeat for `fulfillment_db` if using API services.

#### 2.3 Load Initial Configurations

Run the configuration loader:

```bash
./scripts/load_config.sh
```

Or manually:

```bash
# Load SQS queue configurations
zato service invoke email.config.load-sqs-queues

# Load routing rules
zato service invoke email.rules.load-from-config
```

#### 2.4 Configure Scheduled Jobs

In Zato Web Admin:

1. Navigate to **Scheduler**
2. Click **Create a new job**
3. Configure email intake job:
   - **Name**: `postgres-email-intake`
   - **Service**: `email.intake.postgres-fetch`
   - **Type**: Interval-based
   - **Interval**: 60 (seconds)
   - **Active**: Yes
4. Click **OK** to save

### Phase 3: Rule Engine Migration

#### 3.1 Migrate Existing Rules

Convert your existing YAML rules to the Zato format and load them:

```python
# Example: Load custom rules
import json
import requests

rules = [
    {
        'name': 'your_custom_rule',
        'description': 'Your rule description',
        'condition': "priority == 'high'",
        'action': 'high_priority',
        'priority': 100,
        'enabled': True
    }
]

# Invoke rule loader service with custom rules
payload = {'rules': rules}
# Use Zato service invocation or REST API
```

#### 3.2 Verify Rules in KV DB

```bash
# Check loaded rules in Redis
redis-cli
> KEYS email.rule.*
> GET email.rule.urgent_emails
```

### Phase 4: SQS Integration Migration

#### 4.1 Configure AWS Credentials

**Option 1: Environment Variables (Development)**

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**Option 2: Zato KV DB (Production - Recommended with IAM Roles)**

```python
# Load AWS config into KV DB
import json

aws_config = {
    'region': 'us-east-1',
    'access_key': '',  # Leave empty to use IAM role
    'secret_key': ''
}

# Use Zato service or Redis CLI
redis-cli SET aws.sqs.config '{"region":"us-east-1","access_key":"","secret_key":""}'
```

#### 4.2 Configure SQS Queues

Update queue configurations in the config loader service:

```python
queues = {
    'high_priority': {
        'url': 'https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID/high-priority',
        'description': 'High priority emails'
    },
    'support': {
        'url': 'https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID/support',
        'description': 'Support emails'
    },
    'default': {
        'url': 'https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID/default',
        'description': 'Default queue'
    }
}
```

Reload configurations:

```bash
zato service invoke email.config.load-sqs-queues --payload '{"queues": {...}}'
```

### Phase 5: Orchestration Service

The orchestration service is already deployed. Test it:

```bash
# Test with dry run
zato service invoke email.orchestrator.process --payload '{
  "subject": "Test Email",
  "sender": "test@example.com",
  "dry_run": true
}'
```

### Phase 6: API Migration

#### 6.1 Configure REST Channels

In Zato Web Admin:

1. Navigate to **Connections → Channels → REST**
2. Click **Create a new REST channel**
3. Configure marketplaces endpoint:
   - **Name**: `api-marketplaces-list`
   - **URL path**: `/api/marketplaces`
   - **Service**: `api.marketplaces.list`
   - **Method**: GET
   - **Data format**: JSON
   - **Security**: [Configure as needed]
4. Click **OK** to save

Repeat for other API endpoints.

#### 6.2 Update React UI (if applicable)

Update API base URL in React configuration:

```javascript
// config.js
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

## Testing and Validation

### Unit Tests

Run the Zato service tests:

```bash
cd /path/to/InboundOrchestrator
pytest tests/zato_services/ -v
```

Expected output: All 25 tests pass

### Integration Tests

Run full test suite:

```bash
pytest tests/ --cov=inbound_orchestrator --cov-config=.coveragerc -v
```

Expected output: 169 tests pass with 91%+ coverage

### End-to-End Testing

1. **Test Email Processing**:

```bash
# Process a test email (dry run)
zato service invoke email.orchestrator.process --payload '{
  "subject": "URGENT: Test",
  "sender": "test@example.com",
  "body_text": "Test body",
  "dry_run": true
}'
```

2. **Test Rule Evaluation**:

```bash
zato service invoke email.rules.evaluate --payload '{
  "subject": "Help needed",
  "sender": "customer@example.com",
  "priority": "normal"
}'
```

3. **Monitor Statistics**:

```bash
redis-cli
> GET stats.email.total_processed
> GET stats.email.successful_routes
> KEYS stats.email.*
```

### Performance Testing

Test with batch processing:

```bash
# Simulate 100 emails
for i in {1..100}; do
  zato service invoke email.orchestrator.process --payload "{
    \"subject\": \"Test $i\",
    \"sender\": \"test$i@example.com\",
    \"dry_run\": true
  }"
done
```

Monitor server logs:

```bash
tail -f ~/zato-inbound-orchestrator/server1/logs/server.log
```

## Rollback Procedure

If issues arise during migration:

### Immediate Rollback

1. **Stop Zato scheduler jobs**:
   - In Web Admin → Scheduler
   - Deactivate `postgres-email-intake` job

2. **Disable Zato REST channels**:
   - In Web Admin → Connections → Channels → REST
   - Deactivate all migrated endpoints

3. **Re-enable legacy system**:
   - Start original InboundOrchestrator service
   - Resume legacy email processing

4. **Verify system recovery**:
   - Check email processing continues
   - Monitor SQS queues
   - Verify no data loss

### Complete Rollback

```bash
# Stop Zato components
zato stop ~/zato-inbound-orchestrator/server1
zato stop ~/zato-inbound-orchestrator/web-admin

# Restart legacy services
# [Your legacy startup commands]
```

## Troubleshooting

### Services Not Deploying

**Symptom**: Services don't appear in service list

**Solution**:
```bash
# Check server logs
tail -f ~/zato-inbound-orchestrator/server1/logs/server.log

# Verify Python syntax
python3 -m py_compile zato_services/email/email_parser_service.py

# Check pickup directory permissions
ls -la ~/zato-inbound-orchestrator/server1/pickup/incoming/
```

### Database Connection Errors

**Symptom**: "Connection failed" errors in logs

**Solution**:
```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d email_db

# Check connection settings in Web Admin
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

### SQS Send Failures

**Symptom**: Messages not reaching SQS queues

**Solution**:
```bash
# Verify AWS credentials
aws sqs list-queues --region us-east-1

# Check queue URLs are correct
redis-cli GET aws.sqs.queues

# Verify IAM permissions
# Ensure SQS send permissions are granted

# Check Zato logs for detailed error
tail -f ~/zato-inbound-orchestrator/server1/logs/server.log | grep SQS
```

### High Memory Usage

**Symptom**: Zato server consuming excessive memory

**Solution**:
```bash
# Check server resource usage
zato info ~/zato-inbound-orchestrator/server1

# Adjust worker pool size in server.conf
# Restart server
zato stop ~/zato-inbound-orchestrator/server1
zato start ~/zato-inbound-orchestrator/server1
```

### Rule Evaluation Issues

**Symptom**: Rules not matching expected emails

**Solution**:
```bash
# Verify rules in Redis
redis-cli KEYS email.rule.*

# Check specific rule
redis-cli GET email.rule.urgent_emails

# Test rule evaluation
zato service invoke email.rules.evaluate --payload '{
  "subject": "URGENT",
  "sender": "test@example.com"
}'

# Check rule syntax
# Ensure conditions are valid Python expressions
```

## Additional Resources

- [Zato Official Documentation](https://zato.io/docs)
- [Migration Plan](migrationplan.md)
- [Migration Checklist](migrationplanchecklist.md)
- [Zato Services README](../zato_services/README.md)

## Support

For issues or questions:

1. Check server logs: `tail -f ~/zato-inbound-orchestrator/server1/logs/server.log`
2. Review Zato documentation: https://zato.io/docs
3. Check migration checklist for known issues
4. Contact team for assistance

---

**Last Updated**: 2026-01-16  
**Version**: 1.0
