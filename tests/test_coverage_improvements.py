#!/usr/bin/env python3
"""
Additional tests to improve coverage for various modules.
"""
import unittest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator.models.email_model import EmailData, EmailAttachment
from inbound_orchestrator.orchestrator import InboundOrchestrator
from inbound_orchestrator.rules.rule_engine import EmailRule


class TestEmailModelCoverage(unittest.TestCase):
    """Additional tests for EmailData to improve coverage."""
    
    def test_from_dict_with_attachments(self):
        """Test creating EmailData from dictionary with attachments."""
        email_dict = {
            'subject': 'Test',
            'sender': 'test@example.com',
            'recipients': ['recipient@example.com'],
            'cc_recipients': [],
            'bcc_recipients': [],
            'body_text': 'Body',
            'body_html': None,
            'message_id': '<test@example.com>',
            'received_date': '2024-01-01T12:00:00',
            'sent_date': None,
            'headers': {},
            'attachments': [
                {
                    'filename': 'test.pdf',
                    'content_type': 'application/pdf',
                    'size': 1024,
                    'content': None
                }
            ],
            'priority': 'normal'
        }
        
        email_data = EmailData.from_dict(email_dict)
        self.assertEqual(len(email_data.attachments), 1)
        self.assertEqual(email_data.attachments[0].filename, 'test.pdf')
    
    def test_from_dict_with_sent_date(self):
        """Test creating EmailData from dictionary with sent_date."""
        email_dict = {
            'subject': 'Test',
            'sender': 'test@example.com',
            'recipients': ['recipient@example.com'],
            'cc_recipients': [],
            'bcc_recipients': [],
            'body_text': 'Body',
            'body_html': None,
            'message_id': '<test@example.com>',
            'received_date': '2024-01-01T12:00:00',
            'sent_date': '2024-01-01T11:00:00',
            'headers': {},
            'attachments': [],
            'priority': 'normal'
        }
        
        email_data = EmailData.from_dict(email_dict)
        self.assertIsNotNone(email_data.sent_date)
    
    def test_from_email_message_multipart(self):
        """Test creating EmailData from multipart email."""
        import email
        from email import message_from_string
        
        raw_email = """From: sender@example.com
To: recipient@example.com
Subject: Multipart Test
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

Plain text body
--boundary123
Content-Type: text/html; charset="utf-8"

<p>HTML body</p>
--boundary123--
"""
        message = message_from_string(raw_email)
        email_data = EmailData.from_email_message(message)
        
        self.assertEqual(email_data.subject, 'Multipart Test')
        self.assertTrue(len(email_data.body_text) > 0 or len(email_data.body_html or "") > 0)
    
    def test_from_email_message_with_invalid_date(self):
        """Test creating EmailData with invalid date header."""
        import email
        raw_email = """From: sender@example.com
To: recipient@example.com
Subject: Invalid Date
Date: not-a-valid-date

Body
"""
        message = email.message_from_string(raw_email)
        email_data = EmailData.from_email_message(message)
        
        self.assertIsNone(email_data.sent_date)


class TestOrchestratorCoverage(unittest.TestCase):
    """Additional tests for InboundOrchestrator to improve coverage."""
    
    @patch('inbound_orchestrator.orchestrator.ConfigLoader')
    def test_load_configuration_error(self, mock_loader):
        """Test handling of configuration load error."""
        mock_loader.load_full_config.side_effect = Exception("Load error")
        
        orchestrator = InboundOrchestrator(default_queue='default')
        
        with self.assertRaises(Exception):
            orchestrator.load_configuration('/tmp/test_config.yaml')
    
    def test_process_email_error_handling(self):
        """Test error handling in process_email."""
        orchestrator = InboundOrchestrator(default_queue='default')
        
        # Create a bad email that will cause errors
        bad_email = Mock()
        bad_email.message_id = "bad"
        bad_email.subject = "Test"
        bad_email.sender = "test@example.com"
        bad_email.to_dict = Mock(side_effect=Exception("Test error"))
        
        result = orchestrator.process_email(bad_email, dry_run=True)
        
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error'])
    
    @patch('inbound_orchestrator.orchestrator.EmailParser')
    def test_process_email_from_file(self, mock_parser):
        """Test processing email from file."""
        orchestrator = InboundOrchestrator(default_queue='default')
        
        mock_email = EmailData(
            subject="Test",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="Body",
            body_html=None,
            message_id="<test@example.com>",
            received_date=datetime.now(),
            sent_date=None,
            headers={},
            attachments=[],
            priority="normal"
        )
        mock_parser.from_file.return_value = mock_email
        
        result = orchestrator.process_email_from_file('/tmp/test.eml', dry_run=True)
        self.assertTrue(result['success'])
    
    def test_health_check_with_errors(self):
        """Test health check with errors."""
        orchestrator = InboundOrchestrator(default_queue='default')
        
        # Mock the SQS client to raise an error
        orchestrator.sqs_client.test_all_queues = Mock(side_effect=Exception("SQS error"))
        
        health = orchestrator.health_check()
        
        self.assertEqual(health['overall_status'], 'unhealthy')
    
    def test_health_check_degraded(self):
        """Test health check with degraded status."""
        orchestrator = InboundOrchestrator(default_queue='default')
        
        # Add a queue
        from inbound_orchestrator.sqs.sqs_client import SQSQueue
        orchestrator.add_queue(SQSQueue(
            name="queue1",
            url="https://test.com/queue1",
            description="Test"
        ))
        orchestrator.add_queue(SQSQueue(
            name="queue2",
            url="https://test.com/queue2",
            description="Test"
        ))
        
        # Mock test_all_queues to return partial success
        orchestrator.sqs_client.test_all_queues = Mock(return_value={
            'queue1': True,
            'queue2': False
        })
        
        health = orchestrator.health_check()
        
        self.assertEqual(health['overall_status'], 'degraded')


class TestConfigLoaderCoverage(unittest.TestCase):
    """Additional tests for ConfigLoader to improve coverage."""
    
    def test_load_file_auto_detect_json(self):
        """Test loading file with auto-detected JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('{"test": "value"}')
            path = f.name
        
        try:
            from inbound_orchestrator.utils.config_loader import ConfigLoader
            config = ConfigLoader.load_file(path)
            self.assertEqual(config['test'], 'value')
        finally:
            Path(path).unlink()
    
    def test_load_file_auto_detect_yaml(self):
        """Test loading file with auto-detected YAML format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('test: value\nnumber: 42')
            path = f.name
        
        try:
            from inbound_orchestrator.utils.config_loader import ConfigLoader
            config = ConfigLoader.load_file(path)
            self.assertEqual(config['test'], 'value')
        finally:
            Path(path).unlink()
    
    def test_load_queues_with_error(self):
        """Test loading queues with some invalid entries."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
queues:
  - name: valid_queue
    url: https://test.com/valid
    description: Valid
  - name: invalid_queue
    # Missing required url field
    description: Invalid
""")
            path = f.name
        
        try:
            from inbound_orchestrator.utils.config_loader import ConfigLoader
            queues = ConfigLoader.load_queues(path)
            # Should only load the valid queue
            self.assertEqual(len(queues), 1)
        finally:
            Path(path).unlink()


class TestEmailParserCoverage(unittest.TestCase):
    """Additional tests for EmailParser to improve coverage."""
    
    def test_from_raw_email_with_encoding_error(self):
        """Test parsing raw email with encoding issues."""
        from inbound_orchestrator.utils.email_parser import EmailParser
        
        # Raw email with potentially problematic bytes
        raw_email = b"""From: sender@example.com
To: recipient@example.com
Subject: Test

Body with special chars: \xc3\xa9
"""
        email_data = EmailParser.from_raw_email(raw_email)
        self.assertIsInstance(email_data, EmailData)
    
    def test_validate_email_data_with_exception(self):
        """Test validation with exception handling."""
        from inbound_orchestrator.utils.email_parser import EmailParser
        
        # Create a mock that raises exception during validation
        bad_email = Mock()
        bad_email.subject = Mock(side_effect=Exception("Test error"))
        
        result = EmailParser.validate_email_data(bad_email)
        self.assertFalse(result)


class TestSQSClientCoverage(unittest.TestCase):
    """Additional tests for SQSClient to improve coverage."""
    
    @patch('inbound_orchestrator.sqs.sqs_client.boto3')
    def test_send_message_generic_exception(self, mock_boto3):
        """Test handling of generic exception when sending message."""
        from inbound_orchestrator.sqs.sqs_client import SQSClient, SQSQueue
        
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        
        client = SQSClient(region_name='us-east-1')
        client.add_queue(SQSQueue(
            name="test",
            url="https://test.com/queue",
            description="Test"
        ))
        
        # Mock send_message to raise generic exception
        mock_sqs.send_message.side_effect = Exception("Generic error")
        
        email = EmailData(
            subject="Test",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="Body",
            body_html=None,
            message_id="<test@example.com>",
            received_date=datetime.now(),
            sent_date=None,
            headers={},
            attachments=[],
            priority="normal"
        )
        
        result = client.send_email_message(email, "test")
        self.assertFalse(result)
    
    @patch('inbound_orchestrator.sqs.sqs_client.boto3')
    def test_send_batch_exception(self, mock_boto3):
        """Test batch send with exception."""
        from inbound_orchestrator.sqs.sqs_client import SQSClient, SQSQueue
        
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        
        client = SQSClient(region_name='us-east-1')
        client.add_queue(SQSQueue(
            name="test",
            url="https://test.com/queue",
            description="Test"
        ))
        
        # Mock send_message_batch to raise exception
        mock_sqs.send_message_batch.side_effect = Exception("Batch error")
        
        email = EmailData(
            subject="Test",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="Body",
            body_html=None,
            message_id="<test@example.com>",
            received_date=datetime.now(),
            sent_date=None,
            headers={},
            attachments=[],
            priority="normal"
        )
        
        messages = [(email, None, None, None)]
        result = client.send_batch_messages(messages, "test")
        
        self.assertEqual(result['failure_count'], 1)
    
    @patch('inbound_orchestrator.sqs.sqs_client.boto3')
    def test_test_queue_generic_exception(self, mock_boto3):
        """Test queue connection test with generic exception."""
        from inbound_orchestrator.sqs.sqs_client import SQSClient, SQSQueue
        
        mock_sqs = MagicMock()
        mock_boto3.client.return_value = mock_sqs
        
        client = SQSClient(region_name='us-east-1')
        client.add_queue(SQSQueue(
            name="test",
            url="https://test.com/queue",
            description="Test"
        ))
        
        # Mock get_queue_attributes to raise generic exception
        mock_sqs.get_queue_attributes.side_effect = Exception("Generic error")
        
        result = client.test_queue_connection("test")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
