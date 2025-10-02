"""SQS integration for routing emails to different queues."""

from .sqs_client import SQSClient, SQSQueue

__all__ = ["SQSClient", "SQSQueue"]