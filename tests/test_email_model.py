#!/usr/bin/env python3
"""
Tests for the EmailData model.
"""
import unittest
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator.models.email_model import EmailData, EmailAttachment


class TestEmailData(unittest.TestCase):
    """Test cases for EmailData class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_attachment = EmailAttachment(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            content=b"sample content"
        )
        
        self.sample_email = EmailData(
            subject="Test Email",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            cc_recipients=["cc@example.com"],
            bcc_recipients=[],
            body_text="Test email body",
            body_html="<p>Test email body</p>",
            message_id="<test@example.com>",
            received_date=datetime.now(),
            sent_date=datetime.now(),
            headers={"From": "sender@example.com"},
            attachments=[self.sample_attachment],
            priority="normal"
        )
    
    def test_email_data_creation(self):
        """Test basic EmailData creation."""
        self.assertEqual(self.sample_email.subject, "Test Email")
        self.assertEqual(self.sample_email.sender, "sender@example.com")
        self.assertEqual(self.sample_email.sender_domain, "example.com")
        self.assertEqual(len(self.sample_email.attachments), 1)
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        email_dict = self.sample_email.to_dict()
        
        # Check basic fields
        self.assertEqual(email_dict['subject'], "Test Email")
        self.assertEqual(email_dict['sender'], "sender@example.com")
        self.assertEqual(email_dict['sender_domain'], "example.com")
        
        # Check computed fields
        self.assertEqual(email_dict['recipient_count'], 1)
        self.assertEqual(email_dict['cc_count'], 1)
        self.assertEqual(email_dict['has_attachments'], True)
        self.assertEqual(email_dict['attachment_count'], 1)
        self.assertEqual(email_dict['subject_length'], len("Test Email"))
    
    def test_from_dict_creation(self):
        """Test creation from dictionary."""
        email_dict = {
            'subject': 'Dict Email',
            'sender': 'dict@example.com',
            'recipients': ['recipient@example.com'],
            'cc_recipients': [],
            'bcc_recipients': [],
            'body_text': 'Dict body',
            'body_html': None,
            'message_id': '<dict@example.com>',
            'received_date': datetime.now().isoformat(),
            'sent_date': None,
            'headers': {},
            'attachments': [],
            'priority': 'normal'
        }
        
        email = EmailData.from_dict(email_dict)
        self.assertEqual(email.subject, 'Dict Email')
        self.assertEqual(email.sender, 'dict@example.com')
        self.assertEqual(email.sender_domain, 'example.com')
    
    def test_contains_keyword(self):
        """Test keyword searching functionality."""
        self.assertTrue(self.sample_email.contains_keyword("Test"))
        self.assertTrue(self.sample_email.contains_keyword("email"))
        self.assertFalse(self.sample_email.contains_keyword("nonexistent"))
        
        # Test case insensitive
        self.assertTrue(self.sample_email.contains_keyword("TEST"))
        self.assertTrue(self.sample_email.contains_keyword("EMAIL"))
    
    def test_matches_sender_pattern(self):
        """Test sender pattern matching."""
        self.assertTrue(self.sample_email.matches_sender_pattern("*@example.com"))
        self.assertTrue(self.sample_email.matches_sender_pattern("sender@*"))
        self.assertFalse(self.sample_email.matches_sender_pattern("*@other.com"))
    
    def test_has_attachment_type(self):
        """Test attachment type checking."""
        self.assertTrue(self.sample_email.has_attachment_type("application/pdf"))
        self.assertFalse(self.sample_email.has_attachment_type("text/plain"))


class TestEmailAttachment(unittest.TestCase):
    """Test cases for EmailAttachment class."""
    
    def test_attachment_creation(self):
        """Test attachment creation."""
        attachment = EmailAttachment(
            filename="document.pdf",
            content_type="application/pdf",
            size=2048,
            content=b"PDF content"
        )
        
        self.assertEqual(attachment.filename, "document.pdf")
        self.assertEqual(attachment.content_type, "application/pdf")
        self.assertEqual(attachment.size, 2048)
        self.assertEqual(attachment.content, b"PDF content")
    
    def test_attachment_to_dict(self):
        """Test attachment dictionary conversion."""
        attachment = EmailAttachment(
            filename="test.txt",
            content_type="text/plain",
            size=100,
            content=b"test content"
        )
        
        att_dict = attachment.to_dict()
        
        self.assertEqual(att_dict['filename'], "test.txt")
        self.assertEqual(att_dict['content_type'], "text/plain")
        self.assertEqual(att_dict['size'], 100)
        self.assertTrue(att_dict['has_content'])


if __name__ == '__main__':
    unittest.main()