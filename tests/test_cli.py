#!/usr/bin/env python3
"""
Tests for the CLI module.
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from io import StringIO
import argparse

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator import cli
from inbound_orchestrator.models.email_model import EmailData


class TestCLI(unittest.TestCase):
    """Test cases for CLI module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_email = EmailData(
            subject="Test Email",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="Test body",
            body_html=None,
            message_id="<test@example.com>",
            received_date=None,
            sent_date=None,
            headers={},
            attachments=[]
        )
    
    @patch('inbound_orchestrator.cli.PostgresEmailIntake')
    @patch('inbound_orchestrator.cli.InboundOrchestrator')
    @patch('sys.stdout', new_callable=StringIO)
    def test_process_db_emails_with_email_id(self, mock_stdout, mock_orchestrator_class, mock_intake_class):
        """Test process_db_emails with email_id parameter."""
        # Setup mocks
        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        mock_intake = MagicMock()
        mock_intake_class.return_value.__enter__ = MagicMock(return_value=mock_intake)
        mock_intake_class.return_value.__exit__ = MagicMock(return_value=None)
        mock_intake.test_connection.return_value = True
        mock_intake.fetch_emails_by_email_id.return_value = [self.sample_email]
        
        mock_orchestrator.process_emails_batch.return_value = [
            {
                'success': True,
                'queue_name': 'test_queue',
                'matched_rules': ['rule1'],
                'subject': 'Test Email',
                'sender': 'test@example.com'
            }
        ]
        
        # Create args
        args = argparse.Namespace(
            config=None,
            region='us-east-1',
            default_queue='default',
            host=None,
            port=None,
            database=None,
            user=None,
            password=None,
            schema=None,
            email_id=33,
            limit=None,
            dry_run=True
        )
        
        # Execute
        result = cli.process_db_emails(args)
        
        # Verify
        self.assertEqual(result, 0)
        mock_intake.fetch_emails_by_email_id.assert_called_once_with(33)
        mock_orchestrator.process_emails_batch.assert_called_once()
        
        output = mock_stdout.getvalue()
        self.assertIn('Connected to database:', output)
        self.assertIn('Fetched 1 email for email_id=33', output)
        self.assertIn('Processed 1 email:', output)
        self.assertIn('Successful: 1', output)
        self.assertIn('Queue Distribution:', output)
        self.assertIn('test_queue: 1', output)
        self.assertIn('DRY RUN', output)
    
    @patch('inbound_orchestrator.cli.PostgresEmailIntake')
    @patch('inbound_orchestrator.cli.InboundOrchestrator')
    @patch('sys.stdout', new_callable=StringIO)
    def test_process_db_emails_with_limit(self, mock_stdout, mock_orchestrator_class, mock_intake_class):
        """Test process_db_emails with limit parameter."""
        # Setup mocks
        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        mock_intake = MagicMock()
        mock_intake_class.return_value.__enter__ = MagicMock(return_value=mock_intake)
        mock_intake_class.return_value.__exit__ = MagicMock(return_value=None)
        mock_intake.test_connection.return_value = True
        mock_intake.fetch_all_emails.return_value = [self.sample_email, self.sample_email]
        
        mock_orchestrator.process_emails_batch.return_value = [
            {
                'success': True,
                'queue_name': 'queue1',
                'matched_rules': [],
                'subject': 'Test Email',
                'sender': 'test@example.com'
            },
            {
                'success': False,
                'queue_name': 'queue2',
                'matched_rules': ['rule1'],
                'subject': 'Test Email',
                'sender': 'test@example.com'
            }
        ]
        
        # Create args
        args = argparse.Namespace(
            config=None,
            region='us-east-1',
            default_queue='default',
            host='localhost',
            port=5432,
            database='testdb',
            user='testuser',
            password='testpass',
            schema='test_schema',
            email_id=None,
            limit=10,
            dry_run=False
        )
        
        # Execute
        result = cli.process_db_emails(args)
        
        # Verify
        self.assertEqual(result, 0)
        mock_intake.fetch_all_emails.assert_called_once_with(limit=10)
        mock_orchestrator.process_emails_batch.assert_called_once()
        
        output = mock_stdout.getvalue()
        self.assertIn('Fetched 2 emails from database (limit=10)', output)
        self.assertIn('Processed 2 emails:', output)
        self.assertIn('Successful: 1', output)
        self.assertIn('Failed: 1', output)
        self.assertIn('Success Rate: 50.0%', output)
    
    @patch('inbound_orchestrator.cli.PostgresEmailIntake')
    @patch('inbound_orchestrator.cli.InboundOrchestrator')
    @patch('sys.stdout', new_callable=StringIO)
    def test_process_db_emails_no_results(self, mock_stdout, mock_orchestrator_class, mock_intake_class):
        """Test process_db_emails when no emails are found."""
        # Setup mocks
        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        mock_intake = MagicMock()
        mock_intake_class.return_value.__enter__ = MagicMock(return_value=mock_intake)
        mock_intake_class.return_value.__exit__ = MagicMock(return_value=None)
        mock_intake.test_connection.return_value = True
        mock_intake.fetch_emails_by_email_id.return_value = []
        
        # Create args
        args = argparse.Namespace(
            config=None,
            region='us-east-1',
            default_queue='default',
            host=None,
            port=None,
            database=None,
            user=None,
            password=None,
            schema=None,
            email_id=999,
            limit=None,
            dry_run=True
        )
        
        # Execute
        result = cli.process_db_emails(args)
        
        # Verify
        self.assertEqual(result, 1)
        mock_intake.fetch_emails_by_email_id.assert_called_once_with(999)
        mock_orchestrator.process_emails_batch.assert_not_called()
        
        output = mock_stdout.getvalue()
        self.assertIn('No emails found matching criteria', output)
    
    @patch('inbound_orchestrator.cli.PostgresEmailIntake')
    @patch('inbound_orchestrator.cli.InboundOrchestrator')
    @patch('sys.stdout', new_callable=StringIO)
    def test_process_db_emails_connection_failure(self, mock_stdout, mock_orchestrator_class, mock_intake_class):
        """Test process_db_emails when database connection fails."""
        # Setup mocks
        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        mock_intake = MagicMock()
        mock_intake_class.return_value.__enter__ = MagicMock(return_value=mock_intake)
        mock_intake_class.return_value.__exit__ = MagicMock(return_value=None)
        mock_intake.test_connection.return_value = False
        
        # Create args
        args = argparse.Namespace(
            config=None,
            region='us-east-1',
            default_queue='default',
            host=None,
            port=None,
            database=None,
            user=None,
            password=None,
            schema=None,
            email_id=33,
            limit=None,
            dry_run=True
        )
        
        # Execute
        result = cli.process_db_emails(args)
        
        # Verify
        self.assertEqual(result, 1)
        mock_intake.fetch_emails_by_email_id.assert_not_called()
        
        output = mock_stdout.getvalue()
        self.assertIn('Failed to connect to database', output)
    
    @patch('inbound_orchestrator.cli.PostgresEmailIntake')
    @patch('sys.stdout', new_callable=StringIO)
    def test_process_db_emails_import_error(self, mock_stdout, mock_intake_class):
        """Test process_db_emails when psycopg2 is not available."""
        # Setup mock to raise ImportError
        mock_intake_class.side_effect = ImportError("No module named 'psycopg2'")
        
        # Create args
        args = argparse.Namespace(
            config=None,
            region='us-east-1',
            default_queue='default',
            host=None,
            port=None,
            database=None,
            user=None,
            password=None,
            schema=None,
            email_id=33,
            limit=None,
            dry_run=True
        )
        
        # Execute
        result = cli.process_db_emails(args)
        
        # Verify
        self.assertEqual(result, 1)
        
        output = mock_stdout.getvalue()
        self.assertIn('PostgreSQL support not available', output)
        self.assertIn('pip install psycopg2-binary', output)
    
    @patch.dict('os.environ', {'POSTGRES_PORT': 'invalid'})
    @patch('sys.stdout', new_callable=StringIO)
    def test_process_db_emails_invalid_port_env(self, mock_stdout):
        """Test process_db_emails when POSTGRES_PORT environment variable is invalid."""
        # Create args without port
        args = argparse.Namespace(
            config=None,
            region='us-east-1',
            default_queue='default',
            host=None,
            port=None,
            database=None,
            user=None,
            password=None,
            schema=None,
            email_id=33,
            limit=None,
            dry_run=True
        )
        
        # Execute
        result = cli.process_db_emails(args)
        
        # Verify
        self.assertEqual(result, 1)
        
        output = mock_stdout.getvalue()
        self.assertIn('Invalid port value in POSTGRES_PORT environment variable', output)
    
    @patch('inbound_orchestrator.cli.PostgresEmailIntake')
    @patch('inbound_orchestrator.cli.InboundOrchestrator')
    @patch('sys.stdout', new_callable=StringIO)
    def test_process_db_emails_shows_rule_matches(self, mock_stdout, mock_orchestrator_class, mock_intake_class):
        """Test that process_db_emails displays rule match statistics."""
        # Setup mocks
        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        mock_intake = MagicMock()
        mock_intake_class.return_value.__enter__ = MagicMock(return_value=mock_intake)
        mock_intake_class.return_value.__exit__ = MagicMock(return_value=None)
        mock_intake.test_connection.return_value = True
        mock_intake.fetch_all_emails.return_value = [self.sample_email, self.sample_email]
        
        mock_orchestrator.process_emails_batch.return_value = [
            {
                'success': True,
                'queue_name': 'queue1',
                'matched_rules': ['high_priority', 'urgent'],
                'subject': 'Test Email',
                'sender': 'test@example.com'
            },
            {
                'success': True,
                'queue_name': 'queue1',
                'matched_rules': ['high_priority'],
                'subject': 'Test Email',
                'sender': 'test@example.com'
            }
        ]
        
        # Create args
        args = argparse.Namespace(
            config=None,
            region='us-east-1',
            default_queue='default',
            host=None,
            port=None,
            database=None,
            user=None,
            password=None,
            schema=None,
            email_id=None,
            limit=None,
            dry_run=True
        )
        
        # Execute
        result = cli.process_db_emails(args)
        
        # Verify
        self.assertEqual(result, 0)
        
        output = mock_stdout.getvalue()
        self.assertIn('Rule Matches:', output)
        self.assertIn('high_priority: 2', output)
        self.assertIn('urgent: 1', output)


if __name__ == '__main__':
    unittest.main()
