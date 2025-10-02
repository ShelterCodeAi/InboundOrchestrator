"""
Configuration loader for rules and SQS queue configurations.
"""
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from ..rules.rule_engine import EmailRule
from ..sqs.sqs_client import SQSQueue

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Configuration loader for rules and SQS queues.
    
    Supports loading from JSON and YAML files.
    """
    
    @staticmethod
    def load_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from a file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Dictionary containing the configuration
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    # Try to detect format by content
                    content = f.read()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return yaml.safe_load(content)
                        
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
            raise
    
    @staticmethod
    def save_file(data: Dict[str, Any], file_path: Union[str, Path], format: str = 'yaml') -> None:
        """
        Save configuration to a file.
        
        Args:
            data: Configuration data to save
            file_path: Path to save the configuration
            format: File format ('yaml' or 'json')
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'json':
                    json.dump(data, f, indent=2, default=str)
                else:
                    yaml.dump(data, f, default_flow_style=False, indent=2)
                    
            logger.info(f"Configuration saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {file_path}: {e}")
            raise
    
    @staticmethod
    def load_rules(file_path: Union[str, Path]) -> List[EmailRule]:
        """
        Load email rules from a configuration file.
        
        Args:
            file_path: Path to the rules configuration file
            
        Returns:
            List of EmailRule objects
        """
        config = ConfigLoader.load_file(file_path)
        rules_data = config.get('rules', [])
        
        rules = []
        for rule_data in rules_data:
            try:
                rule = EmailRule.from_dict(rule_data)
                rules.append(rule)
            except Exception as e:
                logger.error(f"Failed to load rule '{rule_data.get('name', 'unknown')}': {e}")
                continue
        
        logger.info(f"Loaded {len(rules)} rules from {file_path}")
        return rules
    
    @staticmethod
    def save_rules(rules: List[EmailRule], file_path: Union[str, Path], format: str = 'yaml') -> None:
        """
        Save email rules to a configuration file.
        
        Args:
            rules: List of EmailRule objects to save
            file_path: Path to save the configuration
            format: File format ('yaml' or 'json')
        """
        config = {
            'rules': [rule.to_dict() for rule in rules]
        }
        ConfigLoader.save_file(config, file_path, format)
    
    @staticmethod
    def load_queues(file_path: Union[str, Path]) -> List[SQSQueue]:
        """
        Load SQS queue configurations from a file.
        
        Args:
            file_path: Path to the queues configuration file
            
        Returns:
            List of SQSQueue objects
        """
        config = ConfigLoader.load_file(file_path)
        queues_data = config.get('queues', [])
        
        queues = []
        for queue_data in queues_data:
            try:
                queue = SQSQueue.from_dict(queue_data)
                queues.append(queue)
            except Exception as e:
                logger.error(f"Failed to load queue '{queue_data.get('name', 'unknown')}': {e}")
                continue
        
        logger.info(f"Loaded {len(queues)} queues from {file_path}")
        return queues
    
    @staticmethod
    def save_queues(queues: List[SQSQueue], file_path: Union[str, Path], format: str = 'yaml') -> None:
        """
        Save SQS queue configurations to a file.
        
        Args:
            queues: List of SQSQueue objects to save
            file_path: Path to save the configuration
            format: File format ('yaml' or 'json')
        """
        config = {
            'queues': [queue.to_dict() for queue in queues]
        }
        ConfigLoader.save_file(config, file_path, format)
    
    @staticmethod
    def load_full_config(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a complete configuration including rules, queues, and settings.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Dictionary with parsed configuration
        """
        config = ConfigLoader.load_file(file_path)
        
        # Parse rules
        rules = []
        if 'rules' in config:
            for rule_data in config['rules']:
                try:
                    rules.append(EmailRule.from_dict(rule_data))
                except Exception as e:
                    logger.error(f"Failed to load rule '{rule_data.get('name', 'unknown')}': {e}")
        
        # Parse queues
        queues = []
        if 'queues' in config:
            for queue_data in config['queues']:
                try:
                    queues.append(SQSQueue.from_dict(queue_data))
                except Exception as e:
                    logger.error(f"Failed to load queue '{queue_data.get('name', 'unknown')}': {e}")
        
        return {
            'rules': rules,
            'queues': queues,
            'settings': config.get('settings', {}),
            'aws_config': config.get('aws_config', {}),
            'logging_config': config.get('logging_config', {})
        }
    
    @staticmethod
    def create_sample_config(file_path: Union[str, Path], format: str = 'yaml') -> None:
        """
        Create a sample configuration file with example rules and queues.
        
        Args:
            file_path: Path to save the sample configuration
            format: File format ('yaml' or 'json')
        """
        sample_config = {
            'settings': {
                'default_queue': 'default',
                'max_retries': 3,
                'enable_logging': True
            },
            'aws_config': {
                'region': 'us-east-1',
                'profile': 'default'
            },
            'queues': [
                {
                    'name': 'high_priority',
                    'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/high-priority',
                    'description': 'Queue for high priority emails'
                },
                {
                    'name': 'support',
                    'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/support',
                    'description': 'Queue for support-related emails'
                },
                {
                    'name': 'sales',
                    'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/sales',
                    'description': 'Queue for sales inquiries'
                },
                {
                    'name': 'default',
                    'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/default',
                    'description': 'Default queue for all other emails'
                }
            ],
            'rules': [
                {
                    'name': 'urgent_emails',
                    'description': 'Route urgent emails to high priority queue',
                    'condition': "priority == 'urgent' or contains(subject, 'URGENT')",
                    'action': 'high_priority',
                    'priority': 100,
                    'enabled': True
                },
                {
                    'name': 'support_emails',
                    'description': 'Route support emails based on subject keywords',
                    'condition': "contains(subject, 'help') or contains(subject, 'support') or contains(subject, 'issue')",
                    'action': 'support',
                    'priority': 80,
                    'enabled': True
                },
                {
                    'name': 'sales_inquiries',
                    'description': 'Route sales inquiries to sales team',
                    'condition': "contains(subject, 'quote') or contains(subject, 'pricing') or contains(subject, 'sales')",
                    'action': 'sales',
                    'priority': 70,
                    'enabled': True
                },
                {
                    'name': 'large_attachments',
                    'description': 'Route emails with large attachments to special processing',
                    'condition': 'has_attachments and total_attachment_size > 10485760',  # 10MB
                    'action': 'high_priority',
                    'priority': 60,
                    'enabled': True
                },
                {
                    'name': 'after_hours_urgent',
                    'description': 'Route after-hours emails with urgent keywords',
                    'condition': "is_after_hours and (contains(subject, 'urgent') or contains(body_text, 'emergency'))",
                    'action': 'high_priority',
                    'priority': 90,
                    'enabled': True
                }
            ]
        }
        
        ConfigLoader.save_file(sample_config, file_path, format)
        logger.info(f"Sample configuration created at {file_path}")