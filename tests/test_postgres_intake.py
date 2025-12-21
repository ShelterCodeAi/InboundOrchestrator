#!/usr/bin/env python3
"""
Tests for the Postgres email intake functionality.
"""
import unittest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator.models.email_model import EmailData


class TestPostgresEmailIntake(unittest.TestCase):
    """Test cases for PostgresEmailIntake class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Check if psycopg2 is available
        try:
            from inbound_orchestrator.intake import PostgresEmailIntake
            self.PostgresEmailIntake = PostgresEmailIntake
            self.psycopg2_available = True
        except ImportError:
            self.psycopg2_available = False
            self.skipTest("psycopg2 not available - skipping Postgres tests")
    
    def test_import_postgres_intake(self):
        """Test that PostgresEmailIntake can be imported."""
        self.assertTrue(self.psycopg2_available)
        self.assertIsNotNone(self.PostgresEmailIntake)
    
    def test_postgres_intake_initialization(self):
        """Test PostgresEmailIntake initialization."""
        if not self.psycopg2_available:
            self.skipTest("psycopg2 not available")
        
        intake = self.PostgresEmailIntake(
            host='localhost',
            port=5432,
            database='test_db',
            user='test_user',
            password='test_pass',
            schema='email_messages'
        )
        
        self.assertEqual(intake.connection_params['host'], 'localhost')
        self.assertEqual(intake.connection_params['port'], 5432)
        self.assertEqual(intake.connection_params['database'], 'test_db')
        self.assertEqual(intake.connection_params['user'], 'test_user')
        self.assertEqual(intake.schema, 'email_messages')
    
    def test_map_row_to_email_data(self):
        """Test mapping database row to EmailData object."""
        if not self.psycopg2_available:
            self.skipTest("psycopg2 not available")
        
        intake = self.PostgresEmailIntake(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_pass'
        )
        
        # Mock database row
        test_row = {
            'em_id': 1,
            'subject': 'Test Subject',
            'body': 'Test body content',
            'from_address': 'sender@example.com',
            'email_message_id': '<test@example.com>',
            'time_received': datetime(2024, 1, 1, 12, 0, 0),
            'headers': {
                'To': 'recipient@example.com',
                'Cc': 'cc@example.com',
                'Date': 'Mon, 1 Jan 2024 12:00:00 +0000'
            },
            'json_object': None,
            'has_attachment': False
        }
        
        email_data = intake._map_row_to_email_data(test_row)
        
        self.assertIsInstance(email_data, EmailData)
        self.assertEqual(email_data.subject, 'Test Subject')
        self.assertEqual(email_data.body_text, 'Test body content')
        self.assertEqual(email_data.sender, 'sender@example.com')
        self.assertEqual(email_data.message_id, '<test@example.com>')
        self.assertIn('recipient@example.com', email_data.recipients)
    
    def test_map_row_with_json_object(self):
        """Test mapping database row with recipients in json_object."""
        if not self.psycopg2_available:
            self.skipTest("psycopg2 not available")
        
        intake = self.PostgresEmailIntake(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_pass'
        )
        
        # Mock database row with json_object
        test_row = {
            'em_id': 2,
            'subject': 'Test Subject 2',
            'body': 'Test body 2',
            'from_address': 'sender2@example.com',
            'email_message_id': '<test2@example.com>',
            'time_received': datetime(2024, 1, 2, 12, 0, 0),
            'headers': {},
            'json_object': {
                'to': ['recipient1@example.com', 'recipient2@example.com'],
                'cc': ['cc1@example.com'],
                'bcc': []
            },
            'has_attachment': False
        }
        
        email_data = intake._map_row_to_email_data(test_row)
        
        self.assertIsInstance(email_data, EmailData)
        self.assertEqual(len(email_data.recipients), 2)
        self.assertIn('recipient1@example.com', email_data.recipients)
        self.assertIn('recipient2@example.com', email_data.recipients)
        self.assertIn('cc1@example.com', email_data.cc_recipients)
    
    def test_map_row_with_default_recipients(self):
        """Test mapping database row with missing recipients."""
        if not self.psycopg2_available:
            self.skipTest("psycopg2 not available")
        
        intake = self.PostgresEmailIntake(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_pass'
        )
        
        # Mock database row without recipients
        test_row = {
            'em_id': 3,
            'subject': 'Test Subject 3',
            'body': 'Test body 3',
            'from_address': 'sender3@example.com',
            'email_message_id': '<test3@example.com>',
            'time_received': datetime(2024, 1, 3, 12, 0, 0),
            'headers': {},
            'json_object': None,
            'has_attachment': False
        }
        
        email_data = intake._map_row_to_email_data(test_row)
        
        self.assertIsInstance(email_data, EmailData)
        # Should use default recipient when none available
        self.assertEqual(email_data.recipients, ['unknown@localhost'])


class TestOrchestratorPostgresIntegration(unittest.TestCase):
    """Test cases for InboundOrchestrator Postgres integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from inbound_orchestrator import InboundOrchestrator
            from inbound_orchestrator.intake import PostgresEmailIntake
            self.InboundOrchestrator = InboundOrchestrator
            self.PostgresEmailIntake = PostgresEmailIntake
            self.psycopg2_available = True
        except ImportError:
            self.psycopg2_available = False
            self.skipTest("Dependencies not available - skipping integration tests")
    
    @patch('inbound_orchestrator.intake.postgres_email_intake.psycopg2')
    def test_process_postgres_emails(self, mock_psycopg2):
        """Test process_postgres_emails method with mocked database."""
        if not self.psycopg2_available:
            self.skipTest("Dependencies not available")
        
        # Create orchestrator
        orchestrator = self.InboundOrchestrator(default_queue='default')
        
        # Create mock Postgres intake
        mock_intake = MagicMock()
        mock_intake.fetch_emails_by_email_id.return_value = [
            EmailData(
                subject='Test Email',
                sender='test@example.com',
                recipients=['recipient@example.com'],
                cc_recipients=[],
                bcc_recipients=[],
                body_text='Test body',
                body_html=None,
                message_id='<test@example.com>',
                received_date=datetime.now(),
                sent_date=None,
                headers={},
                attachments=[],
                priority='normal'
            )
        ]
        
        # Process emails
        result = orchestrator.process_postgres_emails(
            postgres_intake=mock_intake,
            email_id=33,
            dry_run=True
        )
        
        # Verify results
        self.assertEqual(result['email_id'], 33)
        self.assertEqual(result['email_count'], 1)
        self.assertEqual(result['processed'], 1)
        self.assertTrue(result['successful'] > 0 or result['failed'] > 0)
        mock_intake.fetch_emails_by_email_id.assert_called_once_with(33)
    
    @patch('inbound_orchestrator.intake.postgres_email_intake.psycopg2')
    def test_process_postgres_emails_no_results(self, mock_psycopg2):
        """Test process_postgres_emails with no emails found."""
        if not self.psycopg2_available:
            self.skipTest("Dependencies not available")
        
        orchestrator = self.InboundOrchestrator(default_queue='default')
        
        # Create mock intake with no emails
        mock_intake = MagicMock()
        mock_intake.fetch_emails_by_email_id.return_value = []
        
        result = orchestrator.process_postgres_emails(
            postgres_intake=mock_intake,
            email_id=99,
            dry_run=True
        )
        
        # Verify empty results
        self.assertEqual(result['email_id'], 99)
        self.assertEqual(result['email_count'], 0)
        self.assertEqual(result['processed'], 0)
        self.assertEqual(result['successful'], 0)


if __name__ == '__main__':
    unittest.main()
