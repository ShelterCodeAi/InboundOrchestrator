"""
Tests for Zato rule evaluator service.
"""
import pytest
import json


class TestRuleEvaluatorLogic:
    """Test suite for rule evaluation logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_rules = [
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
    
    def _evaluate_condition(self, condition, email_data):
        """
        Simulate the rule evaluation logic with security checks.
        """
        try:
            # Validate condition doesn't contain dangerous patterns
            dangerous_patterns = ['__', 'import', 'exec', 'compile', 'open', 'file']
            if any(pattern in condition.lower() for pattern in dangerous_patterns):
                return False
            
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
            
            result = eval(condition, {"__builtins__": {}}, context)
            return bool(result)
        except Exception:
            return False
    
    def test_urgent_email_by_priority(self):
        """Test urgent email detection by priority field."""
        email_data = {
            'subject': 'Important message',
            'sender': 'user@example.com',
            'priority': 'urgent',
            'body_text': 'This is urgent'
        }
        
        rule = self.sample_rules[0]
        assert self._evaluate_condition(rule['condition'], email_data) == True
    
    def test_urgent_email_by_subject(self):
        """Test urgent email detection by subject keyword."""
        email_data = {
            'subject': 'URGENT: Server down',
            'sender': 'admin@example.com',
            'priority': 'normal',
            'body_text': 'Server is down'
        }
        
        rule = self.sample_rules[0]
        assert self._evaluate_condition(rule['condition'], email_data) == True
    
    def test_support_email(self):
        """Test support email detection."""
        email_data = {
            'subject': 'Need help with account',
            'sender': 'customer@example.com',
            'priority': 'normal',
            'body_text': 'I need help'
        }
        
        rule = self.sample_rules[1]
        assert self._evaluate_condition(rule['condition'], email_data) == True
    
    def test_billing_email(self):
        """Test billing email detection."""
        email_data = {
            'subject': 'Invoice for January',
            'sender': 'billing@company.com',
            'priority': 'normal',
            'body_text': 'Please find attached invoice'
        }
        
        rule = self.sample_rules[2]
        assert self._evaluate_condition(rule['condition'], email_data) == True
    
    def test_no_match(self):
        """Test email that doesn't match any rules."""
        email_data = {
            'subject': 'Regular email',
            'sender': 'user@example.com',
            'priority': 'normal',
            'body_text': 'Just a regular message'
        }
        
        matches = [
            self._evaluate_condition(rule['condition'], email_data)
            for rule in self.sample_rules
        ]
        
        assert not any(matches)
    
    def test_rule_priority_ordering(self):
        """Test that rules are evaluated in priority order."""
        # Sort rules by priority (highest first)
        sorted_rules = sorted(
            self.sample_rules,
            key=lambda r: r.get('priority', 0),
            reverse=True
        )
        
        assert sorted_rules[0]['name'] == 'urgent_emails'
        assert sorted_rules[1]['name'] == 'support_emails'
        assert sorted_rules[2]['name'] == 'billing_emails'
    
    def test_sender_domain_extraction(self):
        """Test sender domain extraction."""
        email_data = {
            'subject': 'Test',
            'sender': 'user@example.com',
            'priority': 'normal',
            'body_text': ''
        }
        
        sender_domain = email_data.get('sender', '').split('@')[-1] if '@' in email_data.get('sender', '') else ''
        assert sender_domain == 'example.com'
    
    def test_attachment_detection(self):
        """Test attachment detection in context."""
        email_data_with_attachments = {
            'subject': 'Test',
            'sender': 'user@example.com',
            'attachments': ['file1.pdf', 'file2.doc']
        }
        
        has_attachments = len(email_data_with_attachments.get('attachments', [])) > 0
        attachment_count = len(email_data_with_attachments.get('attachments', []))
        
        assert has_attachments == True
        assert attachment_count == 2
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive subject matching."""
        email_data = {
            'subject': 'HELP ME PLEASE',
            'sender': 'user@example.com',
            'priority': 'normal',
            'body_text': ''
        }
        
        rule = self.sample_rules[1]  # support_emails rule
        assert self._evaluate_condition(rule['condition'], email_data) == True
    
    def test_invalid_condition_handling(self):
        """Test handling of invalid rule conditions."""
        invalid_condition = "invalid python syntax @@@ error"
        email_data = {
            'subject': 'Test',
            'sender': 'user@example.com'
        }
        
        result = self._evaluate_condition(invalid_condition, email_data)
        assert result == False
    
    def test_dangerous_pattern_rejection(self):
        """Test that dangerous patterns are rejected."""
        dangerous_conditions = [
            "__import__('os').system('ls')",
            "import os",
            "exec('print(1)')",
            "compile('x=1', '', 'exec')",
            "open('/etc/passwd')",
            "__builtins__['eval']"
        ]
        
        email_data = {
            'subject': 'Test',
            'sender': 'user@example.com'
        }
        
        for condition in dangerous_conditions:
            result = self._evaluate_condition(condition, email_data)
            assert result == False, f"Dangerous condition should be rejected: {condition}"


class TestRuleStorage:
    """Test rule storage format."""
    
    def test_rule_json_serialization(self):
        """Test that rules can be serialized to JSON."""
        rule = {
            'name': 'test_rule',
            'description': 'Test rule',
            'condition': "priority == 'urgent'",
            'action': 'high_priority',
            'priority': 100,
            'enabled': True
        }
        
        json_str = json.dumps(rule)
        parsed_rule = json.loads(json_str)
        
        assert parsed_rule['name'] == 'test_rule'
        assert parsed_rule['condition'] == "priority == 'urgent'"
        assert parsed_rule['enabled'] == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
