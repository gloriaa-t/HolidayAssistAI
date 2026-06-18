from __future__ import annotations

from typing import Any, Dict, List


def normalize_missing_information(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize missing_information fields for consistent API responses.
    
    For payment-related intents, ensures "payment details" is always present
    without removing additional useful fields like "amount charged" or "charge date".
    """
    intents = payload.get("intents", [])
    missing_info = payload.get("missing_information", [])
    
    has_payment_intent = any(
        intent in intents 
        for intent in ["payment_problem", "refund_request"]
    )
    
    if has_payment_intent and missing_info:
        if "payment details" not in missing_info:
            missing_info.append("payment details")
            payload["missing_information"] = missing_info
    
    return payload
