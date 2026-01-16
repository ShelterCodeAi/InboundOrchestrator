# InboundOrchestrator

A powerful Python rules engine for processing emails and routing them to different SQS queues based on flexible, user-defined logic. Perfect for automated email workflows, content filtering, and intelligent message routing.

## 🚀 Zato ESB Migration Available

InboundOrchestrator is now available as a **Zato ESB** implementation for enterprise-grade integration! The Zato migration provides:

- **Enterprise Service Bus Architecture**: Built-in service orchestration and message routing
- **Hot Deployment**: Deploy services without restarts
- **Web Admin Interface**: Configure and monitor services via web UI
- **Built-in Scheduler**: Integrated cron-like job scheduling
- **High Availability**: Easy horizontal scaling with clusters
- **Enhanced Security**: Built-in authentication, encryption, and API keys

📖 **See [Zato Migration Guide](docs/MIGRATION_GUIDE.md)** for migration instructions.

📋 **See [Migration Plan](ai/migration/migrationplan.md)** for detailed architecture and strategy.

## Features

- **Flexible Rule Engine**: Use the powerful `rule-engine` PyPI package to define custom rules with complex conditions
- **Email Processing**: Parse and analyze emails from various sources (raw content, files, EmailMessage objects)
- **SQS Integration**: Route emails to different Amazon SQS queues based on rule evaluation
- **Rich Email Model**: Comprehensive email data model with support for attachments, headers, and metadata
- **Configuration Management**: YAML/JSON configuration files for rules and queue definitions
- **Batch Processing**: Process multiple emails efficiently
- **Performance Monitoring**: Built-in statistics and health checking
- **Extensible**: Easy to extend with custom email parsing and routing logic
- **Zato ESB Support**: Enterprise-grade ESB implementation available

## Installation

### Prerequisites

- Python 3.8 or higher
- AWS account with SQS access (for production usage)
- AWS credentials configured (via AWS CLI, environment variables, or IAM roles)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install from Source

```bash
git clone https://github.com/ShelterCodeAi/InboundOrchestrator.git
cd InboundOrchestrator
pip install -r requirements.txt
```

## Quick Start

### 1. Basic Usage

```python
from inbound_orchestrator import InboundOrchestrator, EmailData
from datetime import datetime

# Initialize the orchestrator
orchestrator = InboundOrchestrator(
    config_file="config/sample_config.yaml",
    aws_region="us-east-1",
    default_queue="default"
)

# Create sample email data
email = EmailData(
    subject="Urgent: Server down",
    sender="admin@company.com",
    recipients=["support@company.com"],
    cc_recipients=[],
    bcc_recipients=[],
    body_text="The production server is down and needs immediate attention.",
    body_html=None,
    message_id="<urgent001@company.com>",
    received_date=datetime.now(),
    sent_date=datetime.now(),
    headers={"Priority": "High"},
    attachments=[],
    priority="urgent"
)

# Process the email (dry run - won't actually send to SQS)
result = orchestrator.process_email(email, dry_run=True)
print(f"Email routed to: {result['queue_name']}")
print(f"Matched rules: {result['matched_rules']}")
```

### 2. Configuration File Setup

Create a configuration file (`config/my_config.yaml`):

```yaml
# SQS Queue Configurations
queues:
  - name: high_priority
    url: https://sqs.us-east-1.amazonaws.com/123456789012/high-priority
    description: Queue for high priority emails

  - name: support
    url: https://sqs.us-east-1.amazonaws.com/123456789012/support
    description: Queue for support-related emails

  - name: default
    url: https://sqs.us-east-1.amazonaws.com/123456789012/default
    description: Default queue for all other emails

# Email Processing Rules
rules:
  - name: urgent_emails
    description: Route urgent emails to high priority queue
    condition: "priority == 'urgent' or contains(subject, 'URGENT')"
    action: high_priority
    priority: 100
    enabled: true

  - name: support_emails
    description: Route support emails based on subject keywords
    condition: "contains(subject, 'help') or contains(subject, 'support')"
    action: support
    priority: 80
    enabled: true
```

## Rule Engine Syntax

The rule engine uses a powerful expression language that supports:

### Basic Conditions
```python
# String matching
contains(subject, 'urgent')
starts_with(sender, 'admin@')
ends_with(sender_domain, '.gov')

# Exact matching  
priority == 'high'
sender == 'ceo@company.com'

# Numeric comparisons
attachment_count > 5
total_attachment_size > 10485760  # 10MB

# Boolean conditions
has_attachments
is_business_hours
is_weekend
```

### Advanced Conditions
```python
# Combining conditions
priority == 'urgent' and has_attachments
contains(subject, 'help') or contains(subject, 'support')

# Complex logic
(is_after_hours and priority == 'urgent') or sender_domain == 'vip-client.com'

# Attachment filtering
has_attachment_type('application/pdf')
attachment_count > 3 and total_attachment_size < 5242880  # 5MB
```

### Available Email Properties

| Property | Type | Description |
|----------|------|-------------|
| `subject` | string | Email subject line |
| `sender` | string | Sender email address |
| `sender_domain` | string | Domain part of sender email |
| `priority` | string | Email priority (normal, high, urgent, low) |
| `body_text` | string | Plain text email body |
| `body_html` | string | HTML email body |
| `recipient_count` | number | Number of recipients |
| `attachment_count` | number | Number of attachments |
| `total_attachment_size` | number | Total size of all attachments in bytes |
| `has_attachments` | boolean | Whether email has attachments |
| `is_business_hours` | boolean | Whether received during business hours |
| `is_weekend` | boolean | Whether received on weekend |
| `is_after_hours` | boolean | Whether received after business hours |

## Examples

### Processing Emails from Files

```python
# Process a single email file
result = orchestrator.process_email_from_file("emails/sample.eml")

# Process multiple email files
from inbound_orchestrator.utils.email_parser import EmailParser

emails = EmailParser.batch_parse_directory("emails/", pattern="*.eml")
results = orchestrator.process_emails_batch(emails, dry_run=True)
```

### Processing Emails from Postgres Database

InboundOrchestrator supports processing emails directly from a Postgres database with the `email_gmail` table schema:

```python
from inbound_orchestrator import InboundOrchestrator
from inbound_orchestrator.intake import PostgresEmailIntake

# Initialize the orchestrator
orchestrator = InboundOrchestrator(
    config_file="config/sample_config.yaml",
    default_queue="default"
)

# Connect to Postgres and process emails
with PostgresEmailIntake(
    host='localhost',
    port=5432,
    database='email_db',
    user='postgres',
    password='your_password',
    schema='email_messages'
) as postgres_intake:
    # Process all emails with email_id=33
    result = orchestrator.process_postgres_emails(
        postgres_intake=postgres_intake,
        email_id=33,
        dry_run=True  # Set to False to send to SQS
    )
    
    print(f"Processed {result['processed']} emails")
    print(f"Successful: {result['successful']}")
    print(f"Failed: {result['failed']}")
```

**Field Mapping from Postgres:**
- `subject` → EmailData.subject
- `body` → EmailData.body_text
- `from_address` → EmailData.sender
- `headers` (JSONB) → EmailData.headers, recipients, cc, bcc
- `email_message_id` → EmailData.message_id
- `time_received` → EmailData.received_date
- Date header → EmailData.sent_date (if available)

**Note:** RFC 2047 encoded text in subject/body fields is not decoded and may appear in encoded form.

See `examples/postgres_batch_example.py` for a complete working example.

### Custom Rule Creation

```python
from inbound_orchestrator.rules.rule_engine import EmailRule

# Create a custom rule
custom_rule = EmailRule(
    name="vip_customers",
    description="Route VIP customer emails to priority queue",
    condition="sender_domain == 'vip-client.com' or contains(sender, 'important@')",
    action="high_priority",
    priority=95,
    enabled=True,
    metadata={"category": "vip", "escalation": "immediate"}
)

# Add the rule to the orchestrator
orchestrator.add_rule(custom_rule)
```

### SQS Queue Management

```python
from inbound_orchestrator.sqs.sqs_client import SQSQueue

# Add a new queue
new_queue = SQSQueue(
    name="special_processing",
    url="https://sqs.us-east-1.amazonaws.com/123456789012/special",
    description="Queue for special processing requirements"
)

orchestrator.add_queue(new_queue)

# Test queue connectivity
health = orchestrator.health_check()
print(f"System health: {health['overall_status']}")
```

### Batch Processing

```python
# Process multiple emails efficiently
email_list = [email1, email2, email3, ...]
results = orchestrator.process_emails_batch(email_list, dry_run=False)

# Analyze results
successful = sum(1 for r in results if r['success'])
print(f"Successfully processed {successful}/{len(results)} emails")
```

## Configuration Examples

### Advanced Rule Examples

```yaml
rules:
  # Time-based routing
  - name: after_hours_urgent
    condition: "is_after_hours and (contains(subject, 'urgent') or priority == 'urgent')"
    action: after_hours_priority

  # Size-based routing  
  - name: large_attachments
    condition: "total_attachment_size > 10485760"  # 10MB
    action: large_file_processing

  # Domain-based routing
  - name: external_emails
    condition: "not contains(sender_domain, 'company.com')"
    action: external_review

  # Content analysis
  - name: security_alerts
    condition: "contains(subject, 'security') or contains(body_text, 'breach')"
    action: security_team
    priority: 95
```

### Queue Configuration Examples

```yaml
queues:
  # Standard queue
  - name: standard_processing
    url: https://sqs.us-east-1.amazonaws.com/123456789012/standard
    visibility_timeout: 30
    message_retention_period: 1209600  # 14 days

  # FIFO queue for ordered processing
  - name: ordered_processing.fifo
    url: https://sqs.us-east-1.amazonaws.com/123456789012/ordered.fifo
    visibility_timeout: 60
    message_retention_period: 345600  # 4 days

  # Dead letter queue
  - name: failed_processing
    url: https://sqs.us-east-1.amazonaws.com/123456789012/dlq
    description: Dead letter queue for failed messages
```

## Testing and Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python tests/test_email_model.py
python tests/test_rule_engine.py

# Run with coverage
python -m pytest tests/ --cov=inbound_orchestrator --cov-report=term-missing

# Run with coverage threshold (90% required)
python -m pytest tests/ --cov=inbound_orchestrator --cov-config=.coveragerc --cov-fail-under=90
```

### Coverage Requirements

This project maintains a **90% test coverage** requirement for the `inbound_orchestrator` package (excluding CLI and database-dependent modules). The coverage is automatically checked in CI.

**Excluded from coverage:**
- `cli.py` - Command-line interface (tested manually)
- `intake/postgres_email_intake.py` - Database-dependent (requires PostgreSQL)

**Current Coverage:**
- Overall: 91%+
- `sqs/sqs_client.py`: 95%
- `rules/rule_engine.py`: 93%
- `utils/config_loader.py`: 90%
- `orchestrator.py`: 89%
- `models/email_model.py`: 88%

### Running Tests Locally

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with coverage report
pytest tests/ --cov=inbound_orchestrator --cov-config=.coveragerc --cov-report=html

# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Continuous Integration

Tests run automatically on every push and pull request via GitHub Actions. The CI workflow:

1. Tests on Python 3.8, 3.9, 3.10, 3.11, and 3.12
2. Runs full test suite with pytest
3. Generates coverage report
4. **Fails if coverage drops below 90%**
5. Uploads coverage to Codecov (optional)

See `.github/workflows/python-ci.yml` for details.

### Running Examples

```bash
# Basic usage example
python examples/basic_usage.py

# Advanced usage example  
python examples/advanced_usage.py
```

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run linting (if available)
flake8 inbound_orchestrator/
black inbound_orchestrator/

# Run type checking (if mypy installed)
mypy inbound_orchestrator/
```

## Production Deployment

### AWS Configuration

1. **Set up SQS queues** in your AWS account
2. **Configure IAM permissions** for SQS access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sqs:SendMessage",
                "sqs:GetQueueAttributes",
                "sqs:SendMessageBatch"
            ],
            "Resource": "arn:aws:sqs:*:*:your-queue-name*"
        }
    ]
}
```

3. **Set environment variables**:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Monitoring and Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)

# Monitor performance
stats = orchestrator.get_statistics()
print(f"Processing rate: {stats['total_processed']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

## API Reference

### InboundOrchestrator

Main orchestrator class for email processing and routing.

#### Methods

- `process_email(email_data, dry_run=False)` - Process a single email
- `process_emails_batch(emails, dry_run=False)` - Process multiple emails
- `add_rule(rule)` - Add a processing rule
- `add_queue(queue)` - Add an SQS queue
- `get_statistics()` - Get processing statistics
- `health_check()` - Check system health

### EmailData

Email data model with comprehensive email properties.

#### Key Properties

- `subject`, `sender`, `recipients` - Basic email fields
- `attachments` - List of EmailAttachment objects
- `priority` - Email priority level
- `received_date`, `sent_date` - Timestamp information

### EmailRule

Rule definition for email processing logic.

#### Properties

- `name` - Unique rule identifier
- `condition` - Rule expression
- `action` - Action to take when rule matches
- `priority` - Rule priority (higher = evaluated first)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions:

- Create an issue in the GitHub repository
- Check the examples and documentation
- Review the test files for usage patterns

## Changelog

### Version 0.1.0
- Initial release
- Basic email processing and SQS routing
- Rule engine integration
- Configuration management
- Batch processing support
- Comprehensive examples and documentation

---

## Fulfillment Ticket Operational System

A comprehensive web-based system for managing fulfillment tickets, claims, and order operations with hierarchical organization and complete audit trails.

### Features

- **📁 Hierarchical Organization**: Browse tickets by Marketplace → Category → Folder
- **🎫 Ticket Management**: View and manage fulfillment tickets with detailed information
- **📊 Claims Tracking**: Monitor claims, payments, and order status
- **🏷️ Flexible Labeling**: Tag tickets with customizable labels
- **📝 Complete Audit Trail**: Track all changes with detailed action history
- **💰 Payment Integration**: Link tickets to sales orders, purchase orders, and payments
- **🔄 Status Tracking**: Monitor ticket and fulfillment states
- **🎨 Modern UI**: React-based interface with responsive design

### Quick Start - Fulfillment System

#### 1. Database Setup

The system uses PostgreSQL with Alembic for migrations.

**Create database:**
```bash
# Create PostgreSQL database
createdb fulfillment_db

# Or using psql
psql -U postgres
CREATE DATABASE fulfillment_db;
```

**Run migrations:**
```bash
# Set database URL (optional - overrides alembic.ini)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fulfillment_db"

# Run migrations
alembic upgrade head
```

**Database schema includes:**
- Marketplaces, Categories, Folders (hierarchical tree)
- Tickets with email metadata
- Labels (many-to-many with tickets)
- Claims for dispute tracking
- Sales Orders for payment mapping
- Users for authentication
- Actions for complete audit trail

See [Database Schema Documentation](docs/DATABASE_SCHEMA.md) for complete details.

#### 2. Start the API Backend

The FastAPI backend provides REST endpoints for the React UI.

```bash
# Install dependencies
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary

# Start the API server
cd api
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**API will be available at:**
- Base API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

See [API Documentation](docs/API_ENDPOINTS.md) for all endpoints.

#### 3. Start the React UI

The React application provides a modern web interface.

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev
```

**UI will be available at:**
- React app: `http://localhost:5173` (or `http://localhost:3000`)

**Key UI Components:**
- **FolderBrowser**: Navigate Marketplace → Category → Folder hierarchy
- **TicketGrid**: View tickets in card/grid layout with filtering
- **TicketDetailModal**: Full ticket details with claims and history

### Project Structure

```
InboundOrchestrator/
├── api/                          # FastAPI backend
│   ├── __init__.py
│   └── main.py                  # API endpoints with mock data
├── database/                     # Database models
│   ├── __init__.py
│   └── models.py                # SQLAlchemy ORM models
├── migrations/                   # Alembic migrations
│   ├── versions/
│   │   └── 48ea33bd6d47_initial_fulfillment_ticket_schema.py
│   ├── env.py
│   └── ...
├── ui/                          # React application
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── FolderBrowser.jsx
│   │   │   ├── TicketGrid.jsx
│   │   │   └── TicketDetailModal.jsx
│   │   ├── api/
│   │   │   └── client.js       # API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── docs/                        # Documentation
│   ├── DATABASE_SCHEMA.md      # Complete schema documentation
│   └── API_ENDPOINTS.md        # API endpoint reference
├── alembic.ini                 # Alembic configuration
└── README.md
```

### Database Entities

#### Core Hierarchy
- **Marketplaces**: Sales channels (Amazon, eBay, etc.)
- **Categories**: Organizational units per marketplace
- **Folders**: Hierarchical tree structure for tickets

#### Tickets & Related
- **Tickets**: Email-based fulfillment tickets
- **Labels**: Tags for categorizing tickets (many-to-many)
- **Claims**: Customer claims and disputes
- **Sales_Orders**: Links to sales, POs, and payments

#### System
- **Users**: User accounts and authentication
- **Actions**: Complete audit trail of changes

### Migration Management

**Create a new migration:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migrations:**
```bash
alembic downgrade -1
```

**Check current version:**
```bash
alembic current
```

**View migration history:**
```bash
alembic history
```

### Development Workflow

1. **Make database changes**: Modify `database/models.py`
2. **Generate migration**: `alembic revision --autogenerate -m "description"`
3. **Review migration**: Check generated file in `migrations/versions/`
4. **Apply migration**: `alembic upgrade head`
5. **Update API**: Modify `api/main.py` to use new schema
6. **Update UI**: Add/modify React components as needed

### Mock Data vs Real Data

**Current Implementation:**
- API uses **mock data** for demonstration
- All endpoints return static sample data
- No database connection required to run

**For Production:**
1. Update `api/main.py` to use SQLAlchemy ORM
2. Replace mock data with database queries
3. Add database session management
4. Implement authentication/authorization
5. Add input validation and error handling

### Environment Variables

```bash
# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/fulfillment_db

# API server
PORT=8000

# React app
VITE_API_URL=http://localhost:8000
```

### Testing

**Test the API:**
```bash
# Check health
curl http://localhost:8000/health

# Get marketplaces
curl http://localhost:8000/api/marketplaces

# Get tickets
curl http://localhost:8000/api/tickets
```

**Test the UI:**
1. Open `http://localhost:5173` in browser
2. Select a marketplace from the sidebar
3. Select a category
4. Select a folder
5. View tickets in the main area
6. Click a ticket to see details

### Screenshots

The UI provides:
- Clean, modern interface with gradient header
- Sidebar for hierarchical navigation
- Grid view of tickets with status badges
- Modal popups for detailed ticket information
- Color-coded labels and status indicators
- Complete action history timeline

### Roadmap

- [ ] Connect API to real database (replace mock data)
- [ ] Add user authentication and authorization
- [ ] Implement ticket creation and editing
- [ ] Add claim management features
- [ ] Implement search and advanced filtering
- [ ] Add email integration for ticket creation
- [ ] Create analytics dashboard
- [ ] Add file attachment support
- [ ] Implement notifications system
- [ ] Add bulk operations

### Contributing

Contributions are welcome! Please see the main contributing section above.

### Support

For questions or issues with the Fulfillment Ticket System:
- Check the [Database Schema Documentation](docs/DATABASE_SCHEMA.md)
- Review the [API Documentation](docs/API_ENDPOINTS.md)
- Create an issue in the GitHub repository

