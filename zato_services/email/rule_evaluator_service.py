"""
Zato service for evaluating email against routing rules.

This service evaluates emails against the rules stored in the Key-Value DB
and returns the matching rule/action for routing decisions.
"""

from zato.server.service import Service
import json


class RuleEvaluatorService(Service):
    """
    Evaluate email against routing rules.
    
    Input:
        Email data dictionary with fields like subject, sender, body_text, etc.
        
    Output:
        matched (bool): Whether a rule matched
        rule_name (str): Name of the matched rule (if any)
        action (str): Action/queue name to route to
    """
    
    name = 'email.rules.evaluate'
    
    def handle(self):
        email_data = self.request.payload if self.request.payload else {}
        
        try:
            # Get all rules from KV DB
            rules = []
            for key in self.kvdb.conn.keys('email.rule.*'):
                rule_json = self.kvdb.conn.get(key)
                if rule_json:
                    rule = json.loads(rule_json)
                    if rule.get('enabled', False):
                        rules.append(rule)
            
            # Sort by priority (highest first)
            rules.sort(key=lambda r: r.get('priority', 0), reverse=True)
            
            # Evaluate rules
            matched_rule = None
            for rule in rules:
                if self._evaluate_condition(rule['condition'], email_data):
                    matched_rule = rule
                    self.logger.info(f"Rule '{rule['name']}' matched for email: {email_data.get('subject', '')[:50]}")
                    break
            
            # Return matching action or default
            if matched_rule:
                self.response.payload = {
                    'matched': True,
                    'rule_name': matched_rule['name'],
                    'action': matched_rule['action']
                }
            else:
                self.response.payload = {
                    'matched': False,
                    'action': 'default'
                }
                
        except Exception as e:
            self.logger.error(f"Error evaluating rules: {e}")
            self.response.payload = {
                'matched': False,
                'action': 'default',
                'error': str(e)
            }
    
    def _evaluate_condition(self, condition, email_data):
        """
        Evaluate rule condition against email data.
        Uses restricted evaluation with safe operators only.
        
        Note: This uses eval() with a restricted context and no __builtins__.
        For production use, consider using a dedicated expression library
        like 'simpleeval' for enhanced security.
        
        Args:
            condition (str): Python expression to evaluate
            email_data (dict): Email data dictionary
            
        Returns:
            bool: Result of condition evaluation
        """
        try:
            # Validate condition doesn't contain dangerous patterns
            dangerous_patterns = ['__', 'import', 'exec', 'compile', 'open', 'file']
            if any(pattern in condition.lower() for pattern in dangerous_patterns):
                self.logger.error(f"Condition contains forbidden pattern: {condition}")
                return False
            
            # Create safe evaluation context with email fields only
            context = {
                'subject': email_data.get('subject', ''),
                'sender': email_data.get('sender', ''),
                'sender_domain': email_data.get('sender', '').split('@')[-1] if '@' in email_data.get('sender', '') else '',
                'priority': email_data.get('priority', 'normal'),
                'body_text': email_data.get('body_text', ''),
                'has_attachments': len(email_data.get('attachments', [])) > 0,
                'attachment_count': len(email_data.get('attachments', [])),
                'recipients': email_data.get('recipients', []),
                'cc_recipients': email_data.get('cc_recipients', []),
            }
            
            # Evaluate condition with no builtins for security
            # Note: For production, consider using 'simpleeval' library
            result = eval(condition, {"__builtins__": {}}, context)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
