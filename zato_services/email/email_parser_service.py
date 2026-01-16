"""
Zato service for parsing raw email content into structured data.

This service wraps the existing email parsing functionality from InboundOrchestrator
and exposes it as a Zato service for the ESB migration.
"""

from zato.server.service import Service
from email import message_from_string
from datetime import datetime
import json


class EmailParserService(Service):
    """
    Zato service for parsing raw email content into structured data.
    
    Input:
        raw_email (str): Raw email content as string
        
    Output:
        Structured email data dictionary with:
        - subject, sender, recipients, cc_recipients
        - body_text, headers, received_date, message_id
    """
    
    name = 'email.parser.parse-raw'
    
    def handle(self):
        # Get raw email from request
        raw_email = self.request.payload.get('raw_email')
        
        if not raw_email:
            self.response.payload = {
                'success': False,
                'error': 'No raw_email provided'
            }
            return
        
        try:
            # Parse email
            msg = message_from_string(raw_email)
            
            # Extract email data
            email_data = {
                'subject': msg.get('subject', ''),
                'sender': msg.get('from', ''),
                'recipients': msg.get('to', '').split(',') if msg.get('to') else [],
                'cc_recipients': msg.get('cc', '').split(',') if msg.get('cc') else [],
                'body_text': self._get_body(msg),
                'headers': dict(msg.items()),
                'received_date': datetime.now().isoformat(),
                'message_id': msg.get('message-id', '')
            }
            
            # Return parsed data
            self.response.payload = {
                'success': True,
                'email_data': email_data
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing email: {e}")
            self.response.payload = {
                'success': False,
                'error': str(e)
            }
    
    def _get_body(self, msg):
        """Extract email body text"""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        return part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                return msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except Exception as e:
            self.logger.error(f"Error extracting email body: {e}")
            return ''
        return ''
