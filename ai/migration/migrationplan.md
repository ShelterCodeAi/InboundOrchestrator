# InboundOrchestrator to Zato ESB Migration Plan

## Executive Summary

This document outlines a comprehensive plan to migrate the **InboundOrchestrator** system from a custom email processing and routing architecture to **Zato ESB** (Enterprise Service Bus), a Python-based integration platform. This migration will leverage Zato's built-in features for service orchestration, message routing, and enterprise integration patterns.

---

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Zato ESB Overview](#zato-esb-overview)
3. [Migration Strategy](#migration-strategy)
4. [Component Mapping](#component-mapping)
5. [Implementation Phases](#implementation-phases)
6. [Code Migration Examples](#code-migration-examples)
7. [Configuration Changes](#configuration-changes)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Plan](#deployment-plan)
10. [Rollback Strategy](#rollback-strategy)
11. [Benefits and Trade-offs](#benefits-and-trade-offs)

---

## 1. Current Architecture Analysis

### 1.1 Core Components

**Current System:**
- **InboundOrchestrator**:  Main coordinator for email processing
- **EmailRuleEngine**: Rule evaluation using `rule-engine` PyPI package
- **SQSClient**: AWS SQS integration for message routing
- **EmailParser**: Email parsing and data extraction
- **ConfigLoader**:  YAML/JSON configuration management
- **PostgresEmailIntake**: Database integration for email sources
- **FastAPI Backend**: REST API for fulfillment ticket system
- **React UI**: Web interface for ticket management

### 1.2 Key Features
- Rule-based email routing
- SQS queue integration
- Batch processing
- Database persistence (PostgreSQL)
- REST API endpoints
- Hierarchical ticket organization
- Audit trails and claims tracking

### 1.3 Technology Stack
```
- Python 3.8+
- boto3 (AWS SDK)
- rule-engine (rule evaluation)
- FastAPI (API framework)
- SQLAlchemy (ORM)
- Alembic (migrations)
- React + Vite (UI)
- PostgreSQL (database)
```

---

## 2. Zato ESB Overview

### 2.1 What is Zato? 

Zato is a Python-based ESB and backend application server that provides: 
- **Service-Oriented Architecture (SOA)** support
- **REST and SOAP** services
- **Message queuing** (AMQP, JMS, ZeroMQ, WebSphere MQ)
- **Database connectivity** (PostgreSQL, Oracle, MySQL, etc.)
- **Scheduling** capabilities
- **Web Admin GUI** for configuration
- **Hot-deployment** of services
- **Built-in security** (OAuth, JWT, Basic Auth, API Keys)

### 2.2 Zato Architecture

```
┌─────────────────────────────────────────────┐
│           Zato Web Admin                     │
│  (Configuration, Monitoring, Management)     │
└─────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────┐
│           Zato Scheduler                     │
│  (Cron jobs, Scheduled services)             │
└─────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────┐
│           Zato Server(s)                     │
│  (Service execution, Routing, Orchestration) │
└─────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────┐
│           Redis (ODB)                        │
│  (Operational Database)                      │
└─────────────────────────────────────────────┘
```

### 2.3 Key Zato Components

| Component | Purpose |
|-----------|---------|
| **Services** | Business logic implementation |
| **Channels** | Entry points (HTTP, AMQP, scheduled, etc.) |
| **Outgoing Connections** | External system integration |
| **Schedulers** | Time-based service invocation |
| **Security Definitions** | Authentication/authorization |
| **Key-Value DB** | Distributed configuration storage |

---

## 3. Migration Strategy

### 3.1 Migration Approach:  **Incremental Hybrid**

We recommend a **phased, incremental migration** rather than a "big bang" approach:

1. **Phase 1**:  Set up Zato infrastructure alongside existing system
2. **Phase 2**:  Migrate email intake and parsing to Zato services
3. **Phase 3**:  Migrate rule engine to Zato routing logic
4. **Phase 4**:  Migrate SQS integration to Zato outbound connections
5. **Phase 5**:  Migrate API backend to Zato REST services
6. **Phase 6**: Full cutover and decommission legacy components

### 3.2 Migration Principles

- ✅ **Maintain backward compatibility** during transition
- ✅ **Parallel running** of old and new systems
- ✅ **Gradual traffic shifting** (canary deployments)
- ✅ **Comprehensive testing** at each phase
- ✅ **Easy rollback** mechanisms

---

## 4. Component Mapping

### 4.1 Architecture Mapping

| Current Component | Zato Equivalent | Migration Strategy |
|-------------------|-----------------|-------------------|
| `InboundOrchestrator` | Zato Orchestration Service | Create master orchestration service |
| `EmailRuleEngine` | Zato Routing Logic + Key-Value DB | Store rules in KV DB, implement routing service |
| `SQSClient` | Zato AMQP/JMS Outbound Connection | Configure AWS SQS via AMQP or custom adapter |
| `EmailParser` | Zato Service + Python library | Wrap email parsing in Zato service |
| `ConfigLoader` | Zato Key-Value DB + Config Files | Migrate to Zato configuration system |
| `PostgresEmailIntake` | Zato SQL Connection + Scheduler | Use Zato SQL outconn + scheduled service |
| FastAPI REST endpoints | Zato REST Channels | Convert to Zato REST services |
| Statistics tracking | Zato Stats + Redis | Use built-in Zato statistics |

### 4.2 Data Flow Transformation

**Current Flow:**
```
Email Source → EmailParser → RuleEngine → SQSClient → AWS SQS
```

**Zato Flow:**
```
Email Source → Zato HTTP/Scheduler Channel → Email Parse Service → 
Rule Evaluation Service → SQS Outbound Service → AWS SQS
```

---

## 5. Implementation Phases

### Phase 1: Infrastructure Setup (Week 1-2)

**Goals:**
- Install and configure Zato server
- Set up Zato web admin
- Configure Redis ODB
- Create initial cluster

**Tasks:**
1. Install Zato via pip or system packages
   ```bash
   pip install zato
   ```

2. Create Zato quickstart cluster
   ```bash
   zato quickstart create ~/zato-inbound-orchestrator sqlite localhost 8000
   ```

3. Configure PostgreSQL as ODB (instead of SQLite for production)
   ```bash
   zato create odb postgresql "host=localhost dbname=zato_odb user=zato" --odb-password "password"
   ```

4. Start Zato components
   ```bash
   zato start ~/zato-inbound-orchestrator/server1
   zato start ~/zato-inbound-orchestrator/web-admin
   ```

**Deliverables:**
- ✅ Zato cluster running
- ✅ Web admin accessible
- ✅ Redis configured
- ✅ Basic connectivity tests passed

---

### Phase 2: Email Intake Migration (Week 3-4)

**Goals:**
- Migrate email parsing to Zato services
- Set up PostgreSQL connection for email intake
- Create scheduled jobs for email polling

**Implementation:**

#### 2.1 Create Email Parser Service

```python
# File: ~/zato-inbound-orchestrator/server1/pickup/incoming/email_parser_service.py

from zato.server. service import Service
from email import message_from_string
from datetime import datetime
import json

class EmailParserService(Service):
    """
    Zato service for parsing raw email content into structured data
    """
    
    name = 'email. parser. parse-raw'
    
    def handle(self):
        # Get raw email from request
        raw_email = self. request.payload. get('raw_email')
        
        # Parse email
        msg = message_from_string(raw_email)
        
        # Extract email data
        email_data = {
            'subject': msg.get('subject', ''),
            'sender': msg.get('from', ''),
            'recipients': msg. get('to', '').split(','),
            'cc_recipients': msg.get('cc', '').split(',') if msg.get('cc') else [],
            'body_text': self._get_body(msg),
            'headers': dict(msg.items()),
            'received_date': datetime.now().isoformat(),
            'message_id': msg.get('message-id', '')
        }
        
        # Return parsed data
        self.response.payload = email_data
    
    def _get_body(self, msg):
        """Extract email body text"""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            return msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        return ''
```

#### 2.2 Create PostgreSQL Email Intake Service

```python
# File: ~/zato-inbound-orchestrator/server1/pickup/incoming/postgres_intake_service.py

from zato. server.service import Service

class PostgresEmailIntakeService(Service):
    """
    Scheduled service to fetch emails from PostgreSQL database
    """
    
    name = 'email.intake.postgres-fetch'
    
    def handle(self):
        # Get SQL connection defined in web admin
        with self.outgoing. sql. get('email_db').session() as session:
            # Query emails from database
            query = """
                SELECT email_id, subject, body, from_address, headers, 
                       email_message_id, time_received
                FROM email_messages. email_gmail
                WHERE processed = false
                LIMIT 100
            """
            
            results = session.execute(query)
            
            for row in results: 
                # Create email payload
                email_payload = {
                    'email_id': row.email_id,
                    'subject': row.subject,
                    'body_text': row.body,
                    'sender': row.from_address,
                    'headers': row.headers,
                    'message_id': row.email_message_id,
                    'received_date': row.time_received. isoformat()
                }
                
                # Invoke email processing service
                self.invoke(
                    'email.orchestrator.process',
                    email_payload
                )
                
                # Mark as processed
                session.execute(
                    "UPDATE email_messages.email_gmail SET processed = true WHERE email_id = : id",
                    {'id': row.email_id}
                )
                session.commit()
```

#### 2.3 Configure Scheduler (via Web Admin)

1. Navigate to **Scheduler** → **Create a new job**
2. Configure: 
   - **Name**: `postgres-email-intake`
   - **Service**: `email.intake.postgres-fetch`
   - **Type**: Interval-based
   - **Interval**: 60 seconds
   - **Active**: Yes

**Deliverables:**
- ✅ Email parser service deployed
- ✅ PostgreSQL intake service running
- ✅ Scheduled job fetching emails
- ✅ Integration tests passing

---

### Phase 3: Rule Engine Migration (Week 5-6)

**Goals:**
- Migrate rule definitions to Zato Key-Value DB
- Implement rule evaluation service
- Create routing orchestration logic

**Implementation:**

#### 3.1 Store Rules in Zato Key-Value DB

```python
# File: ~/zato-inbound-orchestrator/server1/pickup/incoming/rule_loader_service.py

from zato.server.service import Service
import json

class RuleLoaderService(Service):
    """
    Load email routing rules from config into Key-Value DB
    """
    
    name = 'email.rules.load-from-config'
    
    def handle(self):
        # Example rules structure
        rules = [
            {
                'name':  'urgent_emails',
                'description': 'Route urgent emails to high priority queue',
                'condition': "priority == 'urgent' or 'URGENT' in subject",
                'action': 'high_priority',
                'priority': 100,
                'enabled': True
            },
            {
                'name': 'support_emails',
                'description': 'Route support emails based on subject keywords',
                'condition': "'help' in subject. lower() or 'support' in subject.lower()",
                'action': 'support',
                'priority': 80,
                'enabled': True
            }
        ]
        
        # Store rules in KV DB
        for rule in rules:
            key = f"email. rule.{rule['name']}"
            self.kvdb.conn.set(key, json.dumps(rule))
        
        self.logger.info(f"Loaded {len(rules)} rules into KV DB")
        self.response.payload = {'loaded': len(rules)}
```

#### 3.2 Create Rule Evaluation Service

```python
# File: ~/zato-inbound-orchestrator/server1/pickup/incoming/rule_evaluator_service.py

from zato.server.service import Service
import json

class RuleEvaluatorService(Service):
    """
    Evaluate email against routing rules
    """
    
    name = 'email.rules. evaluate'
    
    def handle(self):
        email_data = self.request.payload
        
        # Get all rules from KV DB
        rules = []
        for key in self.kvdb.conn.keys('email.rule.*'):
            rule_json = self.kvdb.conn. get(key)
            rule = json.loads(rule_json)
            if rule. get('enabled', False):
                rules.append(rule)
        
        # Sort by priority (highest first)
        rules.sort(key=lambda r: r. get('priority', 0), reverse=True)
        
        # Evaluate rules
        matched_rule = None
        for rule in rules:
            if self._evaluate_condition(rule['condition'], email_data):
                matched_rule = rule
                self.logger.info(f"Rule '{rule['name']}' matched")
                break
        
        # Return matching action or default
        if matched_rule: 
            self.response.payload = {
                'matched':  True,
                'rule_name': matched_rule['name'],
                'action': matched_rule['action']
            }
        else: 
            self.response.payload = {
                'matched': False,
                'action': 'default'
            }
    
    def _evaluate_condition(self, condition, email_data):
        """
        Evaluate rule condition against email data
        Uses Python eval with controlled namespace (security consideration)
        """
        try:
            # Create safe evaluation context
            context = {
                'subject': email_data.get('subject', ''),
                'sender': email_data.get('sender', ''),
                'sender_domain': email_data.get('sender', '').split('@')[-1],
                'priority': email_data.get('priority', 'normal'),
                'body_text': email_data.get('body_text', ''),
                'has_attachments': len(email_data.get('attachments', [])) > 0,
                'attachment_count': len(email_data.get('attachments', [])),
            }
            
            # Evaluate condition
            result = eval(condition, {"__builtins__": {}}, context)
            return bool(result)
            
        except Exception as e: 
            self.logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
```

**Deliverables:**
- ✅ Rules stored in Zato KV DB
- ✅ Rule evaluation service implemented
- ✅ Rule management API created
- ✅ Unit tests for rule evaluation

---

### Phase 4: SQS Integration Migration (Week 7-8)

**Goals:**
- Configure AWS SQS outbound connections in Zato
- Create SQS message sending service
- Implement batch processing

**Implementation:**

#### 4.1 Configure AWS SQS Connection (via Web Admin or API)

Since Zato doesn't have native SQS support, we'll create a custom outbound connection using boto3:

```python
# File: ~/zato-inbound-orchestrator/server1/pickup/incoming/sqs_outbound_service.py

from zato.server.service import Service
import boto3
import json
from botocore.exceptions import ClientError

class SQSOutboundService(Service):
    """
    Send messages to AWS SQS queues
    """
    
    name = 'email.outbound.sqs-send'
    
    def __init__(self):
        # Initialize SQS client (credentials from environment or IAM role)
        self.sqs_client = None
        self.queues = {}
    
    def before_handle(self):
        """Initialize SQS client before handling request"""
        if not self.sqs_client:
            # Get AWS credentials from Zato config store
            aws_config = json.loads(self.kvdb.conn.get('aws.sqs.config') or '{}')
            
            self.sqs_client = boto3.client(
                'sqs',
                region_name=aws_config.get('region', 'us-east-1'),
                aws_access_key_id=aws_config.get('access_key'),
                aws_secret_access_key=aws_config.get('secret_key')
            )
            
            # Load queue URLs
            queues_json = self.kvdb.conn. get('aws.sqs.queues')
            self.queues = json.loads(queues_json) if queues_json else {}
    
    def handle(self):
        email_data = self.request.payload. get('email_data')
        queue_name = self.request.payload.get('queue_name', 'default')
        
        queue_url = self.queues. get(queue_name, {}).get('url')
        
        if not queue_url:
            self.logger.error(f"Queue '{queue_name}' not found")
            self.response.payload = {'success': False, 'error': 'Queue not found'}
            return
        
        try:
            # Prepare message
            message_body = {
                'email_data': email_data,
                'timestamp': email_data.get('received_date'),
                'message_type': 'email_routing'
            }
            
            # Send to SQS
            response = self.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    'sender': {
                        'DataType': 'String',
                        'StringValue': email_data. get('sender', '')
                    },
                    'priority': {
                        'DataType': 'String',
                        'StringValue': email_data.get('priority', 'normal')
                    }
                }
            )
            
            self.logger.info(f"Sent email to queue '{queue_name}', MessageId: {response['MessageId']}")
            self.response.payload = {
                'success': True,
                'message_id': response['MessageId'],
                'queue_name': queue_name
            }
            
        except ClientError as e: 
            self.logger.error(f"Failed to send to SQS: {e}")
            self.response.payload = {'success': False, 'error':  str(e)}
```

#### 4.2 Queue Configuration Loader

```python
# File: ~/zato-inbound-orchestrator/server1/pickup/incoming/sqs_config_loader.py

from zato.server.service import Service
import json

class SQSConfigLoaderService(Service):
    """
    Load SQS queue configurations into KV DB
    """
    
    name = 'email.config.load-sqs-queues'
    
    def handle(self):
        queues = {
            'high_priority': {
                'url': 'https://sqs.us-east-1.amazonaws. com/123456789012/high-priority',
                'description': 'High priority emails'
            },
            'support': {
                'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/support',
                'description': 'Support emails'
            },
            'default': {
                'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/default',
                'description': 'Default queue'
            }
        }
        
        # Store in KV DB
        self.kvdb.conn.set('aws.sqs.queues', json.dumps(queues))
        
        # Store AWS config
        aws_config = {
            'region': 'us-east-1',
            'access_key':  '',  # Use IAM roles in production
            'secret_key':  ''
        }
        self.kvdb.conn.set('aws.sqs.config', json.dumps(aws_config))
        
        self.response.payload = {'loaded': len(queues)}
```

**Deliverables:**
- ✅ SQS outbound service deployed
- ✅ Queue configurations loaded
- ✅ Message sending tested
- ✅ Error handling implemented

---

### Phase 5: Orchestration Service (Week 9-10)

**Goals:**
- Create master orchestration service
- Implement end-to-end email processing flow
- Add statistics and monitoring

**Implementation:**

```python
# File: ~/zato-inbound-orchestrator/server1/pickup/incoming/email_orchestrator_service.py

from zato.server.service import Service

class EmailOrchestratorService(Service):
    """
    Master orchestration service for email processing
    Coordinates:  parsing → rule evaluation → SQS routing
    """
    
    name = 'email.orchestrator.process'
    
    def handle(self):
        email_data = self.request.payload
        dry_run = self.request.payload.get('dry_run', False)
        
        self.logger.info(f"Processing email: {email_data.get('subject', '')[:50]}")
        
        # Step 1: Evaluate routing rules
        rule_result = self.invoke(
            'email.rules.evaluate',
            email_data
        )
        
        matched = rule_result.get('matched', False)
        queue_name = rule_result.get('action', 'default')
        rule_name = rule_result.get('rule_name', 'none')
        
        # Step 2: Route to appropriate queue (unless dry run)
        if not dry_run:
            sqs_result = self.invoke(
                'email.outbound.sqs-send',
                {
                    'email_data': email_data,
                    'queue_name': queue_name
                }
            )
            
            success = sqs_result.get('success', False)
        else:
            success = True
            sqs_result = {'message_id': 'DRY_RUN'}
        
        # Step 3: Update statistics
        self._update_stats(queue_name, matched, success)
        
        # Return result
        self.response.payload = {
            'success': success,
            'queue_name': queue_name,
            'matched_rule': rule_name,
            'message_id': sqs_result.get('message_id'),
            'dry_run': dry_run
        }
    
    def _update_stats(self, queue_name, matched, success):
        """Update processing statistics in Redis"""
        # Increment counters
        self.kvdb. conn.incr('stats.email.total_processed')
        
        if success:
            self.kvdb.conn.incr('stats. email.successful_routes')
        else:
            self.kvdb.conn.incr('stats.email.failed_routes')
        
        if matched:
            self.kvdb.conn.incr(f'stats.email.queue. {queue_name}')
```

**Deliverables:**
- ✅ Orchestration service deployed
- ✅ End-to-end flow tested
- ✅ Statistics tracking working
- ✅ Performance benchmarks met

---

### Phase 6: API Migration (Week 11-12)

**Goals:**
- Migrate FastAPI endpoints to Zato REST services
- Preserve existing API contracts
- Update React UI to use Zato endpoints

**Implementation:**

#### 6.1 Create REST Channels in Zato

```python
# File: ~/zato-inbound-orchestrator/server1/pickup/incoming/api_marketplaces_service.py

from zato.server. service import Service

class MarketplacesAPIService(Service):
    """
    REST API for marketplaces
    """
    
    name = 'api.marketplaces. list'
    
    class SimpleIO:
        output_required = ('marketplaces',)
    
    def handle(self):
        # Get PostgreSQL connection
        with self.outgoing.sql.get('fulfillment_db').session() as session:
            query = "SELECT id, name, code, description, is_active FROM marketplaces"
            results = session.execute(query)
            
            marketplaces = []
            for row in results:
                marketplaces.append({
                    'id': row.id,
                    'name': row.name,
                    'code': row.code,
                    'description': row.description,
                    'is_active': row.is_active
                })
            
            self.response.payload. marketplaces = marketplaces
```

#### 6.2 Configure REST Channel (via Web Admin)

1. Navigate to **Connections** → **Channels** → **REST**
2. Create new channel:
   - **Name**: `/api/marketplaces`
   - **URL path**: `/api/marketplaces`
   - **Service**: `api.marketplaces.list`
   - **Method**: GET
   - **Data format**: JSON

Repeat for all API endpoints. 

**Deliverables:**
- ✅ All REST endpoints migrated
- ✅ API compatibility maintained
- ✅ React UI updated
- ✅ API tests passing

---

## 6. Code Migration Examples

### 6.1 Before/After:  Email Processing

**Before (Current):**
```python
# orchestrator. py
orchestrator = InboundOrchestrator(config_file="config.yaml")
result = orchestrator.process_email(email_data, dry_run=True)
```

**After (Zato):**
```python
# Via Zato service invocation
from zato.server.service import Service

class ClientService(Service):
    def handle(self):
        result = self.invoke('email.orchestrator.process', {
            'email_data': email_data,
            'dry_run': True
        })
```

### 6.2 Before/After: Rule Definition

**Before (YAML config):**
```yaml
rules:
  - name: urgent_emails
    condition: "priority == 'urgent' or contains(subject, 'URGENT')"
    action: high_priority
    priority: 100
```

**After (Zato KV DB):**
```python
# Stored in Redis via Zato KV DB
self.kvdb.conn.set('email.rule.urgent_emails', json.dumps({
    'name': 'urgent_emails',
    'condition': "priority == 'urgent' or 'URGENT' in subject",
    'action': 'high_priority',
    'priority': 100
}))
```

---

## 7. Configuration Changes

### 7.1 Environment Variables

**Current:**
```bash
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_DEFAULT_REGION=us-east-1
POSTGRES_HOST=localhost
POSTGRES_DB=email_db
```

**Zato:**
```bash
# Zato handles configuration through Web Admin and KV DB
# Environment variables only needed for initial setup
ZATO_WEB_ADMIN_PASSWORD=admin
ZATO_SERVER_NAME=server1
```

### 7.2 Database Configuration

**Migration from SQLAlchemy to Zato SQL Connections:**

1. Define outgoing SQL connection in Web Admin: 
   - **Name**: `email_db`
   - **Type**: PostgreSQL
   - **Host**: localhost
   - **Port**: 5432
   - **Database**: email_db
   - **Username**: postgres
   - **Password**:  ********

2. Use in services:
```python
with self.outgoing.sql.get('email_db').session() as session:
    results = session.execute(query)
```

---

## 8. Testing Strategy

### 8.1 Unit Testing

Zato provides testing utilities: 

```python
# test_email_parser.py
from zato.server.service. store import ServiceStore
from zato.server.service import Service

class TestEmailParserService: 
    def test_parse_raw_email(self):
        # Create test service instance
        service = ServiceStore().get_service('email.parser. parse-raw')
        
        # Mock request
        service.request. payload = {
            'raw_email': 'Subject: Test\nFrom: test@example.com\n\nTest body'
        }
        
        # Execute
        service.handle()
        
        # Assert
        assert service.response.payload['subject'] == 'Test'
        assert service.response.payload['sender'] == 'test@example. com'
```

### 8.2 Integration Testing

```python
# test_integration.py
def test_end_to_end_email_processing():
    # Invoke orchestrator service
    result = invoke_zato_service(
        'email.orchestrator.process',
        {'email_data': test_email, 'dry_run': True}
    )
    
    assert result['success'] == True
    assert result['queue_name'] in ['high_priority', 'support', 'default']
```

### 8.3 Performance Testing

- **Load testing** with 1000+ emails/minute
- **Latency monitoring** for service invocations
- **SQS throughput** validation

---

## 9. Deployment Plan

### 9.1 Production Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Zato LB    │────▶│  Zato Server │────▶│   Redis ODB  │
│  (HAProxy)   │     │   (Cluster)  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  PostgreSQL  │
                     │  (Email DB)  │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   AWS SQS    │
                     └──────────────┘
```

### 9.2 Deployment Steps

1. **Set up Zato cluster** (3+ servers for HA)
2. **Deploy services** via hot-deployment (copy to `pickup/incoming/`)
3. **Configure channels** via Web Admin
4. **Load initial data** (rules, queue configs)
5. **Run smoke tests**
6. **Enable monitoring** (Zato stats, CloudWatch)
7. **Gradual traffic shift** (10% → 50% → 100%)

### 9.3 Monitoring

- **Zato Web Admin**: Service statistics, error logs
- **Redis monitoring**: KV DB performance
- **CloudWatch**: SQS metrics
- **PostgreSQL**: Query performance
- **Custom dashboards**: Grafana + Prometheus

---

## 10.  Rollback Strategy

### 10.1 Rollback Triggers

- Service error rate > 5%
- Response time degradation > 50%
- Data integrity issues
- SQS delivery failures

### 10.2 Rollback Procedure

1. **Stop Zato scheduler** jobs
2. **Disable Zato REST channels**
3. **Re-enable legacy FastAPI** service
4. **Resume legacy orchestrator** processing
5. **Verify system recovery**
6. **Post-mortem analysis**

---

## 11. Benefits and Trade-offs

### 11.1 Benefits of Zato Migration

| Benefit | Description |
|---------|-------------|
| **Unified Management** | Single Web Admin for all configurations |
| **Hot Deployment** | Deploy services without restarts |
| **Built-in Monitoring** | Statistics and logging out-of-the-box |
| **Scalability** | Easy horizontal scaling with clusters |
| **Standards-Based** | SOA, REST, SOAP support |
| **Security** | Built-in auth, encryption, API keys |
| **Scheduler** | Integrated cron-like scheduling |
| **Resilience** | Automatic retries, circuit breakers |

### 11.2 Trade-offs

| Trade-off | Mitigation |
|-----------|------------|
| **Learning Curve** | Training, documentation, POCs |
| **Infrastructure Complexity** | Managed Zato hosting or containers |
| **Migration Effort** | Phased approach, parallel running |
| **Custom SQS Integration** | Build reusable SQS adapter library |
| **Testing Overhead** | Automated test suites, CI/CD |

### 11.3 Cost Analysis

| Component | Current | Zato | Change |
|-----------|---------|------|--------|
| Development | 1 FTE | 1 FTE | 0 |
| Infrastructure | EC2 + RDS | EC2 + RDS + Redis | +$50/mo |
| Maintenance | Medium | Low | -20% |
| Licensing | Free | Free (OSS) | 0 |

---

## 12. Conclusion

Migrating **InboundOrchestrator** to **Zato ESB** provides significant long-term benefits: 

✅ **Standardized integration patterns**  
✅ **Improved maintainability**  
✅ **Better scalability**  
✅ **Enhanced monitoring**  
✅ **Reduced operational complexity**

**Recommended Timeline:** 12 weeks for full migration with 2-week buffer for testing and optimization.

**Next Steps:**
1. **Stakeholder approval**
2. **Set up Zato POC** environment
3. **Phase 1 kickoff**:  Infrastructure setup
4. **Weekly progress reviews**
5. **Go-live planning**

---

## Appendix A:  Zato Installation Guide

### Quick Installation

```bash
# Install Zato via pip
pip install zato

# Create quickstart cluster
zato quickstart create ~/zato-cluster sqlite localhost 8000

# Start components
zato start ~/zato-cluster/server1
zato start ~/zato-cluster/web-admin

# Access Web Admin
# URL: http://localhost:8183
# Username: admin
# Password: (displayed during quickstart creation)
```

### Production Installation (Ubuntu/Debian)

```bash
# Add Zato repository
curl -s https://zato.io/repo/zato-3.2-stable-ubuntu-22.04.gpg.key | sudo apt-key add -
sudo add-apt-repository "deb http://repo.zato.io/zato/stable/3.2/ubuntu $(lsb_release -cs) main"

# Install Zato
sudo apt-get update
sudo apt-get install zato

# Create cluster with PostgreSQL ODB
zato create odb postgresql "host=localhost dbname=zato_odb user=zato" --odb-password "secure_password"
zato create cluster ~/zato-cluster
```

---

## Appendix B: Useful Zato Commands

```bash
# Service management
zato service invoke <service-name> --payload '{"key": "value"}'
zato service list

# Check server status
zato info ~/zato-cluster/server1

# View logs
tail -f ~/zato-cluster/server1/logs/server.log

# Hot-deploy service
cp my_service.py ~/zato-cluster/server1/pickup/incoming/
# Service auto-deploys within seconds

# Scheduler management
zato scheduler list
zato scheduler start <job-id>
zato scheduler stop <job-id>
```

---

## Appendix C: Resources

- **Zato Official Documentation**: https://zato.io/docs
- **Zato GitHub**:  https://github.com/zatosource/zato
- **Zato Forum**: https://forum.zato.io
- **Training Videos**: https://zato.io/support/training/index.html

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-16  
**Author:** ShelterCodeAi Migration Team  
**Status:** Draft for Review
