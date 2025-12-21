"""
Main InboundOrchestrator class that coordinates email processing and routing.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime

from .models.email_model import EmailData
from .rules.rule_engine import EmailRuleEngine, EmailRule
from .sqs.sqs_client import SQSClient, SQSQueue
from .utils.config_loader import ConfigLoader
from .utils.email_parser import EmailParser

logger = logging.getLogger(__name__)


class InboundOrchestrator:
    """
    Main orchestrator class for processing emails and routing to SQS queues.
    
    This class provides a high-level interface that:
    - Loads configuration for rules and queues
    - Processes emails through the rule engine
    - Routes emails to appropriate SQS queues
    - Provides monitoring and error handling
    """
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None,
                 aws_region: str = 'us-east-1',
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 default_queue: str = 'default'):
        """
        Initialize the InboundOrchestrator.
        
        Args:
            config_file: Path to configuration file (optional)
            aws_region: AWS region for SQS
            aws_access_key_id: AWS access key (optional, can use IAM roles)
            aws_secret_access_key: AWS secret key (optional, can use IAM roles)
            default_queue: Default queue name for unmatched emails
        """
        self.default_queue = default_queue
        self.config_file = Path(config_file) if config_file else None
        
        # Initialize components
        self.rule_engine = EmailRuleEngine()
        self.sqs_client = SQSClient(
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Statistics tracking
        self.stats = {
            'total_processed': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'rule_matches': {},
            'queue_usage': {},
            'start_time': datetime.now()
        }
        
        # Load configuration if provided
        if self.config_file and self.config_file.exists():
            self.load_configuration(self.config_file)
        
        logger.info("InboundOrchestrator initialized")
    
    def load_configuration(self, config_file: Union[str, Path]) -> None:
        """
        Load configuration from file.
        
        Args:
            config_file: Path to configuration file
        """
        try:
            config = ConfigLoader.load_full_config(config_file)
            
            # Load rules
            if config['rules']:
                self.rule_engine.add_rules(config['rules'])
                logger.info(f"Loaded {len(config['rules'])} rules")
            
            # Load queues
            if config['queues']:
                self.sqs_client.add_queues(config['queues'])
                logger.info(f"Loaded {len(config['queues'])} queues")
            
            # Update settings
            settings = config.get('settings', {})
            if 'default_queue' in settings:
                self.default_queue = settings['default_queue']
            
            self.config_file = Path(config_file)
            logger.info(f"Configuration loaded from {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
            raise
    
    def save_configuration(self, config_file: Optional[Union[str, Path]] = None,
                          format: str = 'yaml') -> None:
        """
        Save current configuration to file.
        
        Args:
            config_file: Path to save configuration (uses loaded file if not specified)
            format: File format ('yaml' or 'json')
        """
        if config_file is None:
            config_file = self.config_file
        
        if config_file is None:
            raise ValueError("No configuration file specified")
        
        config = {
            'settings': {
                'default_queue': self.default_queue
            },
            'rules': self.rule_engine.export_rules(),
            'queues': [queue.to_dict() for queue in self.sqs_client.list_queues()]
        }
        
        ConfigLoader.save_file(config, config_file, format)
        logger.info(f"Configuration saved to {config_file}")
    
    def add_rule(self, rule: Union[EmailRule, Dict[str, Any]]) -> None:
        """Add a rule to the engine."""
        if isinstance(rule, dict):
            rule = EmailRule.from_dict(rule)
        self.rule_engine.add_rule(rule)
    
    def add_queue(self, queue: Union[SQSQueue, Dict[str, Any]]) -> None:
        """Add a queue to the SQS client."""
        if isinstance(queue, dict):
            queue = SQSQueue.from_dict(queue)
        self.sqs_client.add_queue(queue)
    
    def process_email(self, email_data: EmailData,
                     dry_run: bool = False,
                     custom_attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a single email through the rule engine and route to appropriate queue.
        
        Args:
            email_data: EmailData object to process
            dry_run: If True, don't actually send to SQS, just return routing decision
            custom_attributes: Additional attributes to include with the message
            
        Returns:
            Dictionary containing processing results
        """
        start_time = datetime.now()
        result = {
            'email_id': email_data.message_id,
            'subject': email_data.subject[:100],
            'sender': email_data.sender,
            'processing_time': None,
            'matched_rules': [],
            'selected_action': None,
            'queue_name': None,
            'success': False,
            'error': None,
            'dry_run': dry_run
        }
        
        try:
            # Evaluate rules
            matching_rules = self.rule_engine.evaluate_email(email_data)
            result['matched_rules'] = [rule.name for rule in matching_rules]
            
            # Update rule match statistics
            for rule in matching_rules:
                self.stats['rule_matches'][rule.name] = self.stats['rule_matches'].get(rule.name, 0) + 1
            
            # Determine queue (first matching rule or default)
            if matching_rules:
                selected_rule = matching_rules[0]  # Highest priority
                queue_name = selected_rule.action
                result['selected_action'] = selected_rule.action
            else:
                queue_name = self.default_queue
                result['selected_action'] = 'default'
            
            result['queue_name'] = queue_name
            
            # Send to queue (unless dry run)
            if not dry_run:
                success = self.sqs_client.send_email_message(
                    email_data=email_data,
                    queue_name=queue_name,
                    additional_attributes=custom_attributes
                )
                
                if success:
                    self.stats['successful_routes'] += 1
                    self.stats['queue_usage'][queue_name] = self.stats['queue_usage'].get(queue_name, 0) + 1
                    result['success'] = True
                else:
                    self.stats['failed_routes'] += 1
                    result['error'] = f"Failed to send message to queue '{queue_name}'"
            else:
                result['success'] = True  # Dry run is always "successful"
            
            self.stats['total_processed'] += 1
            
        except Exception as e:
            error_msg = f"Error processing email: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
            result['success'] = False
            self.stats['failed_routes'] += 1
        
        finally:
            processing_time = (datetime.now() - start_time).total_seconds()
            result['processing_time'] = processing_time
        
        return result
    
    def process_emails_batch(self, emails: List[EmailData],
                           dry_run: bool = False,
                           parallel: bool = False) -> List[Dict[str, Any]]:
        """
        Process multiple emails in batch.
        
        Args:
            emails: List of EmailData objects to process
            dry_run: If True, don't actually send to SQS
            parallel: If True, process emails in parallel (future enhancement)
            
        Returns:
            List of processing results
        """
        results = []
        
        logger.info(f"Processing batch of {len(emails)} emails (dry_run={dry_run})")
        
        for i, email_data in enumerate(emails):
            try:
                result = self.process_email(email_data, dry_run=dry_run)
                results.append(result)
                
                if i % 100 == 0 and i > 0:
                    logger.info(f"Processed {i}/{len(emails)} emails")
                    
            except Exception as e:
                logger.error(f"Failed to process email {i}: {e}")
                results.append({
                    'email_id': getattr(email_data, 'message_id', f'email_{i}'),
                    'success': False,
                    'error': str(e),
                    'dry_run': dry_run
                })
        
        successful = sum(1 for r in results if r['success'])
        logger.info(f"Batch processing complete: {successful}/{len(emails)} successful")
        
        return results
    
    def process_email_from_file(self, file_path: Union[str, Path],
                              dry_run: bool = False) -> Dict[str, Any]:
        """
        Process an email from a file.
        
        Args:
            file_path: Path to email file
            dry_run: If True, don't actually send to SQS
            
        Returns:
            Processing result
        """
        email_data = EmailParser.from_file(file_path)
        return self.process_email(email_data, dry_run=dry_run)
    
    def process_email_from_raw(self, raw_email: Union[str, bytes],
                             dry_run: bool = False) -> Dict[str, Any]:
        """
        Process an email from raw content.
        
        Args:
            raw_email: Raw email content
            dry_run: If True, don't actually send to SQS
            
        Returns:
            Processing result
        """
        email_data = EmailParser.from_raw_email(raw_email)
        return self.process_email(email_data, dry_run=dry_run)
    
    def process_postgres_emails(self, 
                                postgres_intake,
                                email_id: int,
                                dry_run: bool = False) -> Dict[str, Any]:
        """
        Process emails from Postgres database through the rules engine.
        
        Args:
            postgres_intake: PostgresEmailIntake instance (connected)
            email_id: Email ID to filter by
            dry_run: If True, don't actually send to SQS
            
        Returns:
            Dictionary containing processing results with email count and individual results
        """
        logger.info(f"Processing Postgres emails for email_id={email_id}")
        
        try:
            # Fetch emails from database
            emails = postgres_intake.fetch_emails_by_email_id(email_id)
            
            if not emails:
                logger.warning(f"No emails found for email_id={email_id}")
                return {
                    'email_id': email_id,
                    'email_count': 0,
                    'processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'results': []
                }
            
            # Process emails through rules engine
            results = self.process_emails_batch(emails, dry_run=dry_run)
            
            # Summarize results
            successful = sum(1 for r in results if r['success'])
            
            summary = {
                'email_id': email_id,
                'email_count': len(emails),
                'processed': len(results),
                'successful': successful,
                'failed': len(results) - successful,
                'results': results
            }
            
            logger.info(f"Processed {len(emails)} Postgres emails: {successful} successful, {len(results) - successful} failed")
            
            return summary
            
        except Exception as e:
            error_msg = f"Error processing Postgres emails: {str(e)}"
            logger.error(error_msg)
            return {
                'email_id': email_id,
                'email_count': 0,
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'error': error_msg,
                'results': []
            }
    
    def test_rule(self, rule_condition: str, test_emails: List[EmailData]) -> Dict[str, Any]:
        """
        Test a rule condition against a set of emails.
        
        Args:
            rule_condition: Rule condition to test
            test_emails: List of EmailData objects to test against
            
        Returns:
            Test results including matches and errors
        """
        results = {
            'condition': rule_condition,
            'total_emails': len(test_emails),
            'matches': 0,
            'errors': 0,
            'matching_emails': [],
            'error_details': []
        }
        
        for email_data in test_emails:
            try:
                if self.rule_engine.test_rule(rule_condition, email_data):
                    results['matches'] += 1
                    results['matching_emails'].append({
                        'subject': email_data.subject,
                        'sender': email_data.sender,
                        'message_id': email_data.message_id
                    })
            except Exception as e:
                results['errors'] += 1
                results['error_details'].append(str(e))
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'uptime_seconds': uptime,
            'total_processed': self.stats['total_processed'],
            'successful_routes': self.stats['successful_routes'],
            'failed_routes': self.stats['failed_routes'],
            'success_rate': (self.stats['successful_routes'] / max(1, self.stats['total_processed'])) * 100,
            'rule_matches': self.stats['rule_matches'].copy(),
            'queue_usage': self.stats['queue_usage'].copy(),
            'rules_count': len(self.rule_engine.list_rules()),
            'queues_count': len(self.sqs_client.list_queues()),
            'enabled_rules_count': len(self.rule_engine.list_rules(enabled_only=True))
        }
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            'total_processed': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'rule_matches': {},
            'queue_usage': {},
            'start_time': datetime.now()
        }
        logger.info("Statistics reset")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components.
        
        Returns:
            Health check results
        """
        health = {
            'overall_status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check rule engine
            rules = self.rule_engine.list_rules(enabled_only=True)
            health['components']['rule_engine'] = {
                'status': 'healthy',
                'enabled_rules': len(rules),
                'total_rules': len(self.rule_engine.list_rules())
            }
        except Exception as e:
            health['components']['rule_engine'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['overall_status'] = 'unhealthy'
        
        try:
            # Check SQS queues
            queue_results = self.sqs_client.test_all_queues()
            healthy_queues = sum(1 for status in queue_results.values() if status)
            total_queues = len(queue_results)
            
            health['components']['sqs_client'] = {
                'status': 'healthy' if healthy_queues == total_queues else 'degraded',
                'healthy_queues': healthy_queues,
                'total_queues': total_queues,
                'queue_status': queue_results
            }
            
            if healthy_queues == 0:
                health['overall_status'] = 'unhealthy'
            elif healthy_queues < total_queues:
                health['overall_status'] = 'degraded'
                
        except Exception as e:
            health['components']['sqs_client'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['overall_status'] = 'unhealthy'
        
        return health
    
    def __str__(self) -> str:
        """String representation of the orchestrator."""
        stats = self.get_statistics()
        return (f"InboundOrchestrator("
                f"rules={stats['rules_count']}, "
                f"queues={stats['queues_count']}, "
                f"processed={stats['total_processed']})")
    
    def __repr__(self) -> str:
        """Detailed representation of the orchestrator."""
        return self.__str__()