"""
Zato service for sending messages to AWS SQS queues.

This service wraps boto3 SQS client functionality and integrates it with
Zato's orchestration capabilities.
"""

from zato.server.service import Service
import boto3
import json
from botocore.exceptions import ClientError


class SQSOutboundService(Service):
    """
    Send messages to AWS SQS queues.
    
    Input:
        email_data (dict): Email data to send
        queue_name (str): Name of the queue to send to
        
    Output:
        success (bool): Whether the message was sent successfully
        message_id (str): SQS message ID (if successful)
        queue_name (str): Name of the queue used
    """
    
    name = 'email.outbound.sqs-send'
    
    def __init__(self):
        super().__init__()
        # Initialize SQS client (credentials from environment or IAM role)
        self.sqs_client = None
        self.queues = {}
    
    def before_handle(self):
        """Initialize SQS client before handling request"""
        if not self.sqs_client:
            try:
                # Get AWS credentials from Zato config store
                aws_config_json = self.kvdb.conn.get('aws.sqs.config')
                aws_config = json.loads(aws_config_json) if aws_config_json else {}
                
                # Initialize SQS client
                client_kwargs = {
                    'region_name': aws_config.get('region', 'us-east-1')
                }
                
                # Only add credentials if they are explicitly provided
                # Otherwise, boto3 will use environment variables or IAM role
                if aws_config.get('access_key') and aws_config.get('secret_key'):
                    client_kwargs['aws_access_key_id'] = aws_config['access_key']
                    client_kwargs['aws_secret_access_key'] = aws_config['secret_key']
                
                self.sqs_client = boto3.client('sqs', **client_kwargs)
                
                # Load queue URLs
                queues_json = self.kvdb.conn.get('aws.sqs.queues')
                self.queues = json.loads(queues_json) if queues_json else {}
                
            except Exception as e:
                self.logger.error(f"Error initializing SQS client: {e}")
                # Don't fail here, let handle() deal with it
    
    def handle(self):
        email_data = self.request.payload.get('email_data', {})
        queue_name = self.request.payload.get('queue_name', 'default')
        
        if not self.sqs_client:
            self.logger.error("SQS client not initialized")
            self.response.payload = {
                'success': False,
                'error': 'SQS client not initialized'
            }
            return
        
        queue_config = self.queues.get(queue_name)
        if not queue_config:
            self.logger.error(f"Queue '{queue_name}' not found in configuration")
            self.response.payload = {
                'success': False,
                'error': f"Queue '{queue_name}' not found"
            }
            return
        
        queue_url = queue_config.get('url')
        if not queue_url:
            self.logger.error(f"Queue '{queue_name}' has no URL configured")
            self.response.payload = {
                'success': False,
                'error': f"Queue '{queue_name}' has no URL"
            }
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
                        'StringValue': email_data.get('sender', '')
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
            self.response.payload = {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self.logger.error(f"Unexpected error sending to SQS: {e}")
            self.response.payload = {
                'success': False,
                'error': str(e)
            }
