"""
Zato master orchestration service for email processing.

This service coordinates the complete email processing flow:
1. Evaluate routing rules
2. Route to appropriate SQS queue
3. Update statistics
"""

from zato.server.service import Service


class EmailOrchestratorService(Service):
    """
    Master orchestration service for email processing.
    Coordinates: parsing → rule evaluation → SQS routing
    
    Input:
        email_data (dict): Email data to process
        dry_run (bool): If True, don't actually send to SQS
        
    Output:
        success (bool): Whether processing was successful
        queue_name (str): Queue the email was routed to
        matched_rule (str): Name of matched rule (or 'none')
        message_id (str): SQS message ID (if not dry_run)
        dry_run (bool): Whether this was a dry run
    """
    
    name = 'email.orchestrator.process'
    
    def handle(self):
        email_data = self.request.payload if self.request.payload else {}
        dry_run = email_data.get('dry_run', False)
        
        subject = email_data.get('subject', '')[:50]  # Truncate for logging
        self.logger.info(f"Processing email: {subject}")
        
        try:
            # Step 1: Evaluate routing rules
            rule_result = self.invoke(
                'email.rules.evaluate',
                email_data
            )
            
            matched = rule_result.get('matched', False)
            queue_name = rule_result.get('action', 'default')
            rule_name = rule_result.get('rule_name', 'none')
            
            # Step 2: Route to appropriate queue (unless dry run)
            if not dry_run:
                sqs_result = self.invoke(
                    'email.outbound.sqs-send',
                    {
                        'email_data': email_data,
                        'queue_name': queue_name
                    }
                )
                
                success = sqs_result.get('success', False)
                message_id = sqs_result.get('message_id', '')
            else:
                success = True
                message_id = 'DRY_RUN'
            
            # Step 3: Update statistics
            self._update_stats(queue_name, matched, success)
            
            # Return result
            self.response.payload = {
                'success': success,
                'queue_name': queue_name,
                'matched_rule': rule_name,
                'message_id': message_id,
                'dry_run': dry_run
            }
            
        except Exception as e:
            self.logger.error(f"Error in orchestration: {e}")
            self.response.payload = {
                'success': False,
                'error': str(e)
            }
    
    def _update_stats(self, queue_name, matched, success):
        """Update processing statistics in Redis"""
        try:
            # Increment counters
            self.kvdb.conn.incr('stats.email.total_processed')
            
            if success:
                self.kvdb.conn.incr('stats.email.successful_routes')
            else:
                self.kvdb.conn.incr('stats.email.failed_routes')
            
            if matched:
                self.kvdb.conn.incr(f'stats.email.queue.{queue_name}')
                
        except Exception as e:
            # Don't fail the whole operation if stats update fails
            # Log error without exposing internal state values
            self.logger.error(f"Error updating email processing statistics: {e}")
