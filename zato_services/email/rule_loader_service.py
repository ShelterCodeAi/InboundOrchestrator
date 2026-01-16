"""
Zato service for loading email routing rules into the Key-Value DB.

This service loads email routing rules from configuration and stores them
in Redis via Zato's Key-Value DB for use by the rule evaluation service.
"""

from zato.server.service import Service
import json


class RuleLoaderService(Service):
    """
    Load email routing rules from config into Key-Value DB.
    
    Rules are stored in Redis with keys like: email.rule.<rule_name>
    Each rule contains:
    - name: Rule identifier
    - description: Human-readable description
    - condition: Python expression to evaluate
    - action: Queue name or action to take
    - priority: Rule priority (higher numbers evaluated first)
    - enabled: Whether the rule is active
    """
    
    name = 'email.rules.load-from-config'
    
    def handle(self):
        # Get rules from request or use default examples
        rules = self.request.payload.get('rules') if self.request.payload else []
        
        # If no rules provided, load example rules
        if not rules:
            rules = [
                {
                    'name': 'urgent_emails',
                    'description': 'Route urgent emails to high priority queue',
                    'condition': "priority == 'urgent' or 'URGENT' in subject",
                    'action': 'high_priority',
                    'priority': 100,
                    'enabled': True
                },
                {
                    'name': 'support_emails',
                    'description': 'Route support emails based on subject keywords',
                    'condition': "'help' in subject.lower() or 'support' in subject.lower()",
                    'action': 'support',
                    'priority': 80,
                    'enabled': True
                },
                {
                    'name': 'billing_emails',
                    'description': 'Route billing-related emails',
                    'condition': "'billing' in subject.lower() or 'invoice' in subject.lower()",
                    'action': 'billing',
                    'priority': 70,
                    'enabled': True
                }
            ]
        
        try:
            # Store rules in KV DB
            loaded_count = 0
            for rule in rules:
                key = f"email.rule.{rule['name']}"
                self.kvdb.conn.set(key, json.dumps(rule))
                loaded_count += 1
            
            self.logger.info(f"Loaded {loaded_count} rules into KV DB")
            self.response.payload = {
                'success': True,
                'loaded': loaded_count
            }
            
        except Exception as e:
            self.logger.error(f"Error loading rules: {e}")
            self.response.payload = {
                'success': False,
                'error': str(e)
            }
