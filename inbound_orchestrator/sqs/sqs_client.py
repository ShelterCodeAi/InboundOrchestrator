"""
SQS client for routing emails to different queues based on rule evaluation.
"""
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..models.email_model import EmailData

logger = logging.getLogger(__name__)


@dataclass
class SQSQueue:
    """Represents an SQS queue configuration."""
    name: str
    url: str
    description: str = ""
    max_message_size: int = 262144  # 256KB default
    visibility_timeout: int = 30
    message_retention_period: int = 1209600  # 14 days default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'max_message_size': self.max_message_size,
            'visibility_timeout': self.visibility_timeout,
            'message_retention_period': self.message_retention_period
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SQSQueue':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            url=data['url'],
            description=data.get('description', ''),
            max_message_size=data.get('max_message_size', 262144),
            visibility_timeout=data.get('visibility_timeout', 30),
            message_retention_period=data.get('message_retention_period', 1209600)
        )


class SQSClient:
    """
    SQS client for routing emails to different queues.
    
    Provides functionality to:
    - Configure multiple SQS queues
    - Send email messages to appropriate queues
    - Handle message formatting and error handling
    - Support both standard and FIFO queues
    """
    
    def __init__(self, region_name: str = 'us-east-1', aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None, aws_session_token: Optional[str] = None):
        """
        Initialize SQS client.
        
        Args:
            region_name: AWS region name
            aws_access_key_id: AWS access key (optional, can use IAM roles)
            aws_secret_access_key: AWS secret key (optional, can use IAM roles)
            aws_session_token: AWS session token (optional)
        """
        self.region_name = region_name
        self.queues: Dict[str, SQSQueue] = {}
        
        try:
            # Initialize boto3 SQS client
            session_kwargs = {'region_name': region_name}
            if aws_access_key_id and aws_secret_access_key:
                session_kwargs.update({
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key
                })
                if aws_session_token:
                    session_kwargs['aws_session_token'] = aws_session_token
            
            self.sqs = boto3.client('sqs', **session_kwargs)
            logger.info(f"Initialized SQS client for region: {region_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize SQS client: {e}")
            raise
    
    def add_queue(self, queue: SQSQueue) -> None:
        """
        Add a queue configuration.
        
        Args:
            queue: SQSQueue configuration to add
        """
        self.queues[queue.name] = queue
        logger.info(f"Added queue configuration: {queue.name} -> {queue.url}")
    
    def add_queues(self, queues: List[SQSQueue]) -> None:
        """Add multiple queue configurations."""
        for queue in queues:
            self.add_queue(queue)
    
    def remove_queue(self, queue_name: str) -> bool:
        """Remove a queue configuration."""
        if queue_name in self.queues:
            del self.queues[queue_name]
            logger.info(f"Removed queue configuration: {queue_name}")
            return True
        return False
    
    def get_queue(self, queue_name: str) -> Optional[SQSQueue]:
        """Get queue configuration by name."""
        return self.queues.get(queue_name)
    
    def list_queues(self) -> List[SQSQueue]:
        """List all configured queues."""
        return list(self.queues.values())
    
    def send_email_message(self, email_data: EmailData, queue_name: str, 
                          additional_attributes: Optional[Dict[str, Any]] = None,
                          message_group_id: Optional[str] = None,
                          message_deduplication_id: Optional[str] = None) -> bool:
        """
        Send an email message to the specified SQS queue.
        
        Args:
            email_data: EmailData object to send
            queue_name: Name of the queue to send to
            additional_attributes: Additional message attributes
            message_group_id: For FIFO queues
            message_deduplication_id: For FIFO queues
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        queue = self.queues.get(queue_name)
        if not queue:
            logger.error(f"Queue '{queue_name}' not found in configuration")
            return False
        
        try:
            # Prepare message body
            message_body = self._prepare_message_body(email_data, additional_attributes)
            
            # Prepare message attributes
            message_attributes = self._prepare_message_attributes(email_data)
            
            # Send message parameters
            send_params = {
                'QueueUrl': queue.url,
                'MessageBody': json.dumps(message_body),
                'MessageAttributes': message_attributes
            }
            
            # Add FIFO queue parameters if provided
            if message_group_id:
                send_params['MessageGroupId'] = message_group_id
            if message_deduplication_id:
                send_params['MessageDeduplicationId'] = message_deduplication_id
            
            # Send the message
            response = self.sqs.send_message(**send_params)
            
            message_id = response.get('MessageId')
            logger.info(f"Successfully sent email to queue '{queue_name}', MessageId: {message_id}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to send message to queue '{queue_name}': {error_code} - {error_message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message to queue '{queue_name}': {e}")
            return False
    
    def send_batch_messages(self, messages: List[tuple], queue_name: str) -> Dict[str, Any]:
        """
        Send multiple messages to a queue in a single batch.
        
        Args:
            messages: List of tuples (email_data, additional_attributes, message_group_id, deduplication_id)
            queue_name: Name of the queue to send to
            
        Returns:
            Dictionary with success/failure counts and details
        """
        queue = self.queues.get(queue_name)
        if not queue:
            logger.error(f"Queue '{queue_name}' not found in configuration")
            return {'success_count': 0, 'failure_count': len(messages), 'errors': ['Queue not found']}
        
        batch_size = 10  # SQS batch limit
        total_success = 0
        total_failures = 0
        errors = []
        
        # Process messages in batches
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            
            try:
                entries = []
                for idx, message_data in enumerate(batch):
                    email_data = message_data[0]
                    additional_attributes = message_data[1] if len(message_data) > 1 else None
                    message_group_id = message_data[2] if len(message_data) > 2 else None
                    deduplication_id = message_data[3] if len(message_data) > 3 else None
                    
                    message_body = self._prepare_message_body(email_data, additional_attributes)
                    message_attributes = self._prepare_message_attributes(email_data)
                    
                    entry = {
                        'Id': str(idx),
                        'MessageBody': json.dumps(message_body),
                        'MessageAttributes': message_attributes
                    }
                    
                    if message_group_id:
                        entry['MessageGroupId'] = message_group_id
                    if deduplication_id:
                        entry['MessageDeduplicationId'] = deduplication_id
                    
                    entries.append(entry)
                
                # Send batch
                response = self.sqs.send_message_batch(QueueUrl=queue.url, Entries=entries)
                
                successful = len(response.get('Successful', []))
                failed = len(response.get('Failed', []))
                
                total_success += successful
                total_failures += failed
                
                for failure in response.get('Failed', []):
                    errors.append(f"Message {failure['Id']}: {failure['Code']} - {failure['Message']}")
                
                logger.info(f"Batch sent to '{queue_name}': {successful} successful, {failed} failed")
                
            except Exception as e:
                total_failures += len(batch)
                errors.append(f"Batch error: {str(e)}")
                logger.error(f"Error sending batch to queue '{queue_name}': {e}")
        
        return {
            'success_count': total_success,
            'failure_count': total_failures,
            'errors': errors
        }
    
    def _prepare_message_body(self, email_data: EmailData, additional_attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare the message body for SQS.
        
        Args:
            email_data: EmailData object
            additional_attributes: Additional attributes to include
            
        Returns:
            Dictionary containing the message data
        """
        message_body = {
            'email_data': email_data.to_dict(),
            'timestamp': email_data.received_date.isoformat(),
            'message_type': 'email_routing'
        }
        
        if additional_attributes:
            message_body['additional_attributes'] = additional_attributes
        
        return message_body
    
    def _prepare_message_attributes(self, email_data: EmailData) -> Dict[str, Dict[str, str]]:
        """
        Prepare SQS message attributes.
        
        Args:
            email_data: EmailData object
            
        Returns:
            Dictionary of message attributes
        """
        attributes = {
            'sender': {
                'DataType': 'String',
                'StringValue': email_data.sender
            },
            'sender_domain': {
                'DataType': 'String',
                'StringValue': email_data.sender_domain or 'unknown'
            },
            'priority': {
                'DataType': 'String',
                'StringValue': email_data.priority
            },
            'has_attachments': {
                'DataType': 'String',
                'StringValue': str(len(email_data.attachments) > 0)
            },
            'attachment_count': {
                'DataType': 'Number',
                'StringValue': str(len(email_data.attachments))
            },
            'recipient_count': {
                'DataType': 'Number',
                'StringValue': str(len(email_data.recipients))
            }
        }
        
        # Add subject (truncated if too long)
        subject = email_data.subject[:256] if len(email_data.subject) > 256 else email_data.subject
        attributes['subject'] = {
            'DataType': 'String',
            'StringValue': subject
        }
        
        return attributes
    
    def test_queue_connection(self, queue_name: str) -> bool:
        """
        Test connection to a specific queue.
        
        Args:
            queue_name: Name of the queue to test
            
        Returns:
            True if connection is successful, False otherwise
        """
        queue = self.queues.get(queue_name)
        if not queue:
            logger.error(f"Queue '{queue_name}' not found in configuration")
            return False
        
        try:
            # Try to get queue attributes
            response = self.sqs.get_queue_attributes(
                QueueUrl=queue.url,
                AttributeNames=['QueueArn']
            )
            logger.info(f"Successfully connected to queue '{queue_name}'")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to connect to queue '{queue_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing queue '{queue_name}': {e}")
            return False
    
    def test_all_queues(self) -> Dict[str, bool]:
        """Test connections to all configured queues."""
        results = {}
        for queue_name in self.queues:
            results[queue_name] = self.test_queue_connection(queue_name)
        return results
    
    def get_queue_attributes(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get attributes for a specific queue."""
        queue = self.queues.get(queue_name)
        if not queue:
            return None
        
        try:
            response = self.sqs.get_queue_attributes(
                QueueUrl=queue.url,
                AttributeNames=['All']
            )
            return response.get('Attributes', {})
        except Exception as e:
            logger.error(f"Failed to get attributes for queue '{queue_name}': {e}")
            return None