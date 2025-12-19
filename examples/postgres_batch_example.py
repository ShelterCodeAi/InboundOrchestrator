#!/usr/bin/env python3
"""
Postgres batch processing example for InboundOrchestrator.

This example demonstrates how to:
1. Connect to a Postgres database
2. Query emails from the email_gmail table
3. Process emails through the rules engine
4. View processing results

Note: This example requires a Postgres database with the email_messages schema.
You'll need to update the database connection parameters below.
"""
import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator import InboundOrchestrator
from inbound_orchestrator.intake import PostgresEmailIntake

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main example function."""
    logger.info("Starting InboundOrchestrator Postgres batch processing example")
    
    # Configuration
    # UPDATE THESE PARAMETERS FOR YOUR ENVIRONMENT
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'email_db',
        'user': 'postgres',
        'password': 'your_password_here',  # Update this
        'schema': 'email_messages'
    }
    EMAIL_ID = 33  # The email_id to query for
    
    # 1. Initialize the orchestrator
    logger.info("Initializing InboundOrchestrator...")
    
    # Load configuration if available
    config_file = Path(__file__).parent.parent / "config" / "sample_config.yaml"
    
    try:
        orchestrator = InboundOrchestrator(
            config_file=config_file if config_file.exists() else None,
            aws_region='us-east-1',
            default_queue='default'
        )
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        logger.info("Continuing with default configuration...")
        orchestrator = InboundOrchestrator(default_queue='default')
    
    # 2. Connect to Postgres database
    logger.info(f"Connecting to Postgres database at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    
    try:
        with PostgresEmailIntake(**DB_CONFIG) as postgres_intake:
            logger.info("Database connection established")
            
            # Test the connection
            if not postgres_intake.test_connection():
                logger.error("Database connection test failed")
                return
            
            # 3. Query and process emails
            logger.info(f"\n{'='*60}")
            logger.info(f"PROCESSING EMAILS FROM POSTGRES (email_id={EMAIL_ID})")
            logger.info(f"{'='*60}")
            
            # Process emails (dry run mode - won't actually send to SQS)
            result = orchestrator.process_postgres_emails(
                postgres_intake=postgres_intake,
                email_id=EMAIL_ID,
                dry_run=True  # Set to False to actually send to SQS
            )
            
            # 4. Display results
            logger.info(f"\n{'='*60}")
            logger.info("PROCESSING RESULTS")
            logger.info(f"{'='*60}")
            logger.info(f"Email ID: {result['email_id']}")
            logger.info(f"Emails Found: {result['email_count']}")
            logger.info(f"Emails Processed: {result['processed']}")
            logger.info(f"Successful: {result['successful']}")
            logger.info(f"Failed: {result['failed']}")
            
            if result.get('error'):
                logger.error(f"Error: {result['error']}")
            
            # Display individual email results
            if result['results']:
                logger.info(f"\n{'='*60}")
                logger.info("INDIVIDUAL EMAIL RESULTS")
                logger.info(f"{'='*60}")
                
                for i, email_result in enumerate(result['results'], 1):
                    logger.info(f"\nEmail {i}:")
                    logger.info(f"  Subject: {email_result['subject']}")
                    logger.info(f"  Sender: {email_result['sender']}")
                    logger.info(f"  Matched Rules: {', '.join(email_result['matched_rules']) or 'None'}")
                    logger.info(f"  Target Queue: {email_result['queue_name']}")
                    logger.info(f"  Success: {email_result['success']}")
                    
                    if email_result.get('error'):
                        logger.error(f"  Error: {email_result['error']}")
            
            # 5. Show statistics
            logger.info(f"\n{'='*60}")
            logger.info("ORCHESTRATOR STATISTICS")
            logger.info(f"{'='*60}")
            
            stats = orchestrator.get_statistics()
            logger.info(f"Total Processed: {stats['total_processed']}")
            logger.info(f"Success Rate: {stats['success_rate']:.1f}%")
            logger.info(f"Rules Loaded: {stats['rules_count']}")
            logger.info(f"Queues Configured: {stats['queues_count']}")
            
            if stats['rule_matches']:
                logger.info("\nRule Match Counts:")
                for rule_name, count in stats['rule_matches'].items():
                    logger.info(f"  {rule_name}: {count}")
            
            if stats['queue_usage']:
                logger.info("\nQueue Usage:")
                for queue_name, count in stats['queue_usage'].items():
                    logger.info(f"  {queue_name}: {count}")
            
    except ImportError as e:
        logger.error("=" * 60)
        logger.error("POSTGRES DEPENDENCY MISSING")
        logger.error("=" * 60)
        logger.error(str(e))
        logger.error("\nTo use Postgres email intake, install psycopg2:")
        logger.error("  pip install psycopg2-binary")
        return
        
    except Exception as e:
        logger.error(f"Error during Postgres processing: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return
    
    logger.info("\nExample completed successfully!")
    logger.info("\nNote: This was a DRY RUN. No messages were actually sent to SQS.")
    logger.info("To send messages to SQS, set dry_run=False in process_postgres_emails()")


def example_with_custom_query():
    """
    Alternative example showing how to fetch emails directly
    and process them with the orchestrator.
    """
    logger.info("Running custom query example...")
    
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'email_db',
        'user': 'postgres',
        'password': 'your_password_here',
        'schema': 'email_messages'
    }
    
    try:
        # Initialize orchestrator
        orchestrator = InboundOrchestrator(default_queue='default')
        
        # Connect and fetch emails
        with PostgresEmailIntake(**DB_CONFIG) as postgres_intake:
            # Fetch emails directly
            emails = postgres_intake.fetch_emails_by_email_id(33)
            
            logger.info(f"Fetched {len(emails)} emails from database")
            
            # Process emails
            results = orchestrator.process_emails_batch(emails, dry_run=True)
            
            # Display results
            successful = sum(1 for r in results if r['success'])
            logger.info(f"Processed {len(results)} emails: {successful} successful")
            
            for i, result in enumerate(results, 1):
                logger.info(f"\nEmail {i}: {result['subject'][:50]}...")
                logger.info(f"  Queue: {result['queue_name']}")
                logger.info(f"  Rules: {', '.join(result['matched_rules'])}")
                
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    # Run main example
    main()
    
    # Uncomment to run custom query example
    # logger.info("\n" + "="*60)
    # example_with_custom_query()
