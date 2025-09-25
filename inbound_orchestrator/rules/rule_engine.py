"""
Email rule engine using the rule-engine PyPI package.

This module provides integration with the rule-engine library to evaluate
custom rules against email objects for routing decisions.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
import rule_engine
import logging

from ..models.email_model import EmailData

logger = logging.getLogger(__name__)


@dataclass
class EmailRule:
    """
    Represents a single email processing rule.
    
    A rule consists of:
    - name: Human-readable name for the rule
    - description: What the rule does
    - condition: Rule expression (using rule-engine syntax)
    - action: What to do when rule matches (e.g., queue name)
    - priority: Higher priority rules are evaluated first
    - enabled: Whether the rule is active
    """
    name: str
    description: str
    condition: str
    action: str
    priority: int = 0
    enabled: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'condition': self.condition,
            'action': self.action,
            'priority': self.priority,
            'enabled': self.enabled,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailRule':
        """Create EmailRule from dictionary."""
        return cls(
            name=data['name'],
            description=data['description'],
            condition=data['condition'],
            action=data['action'],
            priority=data.get('priority', 0),
            enabled=data.get('enabled', True),
            metadata=data.get('metadata', {})
        )


class EmailRuleEngine:
    """
    Email rule engine that evaluates rules against email data.
    
    Uses the rule-engine PyPI package to provide flexible, user-defined
    logic for processing emails and triggering routing actions.
    """
    
    def __init__(self):
        """Initialize the rule engine."""
        self.rules: List[EmailRule] = []
        self._compiled_rules: Dict[str, rule_engine.Rule] = {}
    
    def add_rule(self, rule: EmailRule) -> None:
        """
        Add a rule to the engine.
        
        Args:
            rule: EmailRule to add
        """
        try:
            # Compile the rule to validate syntax
            compiled_rule = rule_engine.Rule(rule.condition)
            self._compiled_rules[rule.name] = compiled_rule
            self.rules.append(rule)
            logger.info(f"Added rule: {rule.name}")
        except rule_engine.RuleSyntaxError as e:
            logger.error(f"Invalid rule syntax for '{rule.name}': {e}")
            raise ValueError(f"Invalid rule syntax for '{rule.name}': {e}")
    
    def add_rules(self, rules: List[Union[EmailRule, Dict[str, Any]]]) -> None:
        """
        Add multiple rules to the engine.
        
        Args:
            rules: List of EmailRule objects or dictionaries
        """
        for rule in rules:
            if isinstance(rule, dict):
                rule = EmailRule.from_dict(rule)
            self.add_rule(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        Remove a rule from the engine.
        
        Args:
            rule_name: Name of the rule to remove
            
        Returns:
            True if rule was found and removed, False otherwise
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                if rule_name in self._compiled_rules:
                    del self._compiled_rules[rule_name]
                logger.info(f"Removed rule: {rule_name}")
                return True
        return False
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable a rule by name."""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                logger.info(f"Enabled rule: {rule_name}")
                return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable a rule by name."""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                logger.info(f"Disabled rule: {rule_name}")
                return True
        return False
    
    def get_rule(self, rule_name: str) -> Optional[EmailRule]:
        """Get a rule by name."""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def list_rules(self, enabled_only: bool = False) -> List[EmailRule]:
        """
        List all rules in the engine.
        
        Args:
            enabled_only: If True, only return enabled rules
            
        Returns:
            List of EmailRule objects
        """
        if enabled_only:
            return [rule for rule in self.rules if rule.enabled]
        return self.rules.copy()
    
    def evaluate_email(self, email_data: EmailData) -> List[EmailRule]:
        """
        Evaluate all rules against an email and return matching rules.
        
        Args:
            email_data: EmailData object to evaluate
            
        Returns:
            List of matching EmailRule objects, sorted by priority (highest first)
        """
        matching_rules = []
        email_dict = email_data.to_dict()
        
        # Add custom functions to the context for more complex evaluations
        context = self._create_evaluation_context(email_data)
        email_dict.update(context)
        
        # Sort rules by priority (highest first)
        sorted_rules = sorted(
            [rule for rule in self.rules if rule.enabled],
            key=lambda r: r.priority,
            reverse=True
        )
        
        for rule in sorted_rules:
            try:
                compiled_rule = self._compiled_rules.get(rule.name)
                if compiled_rule is None:
                    # Re-compile if needed
                    compiled_rule = rule_engine.Rule(rule.condition)
                    self._compiled_rules[rule.name] = compiled_rule
                
                if compiled_rule.matches(email_dict):
                    matching_rules.append(rule)
                    logger.debug(f"Rule '{rule.name}' matched email: {email_data.subject[:50]}")
                else:
                    logger.debug(f"Rule '{rule.name}' did not match email: {email_data.subject[:50]}")
                    
            except Exception as e:
                logger.error(f"Error evaluating rule '{rule.name}': {e}")
                continue
        
        return matching_rules
    
    def get_first_matching_action(self, email_data: EmailData) -> Optional[str]:
        """
        Get the action from the first matching rule (highest priority).
        
        Args:
            email_data: EmailData object to evaluate
            
        Returns:
            Action string from the first matching rule, or None if no matches
        """
        matching_rules = self.evaluate_email(email_data)
        if matching_rules:
            return matching_rules[0].action
        return None
    
    def get_all_matching_actions(self, email_data: EmailData) -> List[str]:
        """
        Get actions from all matching rules.
        
        Args:
            email_data: EmailData object to evaluate
            
        Returns:
            List of action strings from all matching rules
        """
        matching_rules = self.evaluate_email(email_data)
        return [rule.action for rule in matching_rules]
    
    def _create_evaluation_context(self, email_data: EmailData) -> Dict[str, Any]:
        """
        Create additional context functions for rule evaluation.
        
        Args:
            email_data: EmailData object
            
        Returns:
            Dictionary of context functions and values
        """
        return {
            # Helper functions
            'contains': lambda text, keyword: keyword.lower() in text.lower(),
            'starts_with': lambda text, prefix: text.lower().startswith(prefix.lower()),
            'ends_with': lambda text, suffix: text.lower().endswith(suffix.lower()),
            'matches_pattern': lambda text, pattern: email_data.matches_sender_pattern(pattern) if text == email_data.sender else False,
            'has_keyword': lambda keyword: email_data.contains_keyword(keyword),
            'has_attachment_type': lambda content_type: email_data.has_attachment_type(content_type),
            
            # Common email domains for rules
            'is_gmail': email_data.sender_domain == 'gmail.com' if email_data.sender_domain else False,
            'is_outlook': email_data.sender_domain in ['outlook.com', 'hotmail.com', 'live.com'] if email_data.sender_domain else False,
            'is_internal': email_data.sender_domain in ['company.com', 'internal.org'] if email_data.sender_domain else False,  # Configure as needed
            
            # Time-based helpers
            'is_weekend': email_data.received_date.weekday() >= 5,
            'is_business_hours': 9 <= email_data.received_date.hour <= 17,
            'is_after_hours': email_data.received_date.hour < 9 or email_data.received_date.hour > 17,
        }
    
    def validate_rule_syntax(self, condition: str) -> bool:
        """
        Validate rule syntax without adding the rule.
        
        Args:
            condition: Rule condition string to validate
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            rule_engine.Rule(condition)
            return True
        except rule_engine.RuleSyntaxError:
            return False
    
    def test_rule(self, condition: str, email_data: EmailData) -> bool:
        """
        Test a rule condition against email data without adding it to the engine.
        
        Args:
            condition: Rule condition to test
            email_data: EmailData to test against
            
        Returns:
            True if rule matches, False otherwise
        """
        try:
            test_rule = rule_engine.Rule(condition)
            email_dict = email_data.to_dict()
            context = self._create_evaluation_context(email_data)
            email_dict.update(context)
            return test_rule.matches(email_dict)
        except Exception as e:
            logger.error(f"Error testing rule: {e}")
            return False
    
    def clear_rules(self) -> None:
        """Remove all rules from the engine."""
        self.rules.clear()
        self._compiled_rules.clear()
        logger.info("Cleared all rules from engine")
    
    def export_rules(self) -> List[Dict[str, Any]]:
        """Export all rules as a list of dictionaries."""
        return [rule.to_dict() for rule in self.rules]
    
    def import_rules(self, rules_data: List[Dict[str, Any]], clear_existing: bool = False) -> None:
        """
        Import rules from a list of dictionaries.
        
        Args:
            rules_data: List of rule dictionaries
            clear_existing: Whether to clear existing rules first
        """
        if clear_existing:
            self.clear_rules()
        
        for rule_dict in rules_data:
            try:
                rule = EmailRule.from_dict(rule_dict)
                self.add_rule(rule)
            except Exception as e:
                logger.error(f"Failed to import rule '{rule_dict.get('name', 'unknown')}': {e}")
                continue