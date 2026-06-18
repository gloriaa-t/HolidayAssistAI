import json

import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


ASSESSMENT_CASES = [
    {
        "name": "simple_case",
        "email_text": "Can you tell me how many loyalty points I need to reach gold status?",
        "expected_intents": {"loyalty_question"},
        "expected_priority": "P4",
        "expected_department": "Customer Care",
        "expected_escalation": False,
        "expected_missing": set(),
        "missing_info_assertion": "exact",
        "explanation": "General informational inquiry about loyalty program. Correctly classified as loyalty_question with P4 priority (low-priority informational). Routed to Customer Care for standard inquiry handling. No booking reference requested because this is a general policy question, not account-specific. No escalation needed for routine information request.",
    },
    {
        "name": "multi_intent_payments_and_hotel",
        "email_text": "I need to move my hotel booking by one day and I was charged twice for it.",
        "expected_intents": {"hotel_change", "hotel_issue", "refund_request", "payment_problem"},
        "expected_priority": "P2",
        "expected_department": "Refunds and Payments",
        "expected_escalation": False,
        "expected_missing": {"booking reference", "travel dates", "payment details"},
        "missing_info_assertion": "contains",
        "explanation": "Multi-intent scenario: customer requests hotel date change and reports duplicate charge. Correctly detects all four intents (hotel_change, hotel_issue, payment_problem, refund_request) because any hotel modification is both a change and an issue, and duplicate charges imply both payment problems and refund needs. P2 priority appropriate for financial issue requiring timely resolution. Routed to Refunds and Payments as financial verification is most urgent; they can coordinate with Hotel Support. Booking reference, travel dates, and payment details required to investigate both issues. No escalation as no legal/media threats present.",
    },
    {
        "name": "multi_intent_accessibility_and_hotel",
        "email_text": "Please change my hotel arrival to July 18 and arrange wheelchair assistance for my mother.",
        "expected_intents": {"hotel_change", "hotel_issue", "special_assistance_request"},
        "expected_priority": "P3",
        "expected_department": "Accessibility Services",
        "expected_escalation": False,
        "expected_missing": {"booking reference", "passenger names"},
        "missing_info_assertion": "contains",
        "explanation": "Multi-intent scenario: customer requests hotel arrival date change and wheelchair assistance. Correctly detects three intents (hotel_change, hotel_issue, special_assistance_request). P3 priority appropriate as both require pre-travel coordination but no immediate disruption. Routed to Accessibility Services as specialist accessibility planning takes precedence; Hotel Support can coordinate date change after accessibility confirmed. Booking reference and passenger names required to arrange both services. No escalation as no safety threats or high-risk factors present.",
    },
    {
        "name": "ambiguous_case",
        "email_text": "I booked a trip through your site and something looks wrong. Can someone check it?",
        "expected_intents": {"general_question", "technical_issue"},
        "expected_priority": "P3",
        "expected_department": "Technical Support",
        "expected_escalation": False,
        "expected_missing": {"booking reference", "technical error details"},
        "missing_info_assertion": "contains",
        "explanation": "Ambiguous technical scenario: customer reports something 'looks wrong' with booking but provides minimal detail. Correctly detects both technical_issue (possible display/system problem) and general_question (vague help request). P3 priority appropriate as potential issue needs investigation but no confirmed service disruption. Routed to Technical Support to diagnose potential platform issue. Booking reference and technical error details required to investigate. No escalation as no legal threats, just unclear technical concern.",
    },
    {
        "name": "escalation_case",
        "email_text": "Your staff discriminated against me and I will contact my lawyer and the media.",
        "expected_intents": {"complaint"},
        "expected_priority": "P1",
        "expected_department": "Customer Care",
        "expected_escalation": True,
        "expected_missing": {"booking reference", "location"},
        "missing_info_assertion": "contains",
        "explanation": "High-severity escalation scenario: discrimination allegation with explicit legal and media threats. Correctly classified as complaint with P1 priority (immediate reputational and legal risk). Routed to Customer Care for urgent senior management review. Booking reference and location required to investigate allegation. Correctly triggers escalation due to rule-based keywords ('discriminated', 'lawyer', 'media') that override normal classification. Validator.py applies hard escalation rules to ensure critical cases never slip through even if LLM under-classifies.",
    },
]


def assert_missing_information(case: dict, payload: dict) -> None:
    expected_missing = case["expected_missing"]
    actual_missing = set(payload["missing_information"])
    assertion_mode = case.get("missing_info_assertion", "contains")

    if assertion_mode == "exact":
        assert actual_missing == expected_missing, case["explanation"]
        return

    assert expected_missing.issubset(actual_missing), case["explanation"]


@pytest.mark.parametrize("case", ASSESSMENT_CASES, ids=[case["name"] for case in ASSESSMENT_CASES])
def test_assessment_examples(case: dict) -> None:
    response = client.post("/analyze", json={"email_text": case["email_text"]})

    assert response.status_code == 200, case["explanation"]
    payload = response.json()
    
    print("\n")
    print("=" * 80)
    print(f"TEST CASE: {case['name']}")
    print("=" * 80)

    print("\nINPUT:")
    print(case["email_text"])

    print("\nOUTPUT:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    print("\nEXPLANATION:")
    print(case["explanation"])
    print("\n")

    expected_keys = {
        "intents",
        "priority",
        "priority_reason",
        "department",
        "department_reason",
        "missing_information",
        "agent_summary",
        "customer_response",
        "requires_escalation",
        "escalation_reason",
        "sentiment",
        "frustration_level",
    }
    assert set(payload.keys()) == expected_keys, case["explanation"]
    assert case["expected_intents"].issubset(set(payload["intents"])), case["explanation"]
    assert payload["priority"] == case["expected_priority"], case["explanation"]
    assert payload["department"] == case["expected_department"], case["explanation"]
    assert payload["requires_escalation"] is case["expected_escalation"], case["explanation"]
    assert_missing_information(case, payload)
    assert payload["sentiment"] in {"positive", "neutral", "negative"}, case["explanation"]
    assert 1 <= payload["frustration_level"] <= 5, case["explanation"]
    assert len(payload["agent_summary"].split()) <= 100, case["explanation"]
    assert payload["priority_reason"], case["explanation"]
    assert payload["department_reason"], case["explanation"]
    assert payload["customer_response"], case["explanation"]
