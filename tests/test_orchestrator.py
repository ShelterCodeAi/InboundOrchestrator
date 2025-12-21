#!/usr/bin/env python3
"""
Tests for the InboundOrchestrator class.
"""
import unittest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import tempfile

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator.orchestrator import InboundOrchestrator
from inbound_orchestrator.models.email_model import EmailData
from inbound_orchestrator.rules.rule_engine import EmailRule
from inbound_orchestrator.sqs.sqs_client import SQSQueue


class TestInboundOrchestrator(unittest.TestCase):
    """Test cases for InboundOrchestrator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = InboundOrchestrator(default_queue='default')
        
        self.sample_email = EmailData(
            subject="Test Email",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="Test email body",
            body_html=None,
            message_id="<test@example.com>",
            received_date=datetime.now(),
            sent_date=datetime.now(),
            headers={},
            attachments=[],
            priority="normal"
        )
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        self.assertEqual(self.orchestrator.default_queue, 'default')
        self.assertIsNotNone(self.orchestrator.rule_engine)
        self.assertIsNotNone(self.orchestrator.sqs_client)
        self.assertIsNotNone(self.orchestrator.stats)
    
    def test_initialization_with_config(self):
        """Test orchestrator initialization with config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
settings:
  default_queue: test_queue

queues:
  - name: test_queue
    url: https://sqs.us-east-1.amazonaws.com/123456789012/test
    description: Test queue

rules:
  - name: test_rule
    description: Test rule
    condition: "priority == 'high'"
    action: test_queue
    priority: 100
    enabled: true
""")
            config_path = f.name
        
        try:
            orchestrator = InboundOrchestrator(config_file=config_path, default_queue='default')
            self.assertEqual(orchestrator.default_queue, 'test_queue')
            self.assertEqual(len(orchestrator.rule_engine.list_rules()), 1)
        finally:
            Path(config_path).unlink()
    
    def test_add_rule(self):
        """Test adding a rule."""
        rule = EmailRule(
            name="test_rule",
            description="Test rule",
            condition="priority == 'high'",
            action="high_priority",
            priority=100,
            enabled=True
        )
        self.orchestrator.add_rule(rule)
        self.assertEqual(len(self.orchestrator.rule_engine.list_rules()), 1)
    
    def test_add_rule_from_dict(self):
        """Test adding a rule from dictionary."""
        rule_dict = {
            'name': 'dict_rule',
            'description': 'Dictionary rule',
            'condition': "contains(subject, 'test')",
            'action': 'test_queue',
            'priority': 50,
            'enabled': True
        }
        self.orchestrator.add_rule(rule_dict)
        self.assertEqual(len(self.orchestrator.rule_engine.list_rules()), 1)
    
    def test_add_queue(self):
        """Test adding a queue."""
        queue = SQSQueue(
            name="test_queue",
            url="https://sqs.us-east-1.amazonaws.com/123456789012/test",
            description="Test queue"
        )
        self.orchestrator.add_queue(queue)
        self.assertEqual(len(self.orchestrator.sqs_client.list_queues()), 1)
    
    def test_add_queue_from_dict(self):
        """Test adding a queue from dictionary."""
        queue_dict = {
            'name': 'dict_queue',
            'url': 'https://sqs.us-east-1.amazonaws.com/123456789012/dict',
            'description': 'Dictionary queue'
        }
        self.orchestrator.add_queue(queue_dict)
        self.assertEqual(len(self.orchestrator.sqs_client.list_queues()), 1)
    
    def test_process_email_dry_run(self):
        """Test processing email in dry run mode."""
        result = self.orchestrator.process_email(self.sample_email, dry_run=True)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['queue_name'], 'default')
        self.assertTrue(result['dry_run'])
        self.assertIsNotNone(result['processing_time'])
    
    def test_process_email_with_matching_rule(self):
        """Test processing email with matching rule."""
        rule = EmailRule(
            name="test_match",
            description="Test matching rule",
            condition="contains(subject, 'Test')",
            action="test_queue",
            priority=100,
            enabled=True
        )
        self.orchestrator.add_rule(rule)
        
        result = self.orchestrator.process_email(self.sample_email, dry_run=True)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['queue_name'], 'test_queue')
        self.assertIn('test_match', result['matched_rules'])
        self.assertEqual(result['selected_action'], 'test_queue')
    
    def test_process_email_with_custom_attributes(self):
        """Test processing email with custom attributes."""
        custom_attrs = {'custom_field': 'custom_value'}
        result = self.orchestrator.process_email(
            self.sample_email,
            dry_run=True,
            custom_attributes=custom_attrs
        )
        
        self.assertTrue(result['success'])
    
    def test_process_emails_batch(self):
        """Test batch processing of emails."""
        emails = [self.sample_email] * 5
        results = self.orchestrator.process_emails_batch(emails, dry_run=True)
        
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r['success'] for r in results))
    
    def test_process_emails_batch_with_error(self):
        """Test batch processing with errors."""
        # Create an email that will cause error
        bad_email = Mock()
        bad_email.message_id = "bad_email"
        bad_email.to_dict = Mock(side_effect=Exception("Test error"))
        
        emails = [self.sample_email, bad_email]
        results = self.orchestrator.process_emails_batch(emails, dry_run=True)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]['success'])
        self.assertFalse(results[1]['success'])
    
    def test_process_email_from_raw(self):
        """Test processing email from raw content."""
        raw_email = """From: sender@example.com
To: recipient@example.com
Subject: Test Subject
Date: Mon, 1 Jan 2024 12:00:00 +0000

Test body content
"""
        result = self.orchestrator.process_email_from_raw(raw_email, dry_run=True)
        self.assertTrue(result['success'])
        self.assertEqual(result['subject'], 'Test Subject')
    
    def test_test_rule(self):
        """Test rule testing functionality."""
        test_emails = [self.sample_email]
        results = self.orchestrator.test_rule("contains(subject, 'Test')", test_emails)
        
        self.assertEqual(results['total_emails'], 1)
        self.assertEqual(results['matches'], 1)
        self.assertEqual(results['errors'], 0)
    
    def test_test_rule_no_match(self):
        """Test rule testing with no matches."""
        test_emails = [self.sample_email]
        results = self.orchestrator.test_rule("priority == 'urgent'", test_emails)
        
        self.assertEqual(results['total_emails'], 1)
        self.assertEqual(results['matches'], 0)
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        # Process some emails
        self.orchestrator.process_email(self.sample_email, dry_run=True)
        
        stats = self.orchestrator.get_statistics()
        
        self.assertIn('total_processed', stats)
        self.assertIn('successful_routes', stats)
        self.assertIn('failed_routes', stats)
        self.assertIn('success_rate', stats)
        self.assertEqual(stats['total_processed'], 1)
    
    def test_reset_statistics(self):
        """Test statistics reset."""
        self.orchestrator.process_email(self.sample_email, dry_run=True)
        self.orchestrator.reset_statistics()
        
        stats = self.orchestrator.get_statistics()
        self.assertEqual(stats['total_processed'], 0)
    
    def test_health_check(self):
        """Test health check."""
        health = self.orchestrator.health_check()
        
        self.assertIn('overall_status', health)
        self.assertIn('components', health)
        self.assertIn('rule_engine', health['components'])
        self.assertIn('sqs_client', health['components'])
    
    def test_save_configuration(self):
        """Test saving configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            # Add some rules and queues
            self.orchestrator.add_rule({
                'name': 'test_rule',
                'description': 'Test',
                'condition': "priority == 'high'",
                'action': 'test_queue',
                'priority': 100,
                'enabled': True
            })
            
            self.orchestrator.save_configuration(config_path)
            self.assertTrue(Path(config_path).exists())
        finally:
            Path(config_path).unlink()
    
    def test_save_configuration_no_file(self):
        """Test saving configuration without file specified."""
        with self.assertRaises(ValueError):
            self.orchestrator.save_configuration()
    
    def test_str_repr(self):
        """Test string representation."""
        str_repr = str(self.orchestrator)
        self.assertIn('InboundOrchestrator', str_repr)
        
        repr_str = repr(self.orchestrator)
        self.assertIn('InboundOrchestrator', repr_str)


if __name__ == '__main__':
    unittest.main()
