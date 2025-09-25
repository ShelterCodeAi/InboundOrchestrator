#!/usr/bin/env python3
"""
Advanced usage example for InboundOrchestrator.

This example demonstrates:
1. Custom rule creation and management
2. Email parsing from various sources
3. Batch processing
4. Configuration management
5. Performance monitoring
"""
import logging
import sys
import time
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator import InboundOrchestrator, EmailData, EmailRule
from inbound_orchestrator.sqs.sqs_client import SQSQueue
from inbound_orchestrator.utils.email_parser import EmailParser
from inbound_orchestrator.utils.config_loader import ConfigLoader

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Advanced usage demonstration."""
    logger.info("Starting InboundOrchestrator advanced usage example")
    
    # 1. Initialize orchestrator without config file
    orchestrator = InboundOrchestrator(
        aws_region='us-east-1',
        default_queue='default'
    )
    
    # 2. Programmatically add queues
    setup_queues(orchestrator)
    
    # 3. Create and add custom rules
    setup_custom_rules(orchestrator)
    
    # 4. Test individual rules
    test_custom_rules(orchestrator)
    
    # 5. Demonstrate batch processing
    batch_processing_demo(orchestrator)
    
    # 6. Configuration management
    configuration_management_demo(orchestrator)
    
    # 7. Performance monitoring
    performance_monitoring_demo(orchestrator)
    
    logger.info("Advanced example completed successfully!")


def setup_queues(orchestrator):
    """Set up SQS queues programmatically."""
    logger.info("\n" + "="*60)
    logger.info("SETTING UP QUEUES")
    logger.info("="*60)
    
    queues = [
        SQSQueue(
            name="critical",
            url="https://sqs.us-east-1.amazonaws.com/123456789012/critical",
            description="Critical issues requiring immediate attention"
        ),
        SQSQueue(
            name="business_hours",
            url="https://sqs.us-east-1.amazonaws.com/123456789012/business-hours",
            description="Standard business hours processing"
        ),
        SQSQueue(
            name="after_hours",
            url="https://sqs.us-east-1.amazonaws.com/123456789012/after-hours",
            description="After hours processing queue"
        ),
        SQSQueue(
            name="bulk_processing",
            url="https://sqs.us-east-1.amazonaws.com/123456789012/bulk",
            description="Bulk processing for newsletters and automated emails"
        ),
        SQSQueue(
            name="default",
            url="https://sqs.us-east-1.amazonaws.com/123456789012/default",
            description="Default processing queue"
        )
    ]
    
    for queue in queues:
        orchestrator.add_queue(queue)
        logger.info(f"Added queue: {queue.name}")
    
    logger.info(f"Total queues configured: {len(orchestrator.sqs_client.list_queues())}")


def setup_custom_rules(orchestrator):
    """Create and add custom rules."""
    logger.info("\n" + "="*60)
    logger.info("SETTING UP CUSTOM RULES")
    logger.info("="*60)
    
    rules = [
        EmailRule(
            name="critical_system_alerts",
            description="Route system alerts to critical queue",
            condition="contains(subject, 'ALERT') or contains(subject, 'CRITICAL') or contains(sender, 'monitoring@')",
            action="critical",
            priority=100,
            enabled=True,
            metadata={"category": "system", "escalation": "immediate"}
        ),
        
        EmailRule(
            name="business_hours_routing",
            description="Route to business hours queue during work hours",
            condition="is_business_hours and not contains(subject, 'urgent')",
            action="business_hours",
            priority=50,
            enabled=True,
            metadata={"category": "timing", "schedule": "business"}
        ),
        
        EmailRule(
            name="after_hours_routing",
            description="Route to after hours queue outside work hours",
            condition="is_after_hours and not contains(subject, 'urgent')",
            action="after_hours",
            priority=50,
            enabled=True,
            metadata={"category": "timing", "schedule": "after_hours"}
        ),
        
        EmailRule(
            name="bulk_email_detection",
            description="Detect and route bulk emails to special queue",
            condition="total_recipients > 50 or contains(sender, 'newsletter') or contains(subject, 'unsubscribe')",
            action="bulk_processing",
            priority=40,
            enabled=True,
            metadata={"category": "volume", "processing": "bulk"}
        ),
        
        EmailRule(
            name="vip_sender_detection",
            description="Detect VIP senders and prioritize",
            condition="contains(sender, 'vip@') or contains(sender, 'important@') or sender_domain == 'priority-client.com'",
            action="critical",
            priority=95,
            enabled=True,
            metadata={"category": "priority", "tier": "vip"}
        ),
        
        EmailRule(
            name="security_alerts",
            description="Route security-related emails to critical queue",
            condition="contains(subject, 'security') or contains(subject, 'breach') or contains(subject, 'violation')",
            action="critical",
            priority=98,
            enabled=True,
            metadata={"category": "security", "escalation": "immediate"}
        )
    ]
    
    for rule in rules:
        orchestrator.add_rule(rule)
        logger.info(f"Added rule: {rule.name} (priority: {rule.priority})")
    
    logger.info(f"Total rules configured: {len(orchestrator.rule_engine.list_rules())}")


def test_custom_rules(orchestrator):
    """Test individual rules with sample data."""
    logger.info("\n" + "="*60)
    logger.info("TESTING CUSTOM RULES")
    logger.info("="*60)
    
    # Create test scenarios
    test_emails = create_test_scenarios()
    
    # Test each scenario
    for scenario_name, email_data in test_emails.items():
        logger.info(f"\nTesting scenario: {scenario_name}")
        logger.info(f"Email: {email_data.subject} from {email_data.sender}")
        
        # Get matching rules
        matching_rules = orchestrator.rule_engine.evaluate_email(email_data)
        
        if matching_rules:
            top_rule = matching_rules[0]
            logger.info(f"Top matching rule: {top_rule.name} -> {top_rule.action}")
            logger.info(f"All matches: {[r.name for r in matching_rules]}")
        else:
            logger.info("No rules matched - would use default queue")


def batch_processing_demo(orchestrator):
    """Demonstrate batch processing capabilities."""
    logger.info("\n" + "="*60)
    logger.info("BATCH PROCESSING DEMO")
    logger.info("="*60)
    
    # Create a batch of emails
    batch_emails = []
    
    # Add various types of emails to the batch
    for i in range(20):
        if i % 5 == 0:
            # Critical alert
            email = EmailData(
                subject=f"CRITICAL ALERT: System {i} down",
                sender="monitoring@company.com",
                recipients=["ops@company.com"],
                cc_recipients=[],
                bcc_recipients=[],
                body_text=f"System {i} has gone down and requires immediate attention.",
                body_html=None,
                message_id=f"<alert{i}@monitoring.com>",
                received_date=datetime.now(),
                sent_date=datetime.now(),
                headers={"Priority": "High"},
                attachments=[],
                priority="urgent"
            )
        elif i % 3 == 0:
            # Bulk newsletter
            email = EmailData(
                subject=f"Newsletter #{i} - Weekly Updates",
                sender="newsletter@company.com",
                recipients=[f"subscriber{j}@example.com" for j in range(100)],  # 100 recipients
                cc_recipients=[],
                bcc_recipients=[],
                body_text=f"This is newsletter {i} with weekly updates.",
                body_html=f"<p>This is newsletter {i} with weekly updates.</p>",
                message_id=f"<newsletter{i}@company.com>",
                received_date=datetime.now(),
                sent_date=datetime.now(),
                headers={},
                attachments=[],
                priority="normal"
            )
        else:
            # Regular email
            email = EmailData(
                subject=f"Regular email #{i}",
                sender=f"user{i}@customer.com",
                recipients=["info@company.com"],
                cc_recipients=[],
                bcc_recipients=[],
                body_text=f"This is regular email number {i}.",
                body_html=None,
                message_id=f"<regular{i}@customer.com>",
                received_date=datetime.now(),
                sent_date=datetime.now(),
                headers={},
                attachments=[],
                priority="normal"
            )
        
        batch_emails.append(email)
    
    # Process batch
    logger.info(f"Processing batch of {len(batch_emails)} emails...")
    start_time = time.time()
    
    results = orchestrator.process_emails_batch(batch_emails, dry_run=True)
    
    processing_time = time.time() - start_time
    successful = sum(1 for r in results if r['success'])
    
    logger.info(f"Batch processing completed in {processing_time:.2f} seconds")
    logger.info(f"Success rate: {successful}/{len(results)} ({(successful/len(results)*100):.1f}%)")
    
    # Analyze routing decisions
    routing_summary = {}
    for result in results:
        queue = result['queue_name']
        routing_summary[queue] = routing_summary.get(queue, 0) + 1
    
    logger.info("Routing summary:")
    for queue, count in routing_summary.items():
        logger.info(f"  {queue}: {count} emails")


def configuration_management_demo(orchestrator):
    """Demonstrate configuration save/load functionality."""
    logger.info("\n" + "="*60)
    logger.info("CONFIGURATION MANAGEMENT DEMO")
    logger.info("="*60)
    
    # Save current configuration
    config_file = Path("/tmp/custom_config.yaml")
    orchestrator.save_configuration(config_file)
    logger.info(f"Configuration saved to {config_file}")
    
    # Create a new orchestrator and load the configuration
    new_orchestrator = InboundOrchestrator()
    new_orchestrator.load_configuration(config_file)
    logger.info("Configuration loaded into new orchestrator instance")
    
    # Verify the configuration was loaded correctly
    original_rules = len(orchestrator.rule_engine.list_rules())
    loaded_rules = len(new_orchestrator.rule_engine.list_rules())
    
    original_queues = len(orchestrator.sqs_client.list_queues())
    loaded_queues = len(new_orchestrator.sqs_client.list_queues())
    
    logger.info(f"Rules: Original={original_rules}, Loaded={loaded_rules}")
    logger.info(f"Queues: Original={original_queues}, Loaded={loaded_queues}")
    
    if original_rules == loaded_rules and original_queues == loaded_queues:
        logger.info("Configuration management test: PASSED")
    else:
        logger.warning("Configuration management test: FAILED")
    
    # Clean up
    config_file.unlink()


def performance_monitoring_demo(orchestrator):
    """Demonstrate performance monitoring capabilities."""
    logger.info("\n" + "="*60)
    logger.info("PERFORMANCE MONITORING DEMO")
    logger.info("="*60)
    
    # Reset statistics
    orchestrator.reset_statistics()
    
    # Process some emails to generate statistics
    test_emails = list(create_test_scenarios().values())
    
    logger.info("Processing emails for performance monitoring...")
    for email in test_emails:
        orchestrator.process_email(email, dry_run=True)
    
    # Get detailed statistics
    stats = orchestrator.get_statistics()
    
    logger.info("Performance Statistics:")
    logger.info(f"  Total Processed: {stats['total_processed']}")
    logger.info(f"  Success Rate: {stats['success_rate']:.1f}%")
    logger.info(f"  Uptime: {stats['uptime_seconds']:.2f} seconds")
    
    if stats['rule_matches']:
        logger.info("  Rule Match Statistics:")
        for rule_name, count in sorted(stats['rule_matches'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    {rule_name}: {count} matches")
    
    if stats['queue_usage']:
        logger.info("  Queue Usage Statistics:")
        for queue_name, count in sorted(stats['queue_usage'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    {queue_name}: {count} emails")
    
    # Health check
    health = orchestrator.health_check()
    logger.info(f"  System Health: {health['overall_status']}")


def create_test_scenarios():
    """Create various test scenarios for rule testing."""
    scenarios = {}
    
    # Scenario 1: Critical system alert
    scenarios["critical_alert"] = EmailData(
        subject="CRITICAL ALERT: Database server down",
        sender="monitoring@company.com",
        recipients=["ops@company.com"],
        cc_recipients=[],
        bcc_recipients=[],
        body_text="The main database server has crashed and needs immediate attention.",
        body_html=None,
        message_id="<critical001@monitoring.com>",
        received_date=datetime.now(),
        sent_date=datetime.now(),
        headers={"Priority": "High"},
        attachments=[],
        priority="urgent"
    )
    
    # Scenario 2: VIP customer email
    scenarios["vip_customer"] = EmailData(
        subject="Meeting request from VIP client",
        sender="ceo@priority-client.com",
        recipients=["sales@company.com"],
        cc_recipients=[],
        bcc_recipients=[],
        body_text="We would like to schedule a meeting to discuss our partnership.",
        body_html=None,
        message_id="<vip001@priority-client.com>",
        received_date=datetime.now(),
        sent_date=datetime.now(),
        headers={},
        attachments=[],
        priority="normal"
    )
    
    # Scenario 3: Security alert
    scenarios["security_alert"] = EmailData(
        subject="Security breach detected in system",
        sender="security@company.com",
        recipients=["admin@company.com"],
        cc_recipients=[],
        bcc_recipients=[],
        body_text="A potential security breach has been detected and requires investigation.",
        body_html=None,
        message_id="<security001@company.com>",
        received_date=datetime.now(),
        sent_date=datetime.now(),
        headers={},
        attachments=[],
        priority="urgent"
    )
    
    # Scenario 4: Bulk newsletter
    scenarios["bulk_newsletter"] = EmailData(
        subject="Weekly Newsletter - Unsubscribe available",
        sender="newsletter@company.com",
        recipients=[f"subscriber{i}@example.com" for i in range(100)],  # 100 recipients
        cc_recipients=[],
        bcc_recipients=[],
        body_text="This is our weekly newsletter. Click here to unsubscribe.",
        body_html="<p>This is our weekly newsletter. <a href='#'>Unsubscribe</a></p>",
        message_id="<newsletter001@company.com>",
        received_date=datetime.now(),
        sent_date=datetime.now(),
        headers={},
        attachments=[],
        priority="normal"
    )
    
    # Scenario 5: Regular business email
    scenarios["regular_business"] = EmailData(
        subject="Project update meeting",
        sender="manager@company.com",
        recipients=["team@company.com"],
        cc_recipients=[],
        bcc_recipients=[],
        body_text="Let's schedule a meeting to discuss the project updates.",
        body_html=None,
        message_id="<meeting001@company.com>",
        received_date=datetime.now().replace(hour=14),  # 2 PM (business hours)
        sent_date=datetime.now(),
        headers={},
        attachments=[],
        priority="normal"
    )
    
    return scenarios


if __name__ == "__main__":
    main()