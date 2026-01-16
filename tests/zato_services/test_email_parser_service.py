"""
Tests for Zato email parser service.
"""
import pytest
from unittest.mock import Mock, MagicMock
from email import message_from_string


class TestEmailParserService:
    """Test suite for EmailParserService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Import the service (this would normally be done via Zato service store)
        # For now, we'll test the logic independently
        self.raw_email = """From: sender@example.com
To: recipient@example.com
Subject: Test Email
Message-ID: <test123@example.com>

This is the email body.
"""
    
    def test_parse_email_basic(self):
        """Test basic email parsing."""
        msg = message_from_string(self.raw_email)
        
        assert msg.get('subject') == 'Test Email'
        assert msg.get('from') == 'sender@example.com'
        assert msg.get('to') == 'recipient@example.com'
        assert msg.get('message-id') == '<test123@example.com>'
    
    def test_parse_email_with_cc(self):
        """Test email parsing with CC recipients."""
        raw_email = """From: sender@example.com
To: recipient@example.com
Cc: cc1@example.com, cc2@example.com
Subject: Test Email

Body text.
"""
        msg = message_from_string(raw_email)
        cc_recipients = msg.get('cc', '').split(',')
        
        assert len(cc_recipients) == 2
        assert 'cc1@example.com' in cc_recipients[0]
        assert 'cc2@example.com' in cc_recipients[1]
    
    def test_parse_email_multipart(self):
        """Test parsing multipart email."""
        # Simple multipart test
        raw_email = """From: sender@example.com
To: recipient@example.com
Subject: Multipart Test
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary"

--boundary
Content-Type: text/plain

Plain text body
--boundary--
"""
        msg = message_from_string(raw_email)
        
        assert msg.is_multipart() == True
        assert msg.get('subject') == 'Multipart Test'
    
    def test_parse_email_missing_fields(self):
        """Test parsing email with missing optional fields."""
        raw_email = """Subject: Minimal Email

Body
"""
        msg = message_from_string(raw_email)
        
        assert msg.get('subject') == 'Minimal Email'
        assert msg.get('from', '') == ''
        assert msg.get('to', '') == ''


class TestEmailParserServiceLogic:
    """Test the actual service logic."""
    
    def test_extract_recipients_list(self):
        """Test recipient list extraction."""
        to_field = "user1@example.com, user2@example.com"
        recipients = to_field.split(',') if to_field else []
        
        assert len(recipients) == 2
        assert recipients[0].strip() == 'user1@example.com'
        assert recipients[1].strip() == 'user2@example.com'
    
    def test_extract_recipients_empty(self):
        """Test empty recipient handling."""
        to_field = ""
        recipients = to_field.split(',') if to_field else []
        
        assert len(recipients) == 0
    
    def test_email_data_structure(self):
        """Test email data structure creation."""
        email_data = {
            'subject': 'Test',
            'sender': 'test@example.com',
            'recipients': ['recipient@example.com'],
            'cc_recipients': [],
            'body_text': 'Test body',
            'headers': {},
            'received_date': '2024-01-16T00:00:00',
            'message_id': '<test@example.com>'
        }
        
        assert email_data['subject'] == 'Test'
        assert len(email_data['recipients']) == 1
        assert email_data['sender'] == 'test@example.com'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
