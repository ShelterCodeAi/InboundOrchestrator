#!/usr/bin/env python3
"""
Command-line interface for InboundOrchestrator.
"""
import argparse
import sys
import logging
from pathlib import Path
import os

from .orchestrator import InboundOrchestrator
from .utils.config_loader import ConfigLoader
from .intake.postgres_email_intake import PostgresEmailIntake


def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_sample_config(args):
    """Create a sample configuration file."""
    output_file = Path(args.output)
    format_type = args.format or 'yaml'
    
    try:
        ConfigLoader.create_sample_config(output_file, format=format_type)
        print(f"Sample configuration created: {output_file}")
    except Exception as e:
        print(f"Error creating sample config: {e}")
        return 1
    
    return 0


def process_db_emails(args):
    """Process emails from PostgreSQL database."""
    try:
        # Initialize orchestrator
        orchestrator = InboundOrchestrator(
            config_file=args.config,
            aws_region=args.region,
            default_queue=args.default_queue
        )
        
        # Get database connection parameters from args or environment
        try:
            port = args.port if args.port is not None else int(os.environ.get('POSTGRES_PORT', '5432'))
        except ValueError:
            print(f"Error: Invalid port value in POSTGRES_PORT environment variable")
            return 1
        
        db_params = {
            'host': args.host or os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': port,
            'database': args.database or os.environ.get('POSTGRES_DB', 'email_db'),
            'user': args.user or os.environ.get('POSTGRES_USER', 'postgres'),
            'password': args.password or os.environ.get('POSTGRES_PASSWORD', ''),
            'schema': args.schema or os.environ.get('POSTGRES_SCHEMA', 'email_messages')
        }
        
        # Connect to database and fetch emails
        with PostgresEmailIntake(**db_params) as postgres_intake:
            # Test connection
            if not postgres_intake.test_connection():
                print("Error: Failed to connect to database")
                return 1
            
            print(f"Connected to database: {db_params['host']}:{db_params['port']}/{db_params['database']}")
            
            # Fetch emails based on email_id or all with limit
            if args.email_id:
                emails = postgres_intake.fetch_emails_by_email_id(args.email_id)
                email_count = len(emails)
                print(f"Fetched {email_count} email{'s' if email_count != 1 else ''} for email_id={args.email_id}")
            else:
                emails = postgres_intake.fetch_all_emails(limit=args.limit)
                email_count = len(emails)
                limit_msg = f" (limit={args.limit})" if args.limit else ""
                print(f"Fetched {email_count} email{'s' if email_count != 1 else ''} from database{limit_msg}")
            
            if not emails:
                print("No emails found matching criteria")
                return 1
            
            # Process emails through orchestrator
            results = orchestrator.process_emails_batch(emails, dry_run=args.dry_run)
            
            # Calculate statistics
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful
            
            # Print summary
            result_count = len(results)
            print(f"\nProcessed {result_count} email{'s' if result_count != 1 else ''}:")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            print(f"  Success Rate: {(successful/len(results)*100):.1f}%")
            
            # Show queue distribution
            queue_counts = {}
            for result in results:
                queue = result.get('queue_name', 'unknown')
                queue_counts[queue] = queue_counts.get(queue, 0) + 1
            
            print("\nQueue Distribution:")
            for queue, count in sorted(queue_counts.items()):
                print(f"  {queue}: {count}")
            
            # Show rule matches
            rule_matches = {}
            for result in results:
                for rule in result.get('matched_rules', []):
                    rule_matches[rule] = rule_matches.get(rule, 0) + 1
            
            if rule_matches:
                print("\nRule Matches:")
                for rule, count in sorted(rule_matches.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {rule}: {count}")
            
            if args.dry_run:
                print("\n(DRY RUN - No messages were actually sent to SQS)")
                
    except ImportError as e:
        print("Error: PostgreSQL support not available")
        print("Install psycopg2 with: pip install psycopg2-binary")
        return 1
    except Exception as e:
        print(f"Error processing database emails: {e}")
        logging.exception("Detailed error:")
        return 1
    
    return 0


def show_statistics(args):
    """Show orchestrator statistics."""
    try:
        orchestrator = InboundOrchestrator(
            config_file=args.config,
            aws_region=args.region,
            default_queue=args.default_queue
        )
        
        stats = orchestrator.get_statistics()
        
        print("InboundOrchestrator Statistics:")
        print(f"  Uptime: {stats['uptime_seconds']:.2f} seconds")
        print(f"  Total Processed: {stats['total_processed']}")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        print(f"  Configured Rules: {stats['rules_count']}")
        print(f"  Enabled Rules: {stats['enabled_rules_count']}")
        print(f"  Configured Queues: {stats['queues_count']}")
        
        if stats['rule_matches']:
            print("\nRule Match Statistics:")
            for rule, count in sorted(stats['rule_matches'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {rule}: {count}")
        
        if stats['queue_usage']:
            print("\nQueue Usage Statistics:")
            for queue, count in sorted(stats['queue_usage'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {queue}: {count}")
                
    except Exception as e:
        print(f"Error showing statistics: {e}")
        return 1
    
    return 0


def health_check(args):
    """Perform health check."""
    try:
        orchestrator = InboundOrchestrator(
            config_file=args.config,
            aws_region=args.region,
            default_queue=args.default_queue
        )
        
        health = orchestrator.health_check()
        
        print(f"Overall Status: {health['overall_status']}")
        print(f"Timestamp: {health['timestamp']}")
        
        print("\nComponent Status:")
        for component, status in health['components'].items():
            print(f"  {component}: {status['status']}")
            if 'error' in status:
                print(f"    Error: {status['error']}")
            if 'healthy_queues' in status:
                print(f"    Healthy Queues: {status['healthy_queues']}/{status['total_queues']}")
                
    except Exception as e:
        print(f"Error performing health check: {e}")
        return 1
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='InboundOrchestrator - Email processing and SQS routing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create sample configuration
  inbound-orchestrator create-config --output config.yaml
  
  # Process emails from database by email_id (dry run)
  inbound-orchestrator process-db --config config.yaml --email-id 33 --dry-run
  
  # Process all emails from database with limit
  inbound-orchestrator process-db --config config.yaml --limit 100
  
  # Process with custom database connection
  inbound-orchestrator process-db --host db.example.com --port 5432 --database email_db --user myuser --password mypass
  
  # Check system health
  inbound-orchestrator health --config config.yaml
  
  # Show statistics
  inbound-orchestrator stats --config config.yaml
        """
    )
    
    # Global arguments
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--config', '-c', type=Path, help='Configuration file path')
    parser.add_argument('--default-queue', default='default', help='Default queue name')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create config command
    config_parser = subparsers.add_parser('create-config', help='Create sample configuration file')
    config_parser.add_argument('--output', '-o', required=True, help='Output file path')
    config_parser.add_argument('--format', choices=['yaml', 'json'], help='Configuration format')
    
    # Process database command
    db_parser = subparsers.add_parser('process-db', help='Process emails from PostgreSQL database')
    db_parser.add_argument('--host', help='Database host (default: env POSTGRES_HOST or localhost)')
    db_parser.add_argument('--port', type=int, help='Database port (default: env POSTGRES_PORT or 5432)')
    db_parser.add_argument('--database', '--db', help='Database name (default: env POSTGRES_DB or email_db)')
    db_parser.add_argument('--user', help='Database user (default: env POSTGRES_USER or postgres)')
    db_parser.add_argument('--password', help='Database password (default: env POSTGRES_PASSWORD or empty)')
    db_parser.add_argument('--schema', help='Database schema (default: env POSTGRES_SCHEMA or email_messages)')
    db_parser.add_argument('--email-id', type=int, help='Process emails with specific email_id')
    db_parser.add_argument('--limit', type=int, help='Limit number of emails to fetch (when not using --email-id)')
    db_parser.add_argument('--dry-run', action='store_true', help='Perform dry run (no SQS sending)')
    
    # Statistics command
    subparsers.add_parser('stats', help='Show processing statistics')
    
    # Health check command
    subparsers.add_parser('health', help='Perform system health check')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate handler
    if args.command == 'create-config':
        return create_sample_config(args)
    elif args.command == 'process-db':
        return process_db_emails(args)
    elif args.command == 'stats':
        return show_statistics(args)
    elif args.command == 'health':
        return health_check(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())