"""
Business rules and constants for HolidayAssist AI email triage system.

This module serves as the single source of truth for:
- Valid intents and departments
- Intent-to-department routing rules
- Priority ordering logic
- Escalation keywords

All other modules should import from here to avoid duplication.
"""

from __future__ import annotations

# Escalation detection keywords
ESCALATION_KEYWORDS = [
    "lawyer",
    "legal action",
    "sue",
    "media",
    "press",
    "police",
    "discrimination",
    "harassment",
    "unsafe",
    "safety",
    "fraud",
    "stolen card",
    "medical emergency",
    "injury",
    "compensation",
]

# Valid intent labels for email classification
VALID_INTENTS = {
    "booking_change",
    "cancellation_request",
    "refund_request",
    "baggage_issue",
    "flight_delay",
    "hotel_change",
    "hotel_issue",
    "payment_problem",
    "complaint",
    "loyalty_question",
    "general_question",
    "special_assistance_request",
    "technical_issue",
}

# Valid department names for routing
VALID_DEPARTMENTS = {
    "Flight Operations",
    "Hotel Support",
    "Customer Care",
    "Refunds and Payments",
    "Accessibility Services",
    "Technical Support",
}

# Priority ordering for intent-based routing (highest to lowest priority)
INTENT_PRIORITY_ORDER = [
    "complaint",
    "refund_request",
    "payment_problem",
    "baggage_issue",
    "flight_delay",
    "cancellation_request",
    "special_assistance_request",
    "hotel_change",
    "hotel_issue",
    "booking_change",
    "technical_issue",
    "loyalty_question",
    "general_question",
]

# Intent-to-department routing map
INTENT_TO_DEPARTMENT = {
    "flight_delay": "Flight Operations",
    "cancellation_request": "Flight Operations",
    "baggage_issue": "Flight Operations",
    "hotel_change": "Hotel Support",
    "hotel_issue": "Hotel Support",
    "refund_request": "Refunds and Payments",
    "payment_problem": "Refunds and Payments",
    "special_assistance_request": "Accessibility Services",
    "technical_issue": "Technical Support",
    "complaint": "Customer Care",
    "booking_change": "Customer Care",
    "loyalty_question": "Customer Care",
    "general_question": "Customer Care",
}
