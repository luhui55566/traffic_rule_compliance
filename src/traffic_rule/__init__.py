"""
Traffic Rule Compliance Verification System

This module provides the main entry point for traffic rule compliance verification.
It integrates map loading, map API, and traffic rule checking modules.
"""

from .traffic_rule_verification_system import TrafficRuleVerificationSystem
from .types import VehicleState, Violation, ViolationSeverity, ViolationReport
from .config import TrafficRuleConfig

__all__ = [
    'TrafficRuleVerificationSystem',
    'VehicleState',
    'Violation',
    'ViolationSeverity',
    'ViolationReport',
    'TrafficRuleConfig',
]
