"""
InboundOrchestrator - A rules engine for processing emails and routing to SQS queues.

This package provides functionality to:
- Parse and model email data
- Define and evaluate custom rules on email objects  
- Route emails to different SQS queues based on rule evaluation
- Provide flexible, user-defined logic for email processing workflows
"""

__version__ = "0.1.0"
__author__ = "ShelterCodeAi"

from .orchestrator import InboundOrchestrator
from .models.email_model import EmailData
from .rules.rule_engine import EmailRuleEngine

__all__ = ["InboundOrchestrator", "EmailData", "EmailRuleEngine"]