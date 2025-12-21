#!/usr/bin/env python3
"""
Tests for the EmailRuleEngine.
"""
import unittest
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator.rules.rule_engine import EmailRuleEngine, EmailRule
from inbound_orchestrator.models.email_model import EmailData


class TestEmailRuleEngine(unittest.TestCase):
    """Test cases for EmailRuleEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = EmailRuleEngine()
        
        # Create sample rules
        self.urgent_rule = EmailRule(
            name="urgent_emails",
            description="Route urgent emails",
            condition="priority == 'urgent' or contains(subject, 'URGENT')",
            action="high_priority",
            priority=100,
            enabled=True
        )
        
        self.support_rule = EmailRule(
            name="support_emails",
            description="Route support emails",
            condition="contains(subject, 'help') or contains(subject, 'support')",
            action="support_queue",
            priority=80,
            enabled=True
        )
        
        # Create sample email
        self.sample_email = EmailData(
            subject="URGENT: Need help with login",
            sender="user@example.com",
            recipients=["support@company.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="I urgently need help with my login issue.",
            body_html=None,
            message_id="<test@example.com>",
            received_date=datetime.now(),
            sent_date=datetime.now(),
            headers={},
            attachments=[],
            priority="urgent"
        )
    
    def test_add_rule(self):
        """Test adding rules to the engine."""
        self.engine.add_rule(self.urgent_rule)
        self.assertEqual(len(self.engine.list_rules()), 1)
        
        rules = self.engine.list_rules()
        self.assertEqual(rules[0].name, "urgent_emails")
    
    def test_add_multiple_rules(self):
        """Test adding multiple rules."""
        rules = [self.urgent_rule, self.support_rule]
        self.engine.add_rules(rules)
        
        self.assertEqual(len(self.engine.list_rules()), 2)
    
    def test_invalid_rule_syntax(self):
        """Test handling of invalid rule syntax."""
        invalid_rule = EmailRule(
            name="invalid_rule",
            description="Invalid syntax rule",
            condition="invalid syntax here!!",
            action="test_queue",
            priority=50,
            enabled=True
        )
        
        with self.assertRaises(ValueError):
            self.engine.add_rule(invalid_rule)
    
    def test_evaluate_email(self):
        """Test email evaluation against rules."""
        self.engine.add_rule(self.urgent_rule)
        self.engine.add_rule(self.support_rule)
        
        matching_rules = self.engine.evaluate_email(self.sample_email)
        
        # Should match both rules (urgent and support)
        self.assertEqual(len(matching_rules), 2)
        
        # Should be sorted by priority (urgent rule first)
        self.assertEqual(matching_rules[0].name, "urgent_emails")
        self.assertEqual(matching_rules[1].name, "support_emails")
    
    def test_get_first_matching_action(self):
        """Test getting the first matching action."""
        self.engine.add_rule(self.urgent_rule)
        self.engine.add_rule(self.support_rule)
        
        action = self.engine.get_first_matching_action(self.sample_email)
        self.assertEqual(action, "high_priority")  # Highest priority rule
    
    def test_rule_enable_disable(self):
        """Test enabling and disabling rules."""
        self.engine.add_rule(self.urgent_rule)
        
        # Disable the rule
        self.assertTrue(self.engine.disable_rule("urgent_emails"))
        
        # Should not match disabled rule
        matching_rules = self.engine.evaluate_email(self.sample_email)
        self.assertEqual(len(matching_rules), 0)
        
        # Re-enable the rule
        self.assertTrue(self.engine.enable_rule("urgent_emails"))
        
        # Should match again
        matching_rules = self.engine.evaluate_email(self.sample_email)
        self.assertEqual(len(matching_rules), 1)
    
    def test_remove_rule(self):
        """Test removing rules."""
        self.engine.add_rule(self.urgent_rule)
        self.assertEqual(len(self.engine.list_rules()), 1)
        
        # Remove the rule
        self.assertTrue(self.engine.remove_rule("urgent_emails"))
        self.assertEqual(len(self.engine.list_rules()), 0)
        
        # Try to remove non-existent rule
        self.assertFalse(self.engine.remove_rule("non_existent"))
    
    def test_validate_rule_syntax(self):
        """Test rule syntax validation."""
        # Valid syntax
        self.assertTrue(self.engine.validate_rule_syntax("priority == 'urgent'"))
        self.assertTrue(self.engine.validate_rule_syntax("contains(subject, 'test')"))
        
        # Invalid syntax
        self.assertFalse(self.engine.validate_rule_syntax("invalid syntax!!!"))
    
    def test_test_rule(self):
        """Test rule testing functionality."""
        # Test condition that should match
        self.assertTrue(
            self.engine.test_rule("priority == 'urgent'", self.sample_email)
        )
        
        # Test condition that should not match
        self.assertFalse(
            self.engine.test_rule("priority == 'low'", self.sample_email)
        )
    
    def test_export_import_rules(self):
        """Test rule export and import."""
        self.engine.add_rule(self.urgent_rule)
        self.engine.add_rule(self.support_rule)
        
        # Export rules
        exported = self.engine.export_rules()
        self.assertEqual(len(exported), 2)
        
        # Clear and import
        self.engine.clear_rules()
        self.assertEqual(len(self.engine.list_rules()), 0)
        
        self.engine.import_rules(exported)
        self.assertEqual(len(self.engine.list_rules()), 2)


class TestEmailRule(unittest.TestCase):
    """Test cases for EmailRule class."""
    
    def test_rule_creation(self):
        """Test rule creation."""
        rule = EmailRule(
            name="test_rule",
            description="Test rule",
            condition="priority == 'high'",
            action="test_queue",
            priority=50,
            enabled=True,
            metadata={"category": "test"}
        )
        
        self.assertEqual(rule.name, "test_rule")
        self.assertEqual(rule.condition, "priority == 'high'")
        self.assertEqual(rule.action, "test_queue")
        self.assertEqual(rule.priority, 50)
        self.assertTrue(rule.enabled)
        self.assertEqual(rule.metadata["category"], "test")
    
    def test_rule_to_dict(self):
        """Test rule dictionary conversion."""
        rule = EmailRule(
            name="dict_rule",
            description="Dictionary test rule",
            condition="contains(subject, 'test')",
            action="dict_queue",
            priority=75,
            enabled=False
        )
        
        rule_dict = rule.to_dict()
        
        self.assertEqual(rule_dict['name'], "dict_rule")
        self.assertEqual(rule_dict['condition'], "contains(subject, 'test')")
        self.assertEqual(rule_dict['action'], "dict_queue")
        self.assertEqual(rule_dict['priority'], 75)
        self.assertFalse(rule_dict['enabled'])
    
    def test_rule_from_dict(self):
        """Test rule creation from dictionary."""
        rule_dict = {
            'name': 'from_dict_rule',
            'description': 'Created from dictionary',
            'condition': 'sender_domain == "example.com"',
            'action': 'from_dict_queue',
            'priority': 60,
            'enabled': True,
            'metadata': {'source': 'dict'}
        }
        
        rule = EmailRule.from_dict(rule_dict)
        
        self.assertEqual(rule.name, 'from_dict_rule')
        self.assertEqual(rule.condition, 'sender_domain == "example.com"')
        self.assertEqual(rule.action, 'from_dict_queue')
        self.assertEqual(rule.priority, 60)
        self.assertTrue(rule.enabled)
        self.assertEqual(rule.metadata['source'], 'dict')


class TestEmailRuleEngineAdvanced(unittest.TestCase):
    """Additional test cases for EmailRuleEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = EmailRuleEngine()
        self.sample_email = EmailData(
            subject="Test Email",
            sender="user@example.com",
            recipients=["support@company.com"],
            cc_recipients=[],
            bcc_recipients=[],
            body_text="Test body content.",
            body_html=None,
            message_id="<test@example.com>",
            received_date=datetime.now(),
            sent_date=datetime.now(),
            headers={},
            attachments=[],
            priority="normal"
        )
    
    def test_get_rule(self):
        """Test getting a rule by name."""
        rule = EmailRule(
            name="get_test",
            description="Test get",
            condition="priority == 'high'",
            action="test_queue",
            priority=100,
            enabled=True
        )
        self.engine.add_rule(rule)
        
        retrieved = self.engine.get_rule("get_test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "get_test")
    
    def test_get_nonexistent_rule(self):
        """Test getting a non-existent rule."""
        retrieved = self.engine.get_rule("nonexistent")
        self.assertIsNone(retrieved)
    
    def test_list_rules_enabled_only(self):
        """Test listing only enabled rules."""
        self.engine.add_rule(EmailRule(
            name="enabled_rule",
            description="Enabled",
            condition="priority == 'high'",
            action="queue1",
            priority=100,
            enabled=True
        ))
        self.engine.add_rule(EmailRule(
            name="disabled_rule",
            description="Disabled",
            condition="priority == 'low'",
            action="queue2",
            priority=50,
            enabled=False
        ))
        
        enabled_rules = self.engine.list_rules(enabled_only=True)
        self.assertEqual(len(enabled_rules), 1)
        self.assertEqual(enabled_rules[0].name, "enabled_rule")
    
    def test_get_all_matching_actions(self):
        """Test getting all matching actions."""
        self.engine.add_rule(EmailRule(
            name="rule1",
            description="First",
            condition="contains(subject, 'Test')",
            action="action1",
            priority=100,
            enabled=True
        ))
        self.engine.add_rule(EmailRule(
            name="rule2",
            description="Second",
            condition="sender_domain == 'example.com'",
            action="action2",
            priority=50,
            enabled=True
        ))
        
        actions = self.engine.get_all_matching_actions(self.sample_email)
        self.assertIn("action1", actions)
        self.assertIn("action2", actions)
    
    def test_import_rules_with_clear(self):
        """Test importing rules with clearing existing."""
        # Add initial rule
        self.engine.add_rule(EmailRule(
            name="initial",
            description="Initial",
            condition="priority == 'high'",
            action="queue1",
            priority=100,
            enabled=True
        ))
        
        # Import new rules with clear
        new_rules = [
            {
                'name': 'new_rule',
                'description': 'New',
                'condition': "priority == 'low'",
                'action': 'queue2',
                'priority': 50,
                'enabled': True
            }
        ]
        
        self.engine.import_rules(new_rules, clear_existing=True)
        
        # Should only have the new rule
        self.assertEqual(len(self.engine.list_rules()), 1)
        self.assertEqual(self.engine.list_rules()[0].name, 'new_rule')
    
    def test_import_rules_with_error(self):
        """Test importing rules with some invalid rules."""
        rules_data = [
            {
                'name': 'valid',
                'description': 'Valid',
                'condition': "priority == 'high'",
                'action': 'queue1',
                'priority': 100,
                'enabled': True
            },
            {
                'name': 'invalid',
                'description': 'Invalid',
                'condition': "invalid syntax!!!",
                'action': 'queue2',
                'priority': 50,
                'enabled': True
            }
        ]
        
        self.engine.import_rules(rules_data)
        
        # Should only import the valid rule
        self.assertEqual(len(self.engine.list_rules()), 1)
        self.assertEqual(self.engine.list_rules()[0].name, 'valid')
    
    def test_test_rule_with_error(self):
        """Test testing a rule with invalid syntax."""
        result = self.engine.test_rule("invalid syntax!!!", self.sample_email)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()