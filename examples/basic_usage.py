#!/usr/bin/env python3
"""
Basic usage example for InboundOrchestrator.

This example demonstrates how to:
1. Initialize the orchestrator
2. Load configuration
3. Process sample emails
4. View processing results
"""
import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator import InboundOrchestrator, EmailData
from inbound_orchestrator.utils.email_parser import EmailParser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main example function."""
    logger.info("Starting InboundOrchestrator basic usage example")
    
    # 1. Initialize the orchestrator
    # Note: For this example, we'll use a sample config file
    config_file = Path(__file__).parent.parent / "config" / "sample_config.yaml"
    
    try:
        orchestrator = InboundOrchestrator(
            config_file=config_file,
            aws_region='us-east-1',
            default_queue='default'
        )
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        logger.info("This is expected if AWS credentials are not configured")
        logger.info("Continuing with dry run mode...")
        
        # Initialize without SQS for demonstration
        orchestrator = InboundOrchestrator(default_queue='default')
    
    # 2. Create some sample email data for testing
    sample_emails = create_sample_emails()
    
    # 3. Process emails in dry run mode (won't actually send to SQS)
    logger.info("\n" + "="*60)
    logger.info("PROCESSING SAMPLE EMAILS (DRY RUN)")
    logger.info("="*60)
    
    results = []
    for i, email_data in enumerate(sample_emails, 1):
        logger.info(f"\nProcessing Email {i}: {email_data.subject}")
        logger.info(f"From: {email_data.sender}")
        
        result = orchestrator.process_email(email_data, dry_run=True)
        results.append(result)
        
        logger.info(f"Matched Rules: {', '.join(result['matched_rules']) or 'None'}")
        logger.info(f"Selected Action: {result['selected_action']}")
        logger.info(f"Target Queue: {result['queue_name']}")
        logger.info(f"Success: {result['success']}")
        
        if result['error']:
            logger.error(f"Error: {result['error']}")
    
    # 4. Show statistics
    logger.info("\n" + "="*60)
    logger.info("PROCESSING STATISTICS")
    logger.info("="*60)
    
    stats = orchestrator.get_statistics()
    logger.info(f"Total Processed: {stats['total_processed']}")
    logger.info(f"Success Rate: {stats['success_rate']:.1f}%")
    logger.info(f"Rules Loaded: {stats['rules_count']}")
    logger.info(f"Queues Configured: {stats['queues_count']}")
    
    if stats['rule_matches']:
        logger.info("\nRule Match Counts:")
        for rule_name, count in stats['rule_matches'].items():
            logger.info(f"  {rule_name}: {count}")
    
    # 5. Demonstrate rule testing
    logger.info("\n" + "="*60)
    logger.info("RULE TESTING EXAMPLE")
    logger.info("="*60)
    
    test_condition = "contains(subject, 'urgent') or priority == 'high'"
    test_results = orchestrator.test_rule(test_condition, sample_emails)
    
    logger.info(f"Test Condition: {test_condition}")
    logger.info(f"Total Emails Tested: {test_results['total_emails']}")
    logger.info(f"Matches Found: {test_results['matches']}")
    logger.info(f"Errors: {test_results['errors']}")
    
    if test_results['matching_emails']:
        logger.info("Matching Emails:")
        for email in test_results['matching_emails']:
            logger.info(f"  - {email['subject']} (from {email['sender']})")
    
    # 6. Health check
    logger.info("\n" + "="*60)
    logger.info("HEALTH CHECK")
    logger.info("="*60)
    
    health = orchestrator.health_check()
    logger.info(f"Overall Status: {health['overall_status']}")
    
    for component, status in health['components'].items():
        logger.info(f"{component}: {status['status']}")
        if 'error' in status:
            logger.warning(f"  Error: {status['error']}")
    
    logger.info("\nExample completed successfully!")


def create_sample_emails():
    """Create sample email data for demonstration."""
    from datetime import datetime
    from inbound_orchestrator.models.email_model import EmailAttachment
    
    emails = []
    
    # 1. Urgent email
    emails.append(EmailData(
        subject="URGENT: Server Down - Need Immediate Help",
        sender="admin@company.com",
        recipients=["support@company.com"],
        cc_recipients=[],
        bcc_recipients=[],
        body_text="Our production server is down and we need immediate assistance!",
        body_html=None,
        message_id="<urgent001@company.com>",
        received_date=datetime.now(),
        sent_date=datetime.now(),
        headers={"Priority": "High"},
        attachments=[],
        priority="urgent"
    ))
    
    # 2. Sales inquiry
    emails.append(EmailData(
        subject="Request for pricing information",
        sender="customer@external.com",
        recipients=["info@company.com"],
        cc_recipients=[],
        bcc_recipients=[],
        body_text="Hello, I would like to get a quote for your enterprise solution.",
        body_html=None,
        message_id="<sales001@external.com>",
        received_date=datetime.now(),
        sent_date=datetime.now(),
        headers={},
        attachments=[],
        priority="normal"
    ))
    
    # 3. Support request with attachment
    attachment = EmailAttachment(
        filename="error_log.txt",
        content_type="text/plain",
        size=5000,
        content=b"Error log content here..."
    )
    
    emails.append(EmailData(
        subject="Login issue - please help",
        sender="user@customer.com",
        recipients=["support@company.com"],
        cc_recipients=[],
        bcc_recipients=[],
        body_text="I'm having trouble logging into my account. Error log attached.",
        body_html=None,
        message_id="<support001@customer.com>",
        received_date=datetime.now(),
        sent_date=datetime.now(),
        headers={},
        attachments=[attachment],
        priority="normal"
    ))
    
    # 4. Marketing newsletter
    emails.append(EmailData(
        subject="Monthly Newsletter - New Features",
        sender="noreply@company.com",
        recipients=["subscriber@customer.com"],
        cc_recipients=[],
        bcc_recipients=[],
        body_text="Check out our new features in this month's newsletter!",
        body_html="<p>Check out our new features!</p>",
        message_id="<newsletter001@company.com>",
        received_date=datetime.now(),
        sent_date=datetime.now(),
        headers={},
        attachments=[],
        priority="normal"
    ))
    
    # 5. Large attachment email
    large_attachment = EmailAttachment(
        filename="presentation.pdf",
        content_type="application/pdf",
        size=15_000_000,  # 15MB
        content=None  # Don't include actual content for demo
    )
    
    emails.append(EmailData(
        subject="Q4 Presentation for Review",
        sender="manager@company.com",
        recipients=["team@company.com"],
        cc_recipients=[],
        bcc_recipients=[],
        body_text="Please review the attached Q4 presentation.",
        body_html=None,
        message_id="<presentation001@company.com>",
        received_date=datetime.now(),
        sent_date=datetime.now(),
        headers={},
        attachments=[large_attachment],
        priority="normal"
    ))
    
    return emails


if __name__ == "__main__":
    main()