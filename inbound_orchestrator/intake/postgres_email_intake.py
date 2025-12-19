"""
Postgres email intake utility for processing emails from the email_gmail table.

This module provides functionality to connect to a Postgres database,
query emails from the email_gmail table, and map them to EmailData objects
for processing by the InboundOrchestrator.

Note: RFC 2047 encoded text in subject/body fields is not decoded and may
appear in encoded form. This is a known limitation.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import email.utils

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import sql
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    sql = None

from ..models.email_model import EmailData, EmailAttachment

logger = logging.getLogger(__name__)


class PostgresEmailIntake:
    """
    Utility class for retrieving emails from Postgres email_gmail table.
    
    This class handles:
    - Database connection management
    - Querying email records from email_gmail and email_message_general tables
    - Mapping database rows to EmailData objects
    """
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 5432,
                 database: str = 'email_db',
                 user: str = 'postgres',
                 password: str = '',
                 schema: str = 'email_messages'):
        """
        Initialize Postgres email intake.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            schema: Database schema containing email tables (default: email_messages)
        """
        if psycopg2 is None:
            raise ImportError(
                "psycopg2 is required for Postgres email intake. "
                "Install it with: pip install psycopg2-binary"
            )
        
        # Validate schema name to prevent SQL injection
        # Schema names must be valid PostgreSQL identifiers
        if not schema or not all(c.isalnum() or c == '_' for c in schema):
            raise ValueError(
                f"Invalid schema name: {schema}. "
                "Schema name must contain only alphanumeric characters and underscores."
            )
        
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.schema = schema
        self._connection = None
        
        logger.info(f"PostgresEmailIntake initialized for {host}:{port}/{database}")
    
    def connect(self) -> None:
        """Establish connection to the database."""
        try:
            self._connection = psycopg2.connect(**self.connection_params)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def _build_email_query(self, where_clause: str = "") -> str:
        """
        Build the SQL query for fetching emails.
        
        Args:
            where_clause: Optional WHERE clause (without the WHERE keyword)
            
        Returns:
            SQL query string with schema safely embedded using sql.Identifier
        """
        # Build base query with safe schema identifier
        query_template = """
            SELECT 
                g.em_id,
                g.headers,
                g.gmail_api_thread_id,
                g.gmail_api_id,
                g.json_object,
                m.email_client,
                m.email_id,
                m.email_message_id,
                m.has_attachment,
                m.from_name,
                m.from_address,
                m.time_received,
                m.subject,
                m.body,
                m.raw_mime
            FROM {schema}.email_gmail g
            INNER JOIN {schema}.email_message_general m ON g.em_id = m.em_id
        """
        
        if where_clause:
            query_template += f"\n            WHERE {where_clause}"
        
        # Use sql.SQL and sql.Identifier to safely compose the query
        query = sql.SQL(query_template).format(
            schema=sql.Identifier(self.schema)
        )
        
        return query
    
    def fetch_emails_by_email_id(self, email_id: int) -> List[EmailData]:
        """
        Fetch all emails from email_gmail table where email_id matches.
        
        Args:
            email_id: The email_id to filter by
            
        Returns:
            List of EmailData objects
        """
        if not self._connection:
            raise RuntimeError("Not connected to database. Call connect() first or use context manager.")
        
        try:
            with self._connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build query with parameterized email_id to prevent SQL injection
                query = self._build_email_query("m.email_id = %s")
                
                cursor.execute(query, (email_id,))
                rows = cursor.fetchall()
                
                logger.info(f"Fetched {len(rows)} email(s) for email_id={email_id}")
                
                emails = []
                for row in rows:
                    try:
                        email_data = self._map_row_to_email_data(row)
                        emails.append(email_data)
                    except Exception as e:
                        logger.error(f"Failed to map row em_id={row.get('em_id')}: {e}")
                        continue
                
                return emails
                
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            raise
    
    def _map_row_to_email_data(self, row: Dict[str, Any]) -> EmailData:
        """
        Map a database row to an EmailData object.
        
        Args:
            row: Database row as dictionary
            
        Returns:
            EmailData object
            
        Note:
            RFC 2047 encoded text in subject/body may not be decoded and 
            could appear in encoded form.
        """
        # Extract basic fields
        subject = row.get('subject', '')
        body_text = row.get('body', '')
        sender = row.get('from_address', '')
        message_id = row.get('email_message_id', f"<db-{row.get('em_id')}@localhost>")
        
        # Parse dates
        received_date = row.get('time_received')
        if received_date is None:
            received_date = datetime.now()
        elif isinstance(received_date, str):
            received_date = datetime.fromisoformat(received_date)
        
        # Parse headers from JSONB
        headers = {}
        if row.get('headers'):
            if isinstance(row['headers'], dict):
                headers = row['headers']
            elif isinstance(row['headers'], str):
                try:
                    headers = json.loads(row['headers'])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse headers for em_id={row.get('em_id')}")
        
        # Extract recipients, cc, bcc from headers or json_object
        recipients = []
        cc_recipients = []
        bcc_recipients = []
        sent_date = None
        
        # Try to get from headers first
        if headers:
            to_header = headers.get('To', headers.get('to', ''))
            if to_header:
                recipients = [addr.strip() for addr in to_header.split(',') if addr.strip()]
            
            cc_header = headers.get('Cc', headers.get('cc', ''))
            if cc_header:
                cc_recipients = [addr.strip() for addr in cc_header.split(',') if addr.strip()]
            
            bcc_header = headers.get('Bcc', headers.get('bcc', ''))
            if bcc_header:
                bcc_recipients = [addr.strip() for addr in bcc_header.split(',') if addr.strip()]
            
            # Try to extract sent date from headers
            date_header = headers.get('Date', headers.get('date', ''))
            if date_header:
                try:
                    sent_date = email.utils.parsedate_to_datetime(date_header)
                except (TypeError, ValueError):
                    pass
        
        # Try to get from json_object if available and recipients are empty
        if not recipients and row.get('json_object'):
            try:
                json_obj = row['json_object']
                if isinstance(json_obj, str):
                    json_obj = json.loads(json_obj)
                
                # Try various common fields in json_object
                if 'to' in json_obj:
                    to_val = json_obj['to']
                    if isinstance(to_val, list):
                        recipients = to_val
                    elif isinstance(to_val, str):
                        recipients = [addr.strip() for addr in to_val.split(',') if addr.strip()]
                
                if 'cc' in json_obj:
                    cc_val = json_obj['cc']
                    if isinstance(cc_val, list):
                        cc_recipients = cc_val
                    elif isinstance(cc_val, str):
                        cc_recipients = [addr.strip() for addr in cc_val.split(',') if addr.strip()]
                
                if 'bcc' in json_obj:
                    bcc_val = json_obj['bcc']
                    if isinstance(bcc_val, list):
                        bcc_recipients = bcc_val
                    elif isinstance(bcc_val, str):
                        bcc_recipients = [addr.strip() for addr in bcc_val.split(',') if addr.strip()]
                        
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug(f"Could not extract recipients from json_object: {e}")
        
        # If still no recipients, use a default
        if not recipients:
            recipients = ['unknown@localhost']
        
        # Handle attachments if indicated
        attachments = []
        if row.get('has_attachment'):
            # Note: Actual attachment data is not in these tables
            # We just note that attachments exist
            logger.debug(f"Email em_id={row.get('em_id')} has attachments (data not loaded)")
        
        # Create EmailData object
        email_data = EmailData(
            subject=subject,
            sender=sender,
            recipients=recipients,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            body_text=body_text,
            body_html=None,  # HTML body not available in this schema
            message_id=message_id,
            received_date=received_date,
            sent_date=sent_date,
            headers=headers,
            attachments=attachments,
            priority="normal"  # Priority not in schema, default to normal
        )
        
        return email_data
    
    def fetch_all_emails(self, limit: Optional[int] = None) -> List[EmailData]:
        """
        Fetch all emails from email_gmail table.
        
        Args:
            limit: Optional limit on number of emails to fetch
            
        Returns:
            List of EmailData objects
        """
        if not self._connection:
            raise RuntimeError("Not connected to database. Call connect() first or use context manager.")
        
        try:
            with self._connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build query without WHERE clause
                query = self._build_email_query()
                
                # Add LIMIT if specified (using parameterized query)
                if limit:
                    # Properly compose SQL with LIMIT using sql.Composed
                    query = sql.Composed([query, sql.SQL(" LIMIT %s")])
                    cursor.execute(query, (int(limit),))
                else:
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                
                logger.info(f"Fetched {len(rows)} email(s) from database")
                
                emails = []
                for row in rows:
                    try:
                        email_data = self._map_row_to_email_data(row)
                        emails.append(email_data)
                    except Exception as e:
                        logger.error(f"Failed to map row em_id={row.get('em_id')}: {e}")
                        continue
                
                return emails
                
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self._connection:
                self.connect()
                should_disconnect = True
            else:
                should_disconnect = False
            
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            if should_disconnect:
                self.disconnect()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
