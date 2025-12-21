#!/usr/bin/env python3
"""
Tests for the EmailParser class.
"""
import unittest
import sys
from pathlib import Path
import tempfile
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator.utils.email_parser import EmailParser
from inbound_orchestrator.models.email_model import EmailData


class TestEmailParser(unittest.TestCase):
    """Test cases for EmailParser class."""
    
    def test_from_raw_email(self):
        """Test parsing email from raw content."""
        raw_email = """From: sender@example.com
To: recipient@example.com
Subject: Test Subject
Date: Mon, 1 Jan 2024 12:00:00 +0000

Test body content
"""
        email_data = EmailParser.from_raw_email(raw_email)
        
        self.assertIsInstance(email_data, EmailData)
        self.assertEqual(email_data.subject, 'Test Subject')
        self.assertEqual(email_data.sender, 'sender@example.com')
    
    def test_from_raw_email_bytes(self):
        """Test parsing email from bytes."""
        raw_email = b"""From: sender@example.com
To: recipient@example.com
Subject: Test Subject

Test body
"""
        email_data = EmailParser.from_raw_email(raw_email)
        
        self.assertIsInstance(email_data, EmailData)
        self.assertEqual(email_data.subject, 'Test Subject')
    
    def test_from_file(self):
        """Test parsing email from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.eml', delete=False) as f:
            f.write("""From: sender@example.com
To: recipient@example.com
Subject: File Test

Body content
""")
            email_path = f.name
        
        try:
            email_data = EmailParser.from_file(email_path)
            self.assertIsInstance(email_data, EmailData)
            self.assertEqual(email_data.subject, 'File Test')
        finally:
            Path(email_path).unlink()
    
    def test_from_file_not_found(self):
        """Test parsing from non-existent file."""
        with self.assertRaises(FileNotFoundError):
            EmailParser.from_file('/nonexistent/email.eml')
    
    def test_from_json_string(self):
        """Test parsing email from JSON string."""
        json_data = """{
            "subject": "JSON Test",
            "sender": "sender@example.com",
            "recipients": ["recipient@example.com"],
            "cc_recipients": [],
            "bcc_recipients": [],
            "body_text": "JSON body",
            "body_html": null,
            "message_id": "<test@example.com>",
            "received_date": "2024-01-01T12:00:00",
            "sent_date": null,
            "headers": {},
            "attachments": [],
            "priority": "normal"
        }"""
        
        email_data = EmailParser.from_json(json_data)
        self.assertIsInstance(email_data, EmailData)
        self.assertEqual(email_data.subject, 'JSON Test')
    
    def test_from_json_dict(self):
        """Test parsing email from dictionary."""
        json_dict = {
            "subject": "Dict Test",
            "sender": "sender@example.com",
            "recipients": ["recipient@example.com"],
            "cc_recipients": [],
            "bcc_recipients": [],
            "body_text": "Dict body",
            "body_html": None,
            "message_id": "<test@example.com>",
            "received_date": "2024-01-01T12:00:00",
            "sent_date": None,
            "headers": {},
            "attachments": [],
            "priority": "normal"
        }
        
        email_data = EmailParser.from_json(json_dict)
        self.assertIsInstance(email_data, EmailData)
        self.assertEqual(email_data.subject, 'Dict Test')
    
    def test_batch_parse_directory(self):
        """Test batch parsing emails from directory."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test email files
            for i in range(3):
                email_file = temp_path / f'email{i}.eml'
                email_file.write_text(f"""From: sender{i}@example.com
To: recipient@example.com
Subject: Email {i}

Body {i}
""")
            
            # Parse all emails
            emails = EmailParser.batch_parse_directory(temp_path, pattern='*.eml')
            
            self.assertEqual(len(emails), 3)
            self.assertTrue(all(isinstance(e, EmailData) for e in emails))
    
    def test_batch_parse_directory_not_found(self):
        """Test batch parsing from non-existent directory."""
        with self.assertRaises(FileNotFoundError):
            EmailParser.batch_parse_directory('/nonexistent/directory')
    
    def test_batch_parse_directory_not_a_directory(self):
        """Test batch parsing from a file path."""
        with tempfile.NamedTemporaryFile() as f:
            with self.assertRaises(ValueError):
                EmailParser.batch_parse_directory(f.name)
    
    def test_batch_parse_directory_with_error(self):
        """Test batch parsing with some invalid files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create valid email file
            (temp_path / 'valid.eml').write_text("""From: sender@example.com
To: recipient@example.com
Subject: Valid

Valid body
""")
            
            # Create invalid file
            (temp_path / 'invalid.eml').write_text("Not a valid email format")
            
            # Should parse only valid emails
            emails = EmailParser.batch_parse_directory(temp_path, pattern='*.eml')
            
            # At least the valid one should be parsed
            self.assertGreaterEqual(len(emails), 1)
    
    def test_create_sample_email_data(self):
        """Test creating sample email data."""
        sample_email = EmailParser.create_sample_email_data()
        
        self.assertIsInstance(sample_email, EmailData)
        self.assertEqual(sample_email.subject, "Sample Email Subject")
        self.assertEqual(sample_email.sender, "sender@example.com")
        self.assertGreater(len(sample_email.attachments), 0)
    
    def test_validate_email_data_valid(self):
        """Test validating valid email data."""
        email_data = EmailData(
            subject="Valid Email",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="Valid body",
            body_html=None,
            message_id="<valid@example.com>",
            received_date=datetime.now(),
            sent_date=None,
            headers={},
            attachments=[],
            priority="normal"
        )
        
        self.assertTrue(EmailParser.validate_email_data(email_data))
    
    def test_validate_email_data_no_subject_or_body(self):
        """Test validating email with no subject or body."""
        email_data = EmailData(
            subject="",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="",
            body_html=None,
            message_id="<test@example.com>",
            received_date=datetime.now(),
            sent_date=None,
            headers={},
            attachments=[],
            priority="normal"
        )
        
        self.assertFalse(EmailParser.validate_email_data(email_data))
    
    def test_validate_email_data_no_sender(self):
        """Test validating email with no sender."""
        email_data = EmailData(
            subject="Test",
            sender="",
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
        
        self.assertFalse(EmailParser.validate_email_data(email_data))
    
    def test_validate_email_data_no_recipients(self):
        """Test validating email with no recipients."""
        email_data = EmailData(
            subject="Test",
            sender="sender@example.com",
            recipients=[],
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
        
        self.assertFalse(EmailParser.validate_email_data(email_data))
    
    def test_validate_email_data_invalid_address(self):
        """Test validating email with invalid email address."""
        email_data = EmailData(
            subject="Test",
            sender="invalid-email",
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
        
        self.assertFalse(EmailParser.validate_email_data(email_data))


if __name__ == '__main__':
    unittest.main()
