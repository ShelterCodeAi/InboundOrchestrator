"""
Email data model for representing email objects in the rules engine.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import email
from email.message import EmailMessage
import json


@dataclass
class EmailAttachment:
    """Represents an email attachment."""
    filename: str
    content_type: str
    size: int
    content: Optional[bytes] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rule evaluation."""
        return {
            'filename': self.filename,
            'content_type': self.content_type,
            'size': self.size,
            'has_content': self.content is not None
        }


@dataclass
class EmailData:
    """
    Email data model that can be used with the rule engine.
    
    This class represents all the relevant email properties that can be
    evaluated by rules to determine routing decisions.
    """
    # Core email properties
    subject: str
    sender: str
    recipients: List[str]
    cc_recipients: List[str]
    bcc_recipients: List[str]
    body_text: str
    body_html: Optional[str]
    
    # Metadata
    message_id: str
    received_date: datetime
    sent_date: Optional[datetime]
    headers: Dict[str, str]
    
    # Attachments
    attachments: List[EmailAttachment]
    
    # Additional properties for rule evaluation
    priority: str = "normal"  # low, normal, high, urgent
    sender_domain: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Extract sender domain if not provided
        if self.sender_domain is None and '@' in self.sender:
            self.sender_domain = self.sender.split('@')[1].lower()
    
    @classmethod
    def from_email_message(cls, message: EmailMessage) -> 'EmailData':
        """
        Create EmailData from an email.message.EmailMessage object.
        
        Args:
            message: EmailMessage object to parse
            
        Returns:
            EmailData instance
        """
        # Extract basic fields
        subject = message.get('Subject', '').strip()
        sender = message.get('From', '').strip()
        
        # Parse recipients
        recipients = []
        if message.get('To'):
            recipients = [addr.strip() for addr in message.get('To').split(',')]
        
        cc_recipients = []
        if message.get('Cc'):
            cc_recipients = [addr.strip() for addr in message.get('Cc').split(',')]
            
        bcc_recipients = []
        if message.get('Bcc'):
            bcc_recipients = [addr.strip() for addr in message.get('Bcc').split(',')]
        
        # Extract body content
        body_text = ""
        body_html = None
        
        # Helper to get content from both old and new email API
        def get_part_content(part):
            """Get content from email part, compatible with both old and new API."""
            if hasattr(part, 'get_content'):
                return part.get_content()
            else:
                # Fallback to get_payload for older API
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    return payload.decode('utf-8', errors='ignore')
                return payload or ""
        
        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body_text = get_part_content(part)
                elif content_type == "text/html":
                    body_html = get_part_content(part)
        else:
            if message.get_content_type() == "text/plain":
                body_text = get_part_content(message)
            elif message.get_content_type() == "text/html":
                body_html = get_part_content(message)
        
        # Parse dates
        received_date = datetime.now()
        sent_date = None
        if message.get('Date'):
            try:
                sent_date = email.utils.parsedate_to_datetime(message.get('Date'))
            except (TypeError, ValueError):
                pass
        
        # Extract headers
        headers = dict(message.items())
        
        # Extract attachments
        attachments = []
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        # Get content compatible with both APIs
                        if hasattr(part, 'get_content'):
                            content = part.get_content()
                        else:
                            content = part.get_payload(decode=True)
                        
                        content_len = len(content) if content and hasattr(content, '__len__') else 0
                        attachment = EmailAttachment(
                            filename=filename,
                            content_type=part.get_content_type(),
                            size=content_len,
                            content=content if isinstance(content, bytes) else content.encode('utf-8') if content else b""
                        )
                        attachments.append(attachment)
        
        # Determine priority
        priority = "normal"
        priority_header = message.get('X-Priority') or message.get('Priority')
        if priority_header:
            priority_header = priority_header.lower()
            if 'high' in priority_header or '1' in priority_header:
                priority = "high"
            elif 'urgent' in priority_header:
                priority = "urgent"
            elif 'low' in priority_header or '5' in priority_header:
                priority = "low"
        
        return cls(
            subject=subject,
            sender=sender,
            recipients=recipients,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            body_text=body_text,
            body_html=body_html,
            message_id=message.get('Message-ID', ''),
            received_date=received_date,
            sent_date=sent_date,
            headers=headers,
            attachments=attachments,
            priority=priority
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailData':
        """
        Create EmailData from a dictionary.
        
        Args:
            data: Dictionary containing email data
            
        Returns:
            EmailData instance
        """
        # Parse attachments
        attachments = []
        if 'attachments' in data:
            for att_data in data['attachments']:
                attachments.append(EmailAttachment(**att_data))
        
        # Parse dates
        received_date = data.get('received_date')
        if isinstance(received_date, str):
            received_date = datetime.fromisoformat(received_date)
        elif received_date is None:
            received_date = datetime.now()
            
        sent_date = data.get('sent_date')
        if isinstance(sent_date, str):
            sent_date = datetime.fromisoformat(sent_date)
        
        return cls(
            subject=data.get('subject', ''),
            sender=data.get('sender', ''),
            recipients=data.get('recipients', []),
            cc_recipients=data.get('cc_recipients', []),
            bcc_recipients=data.get('bcc_recipients', []),
            body_text=data.get('body_text', ''),
            body_html=data.get('body_html'),
            message_id=data.get('message_id', ''),
            received_date=received_date,
            sent_date=sent_date,
            headers=data.get('headers', {}),
            attachments=attachments,
            priority=data.get('priority', 'normal')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert EmailData to a dictionary suitable for rule evaluation.
        
        Returns:
            Dictionary representation of the email data
        """
        return {
            # Basic properties
            'subject': self.subject,
            'sender': self.sender,
            'sender_domain': self.sender_domain,
            'recipients': self.recipients,
            'cc_recipients': self.cc_recipients,
            'bcc_recipients': self.bcc_recipients,
            'body_text': self.body_text,
            'body_html': self.body_html,
            'message_id': self.message_id,
            'priority': self.priority,
            
            # Computed properties for rule evaluation
            'recipient_count': len(self.recipients),
            'cc_count': len(self.cc_recipients),
            'bcc_count': len(self.bcc_recipients),
            'total_recipients': len(self.recipients) + len(self.cc_recipients) + len(self.bcc_recipients),
            'has_attachments': len(self.attachments) > 0,
            'attachment_count': len(self.attachments),
            'attachment_filenames': [att.filename for att in self.attachments],
            'attachment_types': [att.content_type for att in self.attachments],
            'total_attachment_size': sum(att.size for att in self.attachments),
            
            # Text analysis properties
            'subject_length': len(self.subject),
            'body_length': len(self.body_text),
            'has_html_body': self.body_html is not None,
            
            # Date properties
            'received_date': self.received_date.isoformat(),
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'received_hour': self.received_date.hour,
            'received_day_of_week': self.received_date.weekday(),  # Monday is 0
            
            # Headers
            'headers': self.headers
        }
    
    def matches_sender_pattern(self, pattern: str) -> bool:
        """Check if sender matches a pattern (supports wildcards)."""
        import fnmatch
        return fnmatch.fnmatch(self.sender.lower(), pattern.lower())
    
    def contains_keyword(self, keyword: str, in_subject: bool = True, in_body: bool = True) -> bool:
        """Check if email contains a specific keyword."""
        keyword = keyword.lower()
        if in_subject and keyword in self.subject.lower():
            return True
        if in_body and keyword in self.body_text.lower():
            return True
        return False
    
    def has_attachment_type(self, content_type: str) -> bool:
        """Check if email has attachment of specific content type."""
        return any(att.content_type == content_type for att in self.attachments)
    
    def __str__(self) -> str:
        """String representation of the email."""
        return f"EmailData(subject='{self.subject[:50]}...', sender='{self.sender}', attachments={len(self.attachments)})"