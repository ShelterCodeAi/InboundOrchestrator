#!/usr/bin/env python3
"""
Tests for the SQSClient class.
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator.sqs.sqs_client import SQSClient, SQSQueue
from inbound_orchestrator.models.email_model import EmailData


class TestSQSQueue(unittest.TestCase):
    """Test cases for SQSQueue class."""
    
    def test_queue_creation(self):
        """Test queue creation."""
        queue = SQSQueue(
            name="test_queue",
            url="https://sqs.us-east-1.amazonaws.com/123456789012/test",
            description="Test queue"
        )
        
        self.assertEqual(queue.name, "test_queue")
        self.assertEqual(queue.url, "https://sqs.us-east-1.amazonaws.com/123456789012/test")
        self.assertEqual(queue.description, "Test queue")
    
    def test_queue_to_dict(self):
        """Test queue to_dict conversion."""
        queue = SQSQueue(
            name="test_queue",
            url="https://sqs.us-east-1.amazonaws.com/123456789012/test",
            description="Test queue",
            max_message_size=262144,
            visibility_timeout=30
        )
        
        queue_dict = queue.to_dict()
        self.assertEqual(queue_dict['name'], "test_queue")
        self.assertEqual(queue_dict['max_message_size'], 262144)
    
    def test_queue_from_dict(self):
        """Test queue from_dict creation."""
        queue_dict = {
            'name': 'from_dict_queue',
            'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/dict',
            'description': 'Dictionary queue'
        }
        
        queue = SQSQueue.from_dict(queue_dict)
        self.assertEqual(queue.name, 'from_dict_queue')
        self.assertEqual(queue.url, 'https://sqs.us-east-1.amazonaws.com/123456789012/dict')


class TestSQSClient(unittest.TestCase):
    """Test cases for SQSClient class."""
    
    @patch('inbound_orchestrator.sqs.sqs_client.boto3')
    def setUp(self, mock_boto3):
        """Set up test fixtures."""
        self.mock_sqs = MagicMock()
        mock_boto3.client.return_value = self.mock_sqs
        
        self.client = SQSClient(region_name='us-east-1')
        
        self.test_queue = SQSQueue(
            name="test_queue",
            url="https://sqs.us-east-1.amazonaws.com/123456789012/test",
            description="Test queue"
        )
        
        self.sample_email = EmailData(
            subject="Test Email",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="Test body",
            body_html=None,
            message_id="<test@example.com>",
            received_date=datetime.now(),
            sent_date=datetime.now(),
            headers={},
            attachments=[],
            priority="normal"
        )
    
    @patch('inbound_orchestrator.sqs.sqs_client.boto3')
    def test_initialization(self, mock_boto3):
        """Test SQS client initialization."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        
        client = SQSClient(region_name='us-west-2')
        self.assertEqual(client.region_name, 'us-west-2')
    
    @patch('inbound_orchestrator.sqs.sqs_client.boto3')
    def test_initialization_with_credentials(self, mock_boto3):
        """Test SQS client initialization with credentials."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        
        client = SQSClient(
            region_name='us-east-1',
            aws_access_key_id='test_key',
            aws_secret_access_key='test_secret'
        )
        self.assertIsNotNone(client.sqs)
    
    @patch('inbound_orchestrator.sqs.sqs_client.boto3')
    def test_initialization_with_session_token(self, mock_boto3):
        """Test SQS client initialization with session token."""
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        
        client = SQSClient(
            region_name='us-east-1',
            aws_access_key_id='test_key',
            aws_secret_access_key='test_secret',
            aws_session_token='test_token'
        )
        self.assertIsNotNone(client.sqs)
    
    def test_add_queue(self):
        """Test adding a queue."""
        self.client.add_queue(self.test_queue)
        self.assertEqual(len(self.client.list_queues()), 1)
    
    def test_add_queues(self):
        """Test adding multiple queues."""
        queues = [
            self.test_queue,
            SQSQueue(name="queue2", url="https://test.com/queue2", description="Queue 2")
        ]
        self.client.add_queues(queues)
        self.assertEqual(len(self.client.list_queues()), 2)
    
    def test_remove_queue(self):
        """Test removing a queue."""
        self.client.add_queue(self.test_queue)
        result = self.client.remove_queue("test_queue")
        self.assertTrue(result)
        self.assertEqual(len(self.client.list_queues()), 0)
    
    def test_remove_nonexistent_queue(self):
        """Test removing a non-existent queue."""
        result = self.client.remove_queue("nonexistent")
        self.assertFalse(result)
    
    def test_get_queue(self):
        """Test getting a queue by name."""
        self.client.add_queue(self.test_queue)
        queue = self.client.get_queue("test_queue")
        self.assertIsNotNone(queue)
        self.assertEqual(queue.name, "test_queue")
    
    def test_get_nonexistent_queue(self):
        """Test getting a non-existent queue."""
        queue = self.client.get_queue("nonexistent")
        self.assertIsNone(queue)
    
    def test_list_queues(self):
        """Test listing all queues."""
        self.client.add_queue(self.test_queue)
        queues = self.client.list_queues()
        self.assertEqual(len(queues), 1)
        self.assertEqual(queues[0].name, "test_queue")
    
    def test_send_email_message_success(self):
        """Test sending email message successfully."""
        self.client.add_queue(self.test_queue)
        self.mock_sqs.send_message.return_value = {'MessageId': 'test-message-id'}
        
        result = self.client.send_email_message(
            email_data=self.sample_email,
            queue_name="test_queue"
        )
        
        self.assertTrue(result)
        self.mock_sqs.send_message.assert_called_once()
    
    def test_send_email_message_queue_not_found(self):
        """Test sending email to non-existent queue."""
        result = self.client.send_email_message(
            email_data=self.sample_email,
            queue_name="nonexistent"
        )
        
        self.assertFalse(result)
    
    def test_send_email_message_with_fifo_params(self):
        """Test sending email with FIFO queue parameters."""
        self.client.add_queue(self.test_queue)
        self.mock_sqs.send_message.return_value = {'MessageId': 'test-message-id'}
        
        result = self.client.send_email_message(
            email_data=self.sample_email,
            queue_name="test_queue",
            message_group_id="group1",
            message_deduplication_id="dedup1"
        )
        
        self.assertTrue(result)
    
    def test_send_email_message_client_error(self):
        """Test handling of client error when sending message."""
        from botocore.exceptions import ClientError
        
        self.client.add_queue(self.test_queue)
        self.mock_sqs.send_message.side_effect = ClientError(
            {'Error': {'Code': 'TestError', 'Message': 'Test error message'}},
            'send_message'
        )
        
        result = self.client.send_email_message(
            email_data=self.sample_email,
            queue_name="test_queue"
        )
        
        self.assertFalse(result)
    
    def test_send_batch_messages_success(self):
        """Test batch sending of messages."""
        self.client.add_queue(self.test_queue)
        self.mock_sqs.send_message_batch.return_value = {
            'Successful': [{'Id': '0'}, {'Id': '1'}],
            'Failed': []
        }
        
        messages = [
            (self.sample_email, None, None, None),
            (self.sample_email, None, None, None)
        ]
        
        result = self.client.send_batch_messages(messages, "test_queue")
        
        self.assertEqual(result['success_count'], 2)
        self.assertEqual(result['failure_count'], 0)
    
    def test_send_batch_messages_queue_not_found(self):
        """Test batch sending to non-existent queue."""
        messages = [(self.sample_email, None, None, None)]
        result = self.client.send_batch_messages(messages, "nonexistent")
        
        self.assertEqual(result['success_count'], 0)
        self.assertEqual(result['failure_count'], 1)
    
    def test_send_batch_messages_with_failures(self):
        """Test batch sending with some failures."""
        self.client.add_queue(self.test_queue)
        self.mock_sqs.send_message_batch.return_value = {
            'Successful': [{'Id': '0'}],
            'Failed': [{'Id': '1', 'Code': 'TestError', 'Message': 'Test failure'}]
        }
        
        messages = [
            (self.sample_email, None, None, None),
            (self.sample_email, None, None, None)
        ]
        
        result = self.client.send_batch_messages(messages, "test_queue")
        
        self.assertEqual(result['success_count'], 1)
        self.assertEqual(result['failure_count'], 1)
        self.assertGreater(len(result['errors']), 0)
    
    def test_prepare_message_body(self):
        """Test message body preparation."""
        message_body = self.client._prepare_message_body(self.sample_email)
        
        self.assertIn('email_data', message_body)
        self.assertIn('timestamp', message_body)
        self.assertEqual(message_body['message_type'], 'email_routing')
    
    def test_prepare_message_body_with_attributes(self):
        """Test message body preparation with additional attributes."""
        additional_attrs = {'custom_field': 'custom_value'}
        message_body = self.client._prepare_message_body(
            self.sample_email,
            additional_attrs
        )
        
        self.assertIn('additional_attributes', message_body)
        self.assertEqual(message_body['additional_attributes']['custom_field'], 'custom_value')
    
    def test_prepare_message_attributes(self):
        """Test message attributes preparation."""
        attributes = self.client._prepare_message_attributes(self.sample_email)
        
        self.assertIn('sender', attributes)
        self.assertIn('sender_domain', attributes)
        self.assertIn('priority', attributes)
        self.assertIn('has_attachments', attributes)
        self.assertEqual(attributes['sender']['StringValue'], 'test@example.com')
    
    def test_test_queue_connection_success(self):
        """Test successful queue connection test."""
        self.client.add_queue(self.test_queue)
        self.mock_sqs.get_queue_attributes.return_value = {
            'Attributes': {'QueueArn': 'arn:aws:sqs:us-east-1:123456789012:test'}
        }
        
        result = self.client.test_queue_connection("test_queue")
        self.assertTrue(result)
    
    def test_test_queue_connection_not_found(self):
        """Test queue connection test for non-existent queue."""
        result = self.client.test_queue_connection("nonexistent")
        self.assertFalse(result)
    
    def test_test_queue_connection_error(self):
        """Test queue connection test with error."""
        from botocore.exceptions import ClientError
        
        self.client.add_queue(self.test_queue)
        self.mock_sqs.get_queue_attributes.side_effect = ClientError(
            {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
            'get_queue_attributes'
        )
        
        result = self.client.test_queue_connection("test_queue")
        self.assertFalse(result)
    
    def test_test_all_queues(self):
        """Test testing all queues."""
        self.client.add_queue(self.test_queue)
        self.mock_sqs.get_queue_attributes.return_value = {
            'Attributes': {'QueueArn': 'arn:aws:sqs:us-east-1:123456789012:test'}
        }
        
        results = self.client.test_all_queues()
        self.assertIn("test_queue", results)
    
    def test_get_queue_attributes_success(self):
        """Test getting queue attributes."""
        self.client.add_queue(self.test_queue)
        self.mock_sqs.get_queue_attributes.return_value = {
            'Attributes': {
                'QueueArn': 'arn:aws:sqs:us-east-1:123456789012:test',
                'VisibilityTimeout': '30'
            }
        }
        
        attributes = self.client.get_queue_attributes("test_queue")
        self.assertIsNotNone(attributes)
        self.assertIn('QueueArn', attributes)
    
    def test_get_queue_attributes_not_found(self):
        """Test getting attributes for non-existent queue."""
        attributes = self.client.get_queue_attributes("nonexistent")
        self.assertIsNone(attributes)
    
    def test_get_queue_attributes_error(self):
        """Test getting attributes with error."""
        self.client.add_queue(self.test_queue)
        self.mock_sqs.get_queue_attributes.side_effect = Exception("Test error")
        
        attributes = self.client.get_queue_attributes("test_queue")
        self.assertIsNone(attributes)


if __name__ == '__main__':
    unittest.main()
