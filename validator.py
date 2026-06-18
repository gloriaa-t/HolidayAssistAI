from __future__ import annotations

import re

from models import AnalyzeResponse
from rules import ESCALATION_KEYWORDS


def apply_escalation_rules(result: AnalyzeResponse, email_text: str) -> AnalyzeResponse:
    lowered = email_text.lower()

    matched = [
        keyword
        for keyword in ESCALATION_KEYWORDS
        if re.search(rf"\b{re.escape(keyword)}\b", lowered)
    ]

    if matched:
        result.requires_escalation = True
        result.priority = "P1"
        result.escalation_reason = (
            f"Rule-based escalation keywords detected: {', '.join(matched)}."
        )

        if "urgent" not in result.priority_reason.lower():
            result.priority_reason = (
                f"{result.priority_reason} Escalated to P1 due to legal, safety, or reputational risk."
            ).strip()

    if result.frustration_level >= 4 and result.priority == "P3":
        result.priority = "P2"
        result.priority_reason = (
            f"{result.priority_reason} Elevated to P2 because frustration level is high."
        )

    return result