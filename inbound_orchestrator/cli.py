#!/usr/bin/env python3
"""
Command-line interface for InboundOrchestrator.
"""
import argparse
import sys
import logging
from pathlib import Path

from .orchestrator import InboundOrchestrator
from .utils.email_parser import EmailParser
from .utils.config_loader import ConfigLoader


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


def process_email_file(args):
    """Process a single email file."""
    try:
        orchestrator = InboundOrchestrator(
            config_file=args.config,
            aws_region=args.region,
            default_queue=args.default_queue
        )
        
        result = orchestrator.process_email_from_file(
            args.email_file,
            dry_run=args.dry_run
        )
        
        print(f"Email processed successfully:")
        print(f"  Subject: {result.get('subject', 'N/A')}")
        print(f"  Sender: {result.get('sender', 'N/A')}")
        print(f"  Queue: {result.get('queue_name', 'N/A')}")
        print(f"  Matched Rules: {', '.join(result.get('matched_rules', []))}")
        print(f"  Success: {result.get('success', False)}")
        
        if result.get('error'):
            print(f"  Error: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"Error processing email: {e}")
        return 1
    
    return 0


def process_email_directory(args):
    """Process all email files in a directory."""
    try:
        orchestrator = InboundOrchestrator(
            config_file=args.config,
            aws_region=args.region,
            default_queue=args.default_queue
        )
        
        emails = EmailParser.batch_parse_directory(
            args.directory,
            pattern=args.pattern or "*.eml"
        )
        
        if not emails:
            print(f"No email files found in {args.directory}")
            return 1
        
        results = orchestrator.process_emails_batch(emails, dry_run=args.dry_run)
        
        successful = sum(1 for r in results if r['success'])
        print(f"Processed {len(results)} emails:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {len(results) - successful}")
        print(f"  Success Rate: {(successful/len(results)*100):.1f}%")
        
        # Show queue distribution
        queue_counts = {}
        for result in results:
            queue = result.get('queue_name', 'unknown')
            queue_counts[queue] = queue_counts.get(queue, 0) + 1
        
        print("\nQueue Distribution:")
        for queue, count in sorted(queue_counts.items()):
            print(f"  {queue}: {count}")
            
    except Exception as e:
        print(f"Error processing directory: {e}")
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
  
  # Process single email file
  inbound-orchestrator process-file --config config.yaml --email-file email.eml
  
  # Process directory of emails (dry run)
  inbound-orchestrator process-dir --config config.yaml --directory emails/ --dry-run
  
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
    
    # Process file command
    file_parser = subparsers.add_parser('process-file', help='Process single email file')
    file_parser.add_argument('--email-file', '-f', required=True, type=Path, help='Email file to process')
    file_parser.add_argument('--dry-run', action='store_true', help='Perform dry run (no SQS sending)')
    
    # Process directory command
    dir_parser = subparsers.add_parser('process-dir', help='Process directory of email files')
    dir_parser.add_argument('--directory', '-d', required=True, type=Path, help='Directory containing email files')
    dir_parser.add_argument('--pattern', '-p', help='File pattern to match (default: *.eml)')
    dir_parser.add_argument('--dry-run', action='store_true', help='Perform dry run (no SQS sending)')
    
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
    elif args.command == 'process-file':
        return process_email_file(args)
    elif args.command == 'process-dir':
        return process_email_directory(args)
    elif args.command == 'stats':
        return show_statistics(args)
    elif args.command == 'health':
        return health_check(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())