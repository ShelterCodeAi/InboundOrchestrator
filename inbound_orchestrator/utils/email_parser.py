"""
Email parsing utilities for converting various email formats to EmailData objects.
"""
import email
import logging
from email.message import EmailMessage
from pathlib import Path
from typing import Union, Optional, List
import json

from ..models.email_model import EmailData

logger = logging.getLogger(__name__)


class EmailParser:
    """
    Utility class for parsing emails from various sources and formats.
    """
    
    @staticmethod
    def from_raw_email(raw_email: Union[str, bytes]) -> EmailData:
        """
        Parse raw email content into EmailData.
        
        Args:
            raw_email: Raw email content as string or bytes
            
        Returns:
            EmailData object
        """
        try:
            if isinstance(raw_email, bytes):
                raw_email = raw_email.decode('utf-8', errors='ignore')
            
            message = email.message_from_string(raw_email)
            return EmailData.from_email_message(message)
            
        except Exception as e:
            logger.error(f"Failed to parse raw email: {e}")
            raise
    
    @staticmethod
    def from_file(file_path: Union[str, Path]) -> EmailData:
        """
        Parse email from a file.
        
        Args:
            file_path: Path to the email file
            
        Returns:
            EmailData object
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Email file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return EmailParser.from_raw_email(content)
            
        except Exception as e:
            logger.error(f"Failed to parse email from file {file_path}: {e}")
            raise
    
    @staticmethod
    def from_json(json_data: Union[str, dict]) -> EmailData:
        """
        Parse email from JSON data.
        
        Args:
            json_data: JSON string or dictionary containing email data
            
        Returns:
            EmailData object
        """
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            return EmailData.from_dict(data)
            
        except Exception as e:
            logger.error(f"Failed to parse email from JSON: {e}")
            raise
    
    @staticmethod
    def batch_parse_directory(directory_path: Union[str, Path], 
                            pattern: str = "*.eml") -> List[EmailData]:
        """
        Parse all email files in a directory.
        
        Args:
            directory_path: Path to directory containing email files
            pattern: File pattern to match (default: *.eml)
            
        Returns:
            List of EmailData objects
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        emails = []
        email_files = list(directory_path.glob(pattern))
        
        logger.info(f"Found {len(email_files)} email files in {directory_path}")
        
        for email_file in email_files:
            try:
                email_data = EmailParser.from_file(email_file)
                emails.append(email_data)
                logger.debug(f"Successfully parsed: {email_file.name}")
            except Exception as e:
                logger.error(f"Failed to parse {email_file.name}: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(emails)} out of {len(email_files)} email files")
        return emails
    
    @staticmethod
    def create_sample_email_data() -> EmailData:
        """
        Create a sample EmailData object for testing purposes.
        
        Returns:
            Sample EmailData object
        """
        from datetime import datetime
        from ..models.email_model import EmailAttachment
        
        sample_attachment = EmailAttachment(
            filename="document.pdf",
            content_type="application/pdf",
            size=1024000,  # 1MB
            content=b"sample pdf content"
        )
        
        return EmailData(
            subject="Sample Email Subject",
            sender="sender@example.com",
            recipients=["recipient@company.com"],
            cc_recipients=["cc@company.com"],
            bcc_recipients=[],
            body_text="This is a sample email body with some text content.",
            body_html="<p>This is a sample email body with some <strong>HTML</strong> content.</p>",
            message_id="<sample@example.com>",
            received_date=datetime.now(),
            sent_date=datetime.now(),
            headers={
                "From": "sender@example.com",
                "To": "recipient@company.com",
                "Subject": "Sample Email Subject",
                "Date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            },
            attachments=[sample_attachment],
            priority="normal"
        )
    
    @staticmethod
    def validate_email_data(email_data: EmailData) -> bool:
        """
        Validate EmailData object for completeness.
        
        Args:
            email_data: EmailData object to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not email_data.subject and not email_data.body_text:
                logger.warning("Email has no subject or body content")
                return False
            
            if not email_data.sender:
                logger.warning("Email has no sender")
                return False
            
            if not email_data.recipients:
                logger.warning("Email has no recipients")
                return False
            
            # Validate email addresses (basic check)
            all_addresses = [email_data.sender] + email_data.recipients + email_data.cc_recipients + email_data.bcc_recipients
            for addr in all_addresses:
                if addr and '@' not in addr:
                    logger.warning(f"Invalid email address format: {addr}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating email data: {e}")
            return False