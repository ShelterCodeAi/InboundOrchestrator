"""
Zato service for loading SQS queue configurations into the Key-Value DB.

This service stores AWS SQS queue configurations and credentials in Redis
for use by the SQS outbound service.
"""

from zato.server.service import Service
import json


class SQSConfigLoaderService(Service):
    """
    Load SQS queue configurations into KV DB.
    
    Input (optional):
        queues (dict): Dictionary of queue configurations
        aws_config (dict): AWS credentials and region
        
    If not provided, loads example configurations.
    """
    
    name = 'email.config.load-sqs-queues'
    
    def handle(self):
        # Get configurations from request or use examples
        queues = self.request.payload.get('queues') if self.request.payload else None
        aws_config = self.request.payload.get('aws_config') if self.request.payload else None
        
        # Default queue configurations (examples)
        if not queues:
            queues = {
                'high_priority': {
                    'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/high-priority',
                    'description': 'High priority emails'
                },
                'support': {
                    'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/support',
                    'description': 'Support emails'
                },
                'billing': {
                    'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/billing',
                    'description': 'Billing emails'
                },
                'default': {
                    'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/default',
                    'description': 'Default queue'
                }
            }
        
        # Default AWS configuration
        if not aws_config:
            aws_config = {
                'region': 'us-east-1',
                'access_key': '',  # Use IAM roles in production
                'secret_key': ''
            }
        
        try:
            # Store queues in KV DB
            self.kvdb.conn.set('aws.sqs.queues', json.dumps(queues))
            
            # Store AWS config
            self.kvdb.conn.set('aws.sqs.config', json.dumps(aws_config))
            
            self.logger.info(f"Loaded {len(queues)} SQS queue configurations")
            self.response.payload = {
                'success': True,
                'loaded': len(queues)
            }
            
        except Exception as e:
            self.logger.error(f"Error loading SQS configurations: {e}")
            self.response.payload = {
                'success': False,
                'error': str(e)
            }
