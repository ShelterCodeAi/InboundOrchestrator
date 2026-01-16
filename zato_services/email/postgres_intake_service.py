"""
Zato service for fetching emails from PostgreSQL database.

This service is scheduled to run periodically to fetch unprocessed emails
from the PostgreSQL database and forward them to the orchestration service.
"""

from zato.server.service import Service


class PostgresEmailIntakeService(Service):
    """
    Scheduled service to fetch emails from PostgreSQL database.
    
    This service:
    1. Queries unprocessed emails from the database
    2. Invokes the orchestration service for each email
    3. Marks emails as processed
    """
    
    name = 'email.intake.postgres-fetch'
    
    def handle(self):
        # Get batch size from request or use default
        batch_size = self.request.payload.get('batch_size', 100) if self.request.payload else 100
        
        try:
            # Get SQL connection defined in web admin
            with self.outgoing.sql.get('email_db').session() as session:
                # Query emails from database
                query = """
                    SELECT email_id, subject, body, from_address, headers, 
                           email_message_id, time_received
                    FROM email_messages.email_gmail
                    WHERE processed = false
                    LIMIT :batch_size
                """
                
                results = session.execute(query, {'batch_size': batch_size})
                
                processed_count = 0
                failed_count = 0
                
                for row in results:
                    try:
                        # Create email payload
                        email_payload = {
                            'email_id': row.email_id,
                            'subject': row.subject,
                            'body_text': row.body,
                            'sender': row.from_address,
                            'headers': row.headers,
                            'message_id': row.email_message_id,
                            'received_date': row.time_received.isoformat() if row.time_received else None
                        }
                        
                        # Invoke email processing service
                        result = self.invoke(
                            'email.orchestrator.process',
                            email_payload
                        )
                        
                        if result.get('success', False):
                            # Mark as processed
                            session.execute(
                                "UPDATE email_messages.email_gmail SET processed = true WHERE email_id = :id",
                                {'id': row.email_id}
                            )
                            session.commit()
                            processed_count += 1
                        else:
                            self.logger.error(f"Failed to process email {row.email_id}: {result.get('error')}")
                            failed_count += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error processing email {row.email_id}: {e}")
                        failed_count += 1
                        session.rollback()
                
                self.logger.info(f"Processed {processed_count} emails, {failed_count} failed")
                
                self.response.payload = {
                    'success': True,
                    'processed': processed_count,
                    'failed': failed_count
                }
                
        except Exception as e:
            self.logger.error(f"Error in PostgreSQL intake: {e}")
            self.response.payload = {
                'success': False,
                'error': str(e)
            }
