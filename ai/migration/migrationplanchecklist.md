# Zato ESB Migration Plan Checklist

**Project:** InboundOrchestrator to Zato ESB Migration  
**Start Date:** 2026-01-16  
**Status:** In Progress  
**Document Version:** 1.0

---

## Overview

This checklist tracks the comprehensive migration from InboundOrchestrator to Zato ESB as detailed in [migrationplan.md](migrationplan.md). The migration follows a phased approach with incremental deployment to minimize risk.

---

## Phase 1: Infrastructure Setup (Week 1-2)

**Timeline:** Week 1-2  
**Status:** 🟡 Not Started

### Tasks

- [ ] **1.1** Install Zato via pip or system packages
  - **Status:** Not Started
  - **Assignee:** TBD
  - **Notes:**
  
- [ ] **1.2** Create Zato quickstart cluster
  - **Status:** Not Started
  - **Command:** `zato quickstart create ~/zato-inbound-orchestrator sqlite localhost 8000`
  - **Notes:**
  
- [ ] **1.3** Configure PostgreSQL as ODB (for production)
  - **Status:** Not Started
  - **Command:** `zato create odb postgresql "host=localhost dbname=zato_odb user=zato" --odb-password "password"`
  - **Notes:**
  
- [ ] **1.4** Configure Redis for Key-Value DB
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **1.5** Start Zato components
  - **Status:** Not Started
  - **Commands:**
    - `zato start ~/zato-inbound-orchestrator/server1`
    - `zato start ~/zato-inbound-orchestrator/web-admin`
  - **Notes:**
  
- [ ] **1.6** Verify web admin accessibility
  - **Status:** Not Started
  - **URL:** http://localhost:8183
  - **Notes:**
  
- [ ] **1.7** Run basic connectivity tests
  - **Status:** Not Started
  - **Notes:**

### Deliverables

- [ ] Zato cluster running and accessible
- [ ] Web admin accessible at http://localhost:8183
- [ ] Redis ODB configured and connected
- [ ] Basic connectivity tests passed
- [ ] Documentation of installation steps

### Issues Encountered

*None yet*

---

## Phase 2: Email Intake Migration (Week 3-4)

**Timeline:** Week 3-4  
**Status:** 🟡 Not Started

### Tasks

- [ ] **2.1** Create EmailParserService
  - **Status:** Not Started
  - **File:** `~/zato-inbound-orchestrator/server1/pickup/incoming/email_parser_service.py`
  - **Service Name:** `email.parser.parse-raw`
  - **Notes:**
  
- [ ] **2.2** Create PostgresEmailIntakeService
  - **Status:** Not Started
  - **File:** `~/zato-inbound-orchestrator/server1/pickup/incoming/postgres_intake_service.py`
  - **Service Name:** `email.intake.postgres-fetch`
  - **Notes:**
  
- [ ] **2.3** Configure PostgreSQL outgoing SQL connection
  - **Status:** Not Started
  - **Connection Name:** `email_db`
  - **Database:** email_db
  - **Notes:** Configure via Web Admin
  
- [ ] **2.4** Create scheduled job for email polling
  - **Status:** Not Started
  - **Job Name:** `postgres-email-intake`
  - **Service:** `email.intake.postgres-fetch`
  - **Interval:** 60 seconds
  - **Notes:** Configure via Web Admin Scheduler
  
- [ ] **2.5** Deploy services to pickup/incoming
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **2.6** Test email parser service
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **2.7** Test PostgreSQL intake service
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **2.8** Run integration tests
  - **Status:** Not Started
  - **Notes:**

### Deliverables

- [ ] Email parser service deployed and functional
- [ ] PostgreSQL intake service running
- [ ] Scheduled job fetching emails every 60 seconds
- [ ] Integration tests passing
- [ ] Service monitoring configured

### Issues Encountered

*None yet*

---

## Phase 3: Rule Engine Migration (Week 5-6)

**Timeline:** Week 5-6  
**Status:** 🟡 Not Started

### Tasks

- [ ] **3.1** Create RuleLoaderService
  - **Status:** Not Started
  - **File:** `~/zato-inbound-orchestrator/server1/pickup/incoming/rule_loader_service.py`
  - **Service Name:** `email.rules.load-from-config`
  - **Notes:**
  
- [ ] **3.2** Create RuleEvaluatorService
  - **Status:** Not Started
  - **File:** `~/zato-inbound-orchestrator/server1/pickup/incoming/rule_evaluator_service.py`
  - **Service Name:** `email.rules.evaluate`
  - **Notes:**
  
- [ ] **3.3** Migrate rule definitions to Zato KV DB format
  - **Status:** Not Started
  - **Notes:** Convert existing YAML rules to JSON format for KV DB
  
- [ ] **3.4** Implement safe rule evaluation context
  - **Status:** Not Started
  - **Notes:** Use restricted eval with controlled namespace
  
- [ ] **3.5** Test rule loading to KV DB
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **3.6** Test rule evaluation service
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **3.7** Create unit tests for rule evaluation
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **3.8** Create rule management API
  - **Status:** Not Started
  - **Notes:**

### Deliverables

- [ ] Rules stored in Zato Key-Value DB
- [ ] Rule evaluation service implemented
- [ ] Rule management API created
- [ ] Unit tests for rule evaluation passing
- [ ] Documentation of rule format

### Issues Encountered

*None yet*

---

## Phase 4: SQS Integration Migration (Week 7-8)

**Timeline:** Week 7-8  
**Status:** 🟡 Not Started

### Tasks

- [ ] **4.1** Create SQSOutboundService
  - **Status:** Not Started
  - **File:** `~/zato-inbound-orchestrator/server1/pickup/incoming/sqs_outbound_service.py`
  - **Service Name:** `email.outbound.sqs-send`
  - **Notes:**
  
- [ ] **4.2** Create SQSConfigLoaderService
  - **Status:** Not Started
  - **File:** `~/zato-inbound-orchestrator/server1/pickup/incoming/sqs_config_loader.py`
  - **Service Name:** `email.config.load-sqs-queues`
  - **Notes:**
  
- [ ] **4.3** Configure AWS credentials in Zato KV DB
  - **Status:** Not Started
  - **Key:** `aws.sqs.config`
  - **Notes:** Use IAM roles in production
  
- [ ] **4.4** Load SQS queue configurations to KV DB
  - **Status:** Not Started
  - **Key:** `aws.sqs.queues`
  - **Notes:**
  
- [ ] **4.5** Implement batch processing support
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **4.6** Test SQS message sending
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **4.7** Implement error handling and retries
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **4.8** Validate SQS integration tests
  - **Status:** Not Started
  - **Notes:**

### Deliverables

- [ ] SQS outbound service deployed
- [ ] Queue configurations loaded in KV DB
- [ ] Message sending tested and working
- [ ] Error handling implemented
- [ ] Batch processing functional

### Issues Encountered

*None yet*

---

## Phase 5: Orchestration Service (Week 9-10)

**Timeline:** Week 9-10  
**Status:** 🟡 Not Started

### Tasks

- [ ] **5.1** Create EmailOrchestratorService
  - **Status:** Not Started
  - **File:** `~/zato-inbound-orchestrator/server1/pickup/incoming/email_orchestrator_service.py`
  - **Service Name:** `email.orchestrator.process`
  - **Notes:**
  
- [ ] **5.2** Implement end-to-end flow
  - **Status:** Not Started
  - **Flow:** parsing → rule evaluation → SQS routing
  - **Notes:**
  
- [ ] **5.3** Add statistics tracking in Redis
  - **Status:** Not Started
  - **Keys:** `stats.email.*`
  - **Notes:**
  
- [ ] **5.4** Implement dry run mode
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **5.5** Add monitoring and logging
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **5.6** Test orchestration flow
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **5.7** Run performance benchmarks
  - **Status:** Not Started
  - **Target:** 1000+ emails/minute
  - **Notes:**
  
- [ ] **5.8** Validate end-to-end integration
  - **Status:** Not Started
  - **Notes:**

### Deliverables

- [ ] Orchestration service deployed
- [ ] End-to-end flow tested
- [ ] Statistics tracking working
- [ ] Performance benchmarks met
- [ ] Monitoring dashboards created

### Issues Encountered

*None yet*

---

## Phase 6: API Migration (Week 11-12)

**Timeline:** Week 11-12  
**Status:** 🟡 Not Started

### Tasks

- [ ] **6.1** Create MarketplacesAPIService
  - **Status:** Not Started
  - **File:** `~/zato-inbound-orchestrator/server1/pickup/incoming/api_marketplaces_service.py`
  - **Service Name:** `api.marketplaces.list`
  - **Notes:**
  
- [ ] **6.2** Configure REST channels in web admin
  - **Status:** Not Started
  - **Endpoint:** `/api/marketplaces`
  - **Notes:**
  
- [ ] **6.3** Migrate all FastAPI endpoints to Zato
  - **Status:** Not Started
  - **Notes:** List all endpoints from api/main.py
  
- [ ] **6.4** Configure PostgreSQL connection for fulfillment DB
  - **Status:** Not Started
  - **Connection Name:** `fulfillment_db`
  - **Notes:**
  
- [ ] **6.5** Update React UI to use Zato endpoints
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **6.6** Test API endpoint compatibility
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **6.7** Run API integration tests
  - **Status:** Not Started
  - **Notes:**
  
- [ ] **6.8** Verify React UI functionality
  - **Status:** Not Started
  - **Notes:**

### Deliverables

- [ ] All REST endpoints migrated to Zato
- [ ] API compatibility maintained
- [ ] React UI updated and functional
- [ ] API tests passing
- [ ] Documentation updated

### Issues Encountered

*None yet*

---

## Testing & Quality Assurance

**Status:** 🟡 Not Started

### Unit Testing

- [ ] **T.1** Create unit tests for EmailParserService
  - **Status:** Not Started
  - **Coverage Target:** 90%+
  
- [ ] **T.2** Create unit tests for RuleEvaluatorService
  - **Status:** Not Started
  - **Coverage Target:** 90%+
  
- [ ] **T.3** Create unit tests for SQSOutboundService
  - **Status:** Not Started
  - **Coverage Target:** 90%+
  
- [ ] **T.4** Create unit tests for EmailOrchestratorService
  - **Status:** Not Started
  - **Coverage Target:** 90%+
  
- [ ] **T.5** Create unit tests for API services
  - **Status:** Not Started
  - **Coverage Target:** 90%+

### Integration Testing

- [ ] **T.6** Test email intake to orchestration flow
  - **Status:** Not Started
  
- [ ] **T.7** Test rule evaluation with various email types
  - **Status:** Not Started
  
- [ ] **T.8** Test SQS integration with AWS
  - **Status:** Not Started
  
- [ ] **T.9** Test API endpoints with React UI
  - **Status:** Not Started
  
- [ ] **T.10** Run full end-to-end system test
  - **Status:** Not Started

### Backward Compatibility

- [ ] **T.11** Run existing test suite
  - **Status:** Not Started
  - **Command:** `pytest tests/ --cov=inbound_orchestrator --cov-fail-under=90 -v`
  
- [ ] **T.12** Verify all existing tests pass
  - **Status:** Not Started
  
- [ ] **T.13** Ensure coverage threshold is met (90%)
  - **Status:** Not Started

### Issues Encountered

*None yet*

---

## Documentation

**Status:** 🟡 Not Started

### Documentation Tasks

- [ ] **D.1** Update README.md with Zato migration info
  - **Status:** Not Started
  
- [ ] **D.2** Document Zato service architecture
  - **Status:** Not Started
  
- [ ] **D.3** Create deployment guide for Zato
  - **Status:** Not Started
  
- [ ] **D.4** Document configuration management
  - **Status:** Not Started
  
- [ ] **D.5** Create troubleshooting guide
  - **Status:** Not Started
  
- [ ] **D.6** Document API endpoint mappings
  - **Status:** Not Started
  
- [ ] **D.7** Update developer setup guide
  - **Status:** Not Started

### Issues Encountered

*None yet*

---

## Deployment & Rollout

**Status:** 🟡 Not Started

### Deployment Tasks

- [ ] **R.1** Set up production Zato cluster
  - **Status:** Not Started
  - **Servers:** 3+ for HA
  
- [ ] **R.2** Configure load balancer (HAProxy)
  - **Status:** Not Started
  
- [ ] **R.3** Set up monitoring (Grafana + Prometheus)
  - **Status:** Not Started
  
- [ ] **R.4** Configure CloudWatch integration
  - **Status:** Not Started
  
- [ ] **R.5** Run smoke tests in production
  - **Status:** Not Started
  
- [ ] **R.6** Gradual traffic shift (10% → 50% → 100%)
  - **Status:** Not Started
  
- [ ] **R.7** Monitor error rates and performance
  - **Status:** Not Started
  
- [ ] **R.8** Decommission legacy components
  - **Status:** Not Started

### Rollback Plan

- [ ] **R.9** Document rollback triggers
  - **Status:** Not Started
  - **Triggers:** Error rate > 5%, Response time > 50% degradation
  
- [ ] **R.10** Test rollback procedure
  - **Status:** Not Started

### Issues Encountered

*None yet*

---

## Progress Summary

### Overall Status

- **Total Tasks:** 80+
- **Completed:** 0
- **In Progress:** 0
- **Not Started:** 80+
- **Blocked:** 0

### Phase Status

| Phase | Status | Completion % |
|-------|--------|--------------|
| Phase 1: Infrastructure Setup | 🟡 Not Started | 0% |
| Phase 2: Email Intake Migration | 🟡 Not Started | 0% |
| Phase 3: Rule Engine Migration | 🟡 Not Started | 0% |
| Phase 4: SQS Integration Migration | 🟡 Not Started | 0% |
| Phase 5: Orchestration Service | 🟡 Not Started | 0% |
| Phase 6: API Migration | 🟡 Not Started | 0% |
| Testing & QA | 🟡 Not Started | 0% |
| Documentation | 🟡 Not Started | 0% |
| Deployment & Rollout | 🟡 Not Started | 0% |

### Timeline

- **Start Date:** 2026-01-16
- **Target Completion:** 12 weeks (2026-04-09)
- **Current Week:** 0
- **Days Elapsed:** 0
- **Days Remaining:** 84

---

## Risk Register

### Identified Risks

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|------------|
| R-001 | Zato learning curve for team | Medium | Training, POCs, documentation |
| R-002 | Custom SQS integration complexity | Medium | Reusable adapter library, thorough testing |
| R-003 | Migration effort underestimated | High | Phased approach, buffer time |
| R-004 | Performance degradation | High | Benchmarking, gradual rollout |
| R-005 | Data loss during migration | High | Parallel running, comprehensive testing |

---

## Notes and Observations

### General Notes

- Migration follows incremental hybrid approach
- All phases maintain backward compatibility
- Comprehensive testing at each phase
- Easy rollback mechanisms in place

### Key Decisions

- Using Zato for enterprise integration capabilities
- PostgreSQL for ODB in production (instead of SQLite)
- Redis for Key-Value DB and statistics
- boto3 for custom SQS integration
- Phased migration over "big bang" approach

### Dependencies

- Zato 3.2+ installation
- PostgreSQL database access
- Redis instance
- AWS SQS access
- Python 3.8+ environment

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-16 | 1.0 | Initial checklist created | Migration Team |

---

**Legend:**
- ✅ Completed
- 🟢 In Progress
- 🟡 Not Started
- 🔴 Blocked
- ⚠️ Issues Encountered
