from __future__ import annotations

import re
from typing import Any, Dict, List

from rules import (
    ESCALATION_KEYWORDS,
    INTENT_PRIORITY_ORDER,
    INTENT_TO_DEPARTMENT,
)


class FallbackAnalyzer:
    """Rule-based fallback analyzer for email classification."""

    def analyze(self, email_text: str) -> Dict[str, Any]:
        """
        Analyze email using rule-based detection.
        
        Returns analysis dict with same schema as LLM response.
        """
        lowered = email_text.lower()
        intents = self._detect_intents(lowered)
        requires_escalation = self._check_escalation(lowered)
        priority = self._determine_priority(intents, requires_escalation, lowered)
        department = self._determine_department(intents)
        missing_information = self._detect_missing_information(email_text, intents)
        sentiment, frustration_level = self._compute_sentiment(lowered, requires_escalation)

        escalation_reason = ""
        if requires_escalation:
            escalation_reason = (
                "Customer references legal, safety, discrimination, harassment, or media escalation."
            )

        return {
            "intents": intents,
            "priority": priority,
            "priority_reason": self._build_priority_reason(priority, requires_escalation, intents),
            "department": department,
            "department_reason": self._build_department_reason(department, intents),
            "missing_information": missing_information,
            "agent_summary": self._build_agent_summary(intents, missing_information, email_text),
            "customer_response": self._build_customer_response(intents, missing_information),
            "requires_escalation": requires_escalation,
            "escalation_reason": escalation_reason,
            "sentiment": sentiment,
            "frustration_level": frustration_level,
        }

    def _detect_intents(self, lowered: str) -> List[str]:
        intents: List[str] = []

        if any(token in lowered for token in ["change", "reschedule", "postpone", "move my booking"]):
            intents.append("booking_change")

        if any(token in lowered for token in ["cancel", "cancellation"]):
            intents.append("cancellation_request")

        if any(token in lowered for token in ["refund", "money back", "charged twice", "billed twice"]):
            intents.append("refund_request")

        if any(token in lowered for token in ["bag", "baggage", "luggage", "suitcase"]):
            intents.append("baggage_issue")

        if any(token in lowered for token in ["delayed flight", "flight delay", "late flight"]):
            intents.append("flight_delay")

        if any(token in lowered for token in ["move my hotel", "hotel dates", "change my hotel", "hotel booking", "postpone my stay"]):
            intents.append("hotel_change")

        if any(token in lowered for token in ["hotel", "room", "reservation", "property", "stay"]):
            intents.append("hotel_issue")

        if any(token in lowered for token in ["charged", "payment", "card", "billing", "billed twice"]):
            intents.append("payment_problem")

        if any(token in lowered for token in ["complaint", "terrible", "awful", "unacceptable", "discriminat"]):
            intents.append("complaint")

        if any(token in lowered for token in ["points", "loyalty", "status"]):
            intents.append("loyalty_question")

        if any(token in lowered for token in ["wheelchair", "assistance", "accessible", "special assistance"]):
            intents.append("special_assistance_request")

        if any(
            token in lowered
            for token in [
                "app",
                "website",
                "site",
                "login",
                "password",
                "technical",
                "error code",
                "looks wrong",
            ]
        ):
            intents.append("technical_issue")

        if "technical_issue" in intents and any(
            token in lowered
            for token in ["can someone check", "can you check", "something looks wrong"]
        ):
            intents.append("general_question")

        if not intents:
            intents.append("general_question")

        return list(dict.fromkeys(intents))

    def _check_escalation(self, lowered: str) -> bool:
        return any(
            self._contains_whole_word(lowered, token)
            for token in ESCALATION_KEYWORDS
        )

    def _determine_priority(self, intents: List[str], requires_escalation: bool, lowered: str) -> str:
        if requires_escalation or any(
            self._contains_whole_word(lowered, token)
            for token in ["medication", "unsafe", "safety"]
        ):
            return "P1"

        if any(
            intent in intents
            for intent in [
                "payment_problem",
                "refund_request",
                "baggage_issue",
                "flight_delay",
                "complaint",
            ]
        ):
            return "P2"

        if any(
            intent in intents
            for intent in [
                "booking_change",
                "cancellation_request",
                "hotel_change",
                "hotel_issue",
                "special_assistance_request",
                "technical_issue",
            ]
        ):
            return "P3"

        return "P4"

    def _determine_department(self, intents: List[str]) -> str:
        for intent in INTENT_PRIORITY_ORDER:
            if intent in intents:
                return INTENT_TO_DEPARTMENT[intent]
        return "Customer Care"

    def _build_priority_reason(
        self,
        priority: str,
        requires_escalation: bool,
        intents: List[str],
    ) -> str:
        if requires_escalation:
            return "Escalation triggers create immediate legal, safety, or reputational risk requiring urgent handling."

        if priority == "P1":
            return "The issue has immediate customer impact and requires urgent handling."

        if priority == "P2":
            return f"The issue involves {', '.join(intents)} and needs timely review from support."

        if priority == "P3":
            return f"The issue involves {', '.join(intents)} and should be handled in the normal service queue."

        return "This is a routine informational request with no operational urgency."

    def _build_department_reason(self, department: str, intents: List[str]) -> str:
        joined_intents = ", ".join(intents)

        if department == "Flight Operations":
            return f"The request involves flight-related operational handling such as {joined_intents}."

        if department == "Hotel Support":
            return f"The request centers on hotel servicing or date changes, including {joined_intents}."

        if department == "Refunds and Payments":
            return f"The request includes financial servicing needs such as {joined_intents}."

        if department == "Accessibility Services":
            return "The request involves accessibility or special assistance coordination."

        if department == "Technical Support":
            return "The request involves a website, app, login, or other technical access problem."

        return f"The request is best handled by customer care because it includes {joined_intents}."

    def _detect_missing_information(self, email_text: str, intents: List[str]) -> List[str]:
        lowered = email_text.lower()
        missing: List[str] = []

        booking_reference_needed = any(
            intent in intents
            for intent in [
                "booking_change",
                "cancellation_request",
                "refund_request",
                "baggage_issue",
                "flight_delay",
                "hotel_change",
                "hotel_issue",
                "payment_problem",
                "complaint",
                "special_assistance_request",
                "technical_issue",
            ]
        )

        if booking_reference_needed and not self._contains_booking_reference(lowered):
            missing.append("booking reference")

        if any(intent in intents for intent in ["flight_delay", "cancellation_request", "baggage_issue"]):
            if not self._contains_any(lowered, ["flight ", "flight number", "ba", "aa", "ua", "dl"]):
                missing.append("flight number")
            if not self._contains_travel_dates(lowered):
                missing.append("travel dates")
            if not self._contains_passenger_names(lowered):
                missing.append("passenger names")

        if any(intent in intents for intent in ["hotel_change", "hotel_issue", "booking_change"]):
            if not self._contains_travel_dates(lowered):
                missing.append("travel dates")
            if "hotel" in lowered and not self._contains_any(lowered, ["property", "hotel name", "reservation at"]):
                missing.append("hotel name")

        if any(intent in intents for intent in ["refund_request", "payment_problem"]):
            if not self._contains_any(
                lowered,
                ["visa", "mastercard", "amex", "receipt", "charged to", "invoice", "last four"],
            ):
                missing.append("payment details")

            if not self._contains_any(
                lowered,
                ["€", "$", "amount", "charged", "charge of"],
            ):
                missing.append("amount charged")

            if not self._contains_any(
                lowered,
                ["today", "yesterday", "january", "february", "march", "april",
                 "may", "june", "july", "august", "september",
                 "october", "november", "december"],
            ):
                missing.append("charge date")

        if "special_assistance_request" in intents:
            if not self._contains_travel_dates(lowered):
                missing.append("travel dates")
            if not self._contains_passenger_names(lowered):
                missing.append("passenger names")
            if not self._contains_any(lowered, ["wheelchair", "mobility", "hearing", "visual", "oxygen"]):
                missing.append("specific assistance needs")

        if "complaint" in intents:
            if not self._contains_any(lowered, ["airport", "hotel", "flight", "check-in", "desk", "location"]):
                missing.append("location")
            if not self._contains_any(lowered, ["staff", "agent", "representative", "employee"]):
                missing.append("staff details")

        if "technical_issue" in intents and not self._contains_any(
            lowered,
            ["error", "code", "login", "screen", "browser"],
        ):
            missing.append("technical error details")

        if "loyalty_question" in intents and self._contains_any(
            lowered,
            ["my account", "my points", "my status"],
        ):
            if not self._contains_any(lowered, ["member", "membership", "account email"]):
                missing.append("loyalty account details")

        return list(dict.fromkeys(missing))

    def _build_agent_summary(
        self,
        intents: List[str],
        missing_information: List[str],
        email_text: str,
    ) -> str:
        sentences: List[str] = []

        if "hotel_change" in intents and "special_assistance_request" in intents:
            sentences.append(
                "Customer requests a hotel booking change and accessibility support for a passenger."
            )
        elif "payment_problem" in intents and "hotel_change" in intents:
            sentences.append(
                "Customer reports a duplicate charge and requests a hotel date change on the same booking."
            )
        elif "complaint" in intents:
            sentences.append("Customer submitted a complaint that requires internal review.")
        elif "special_assistance_request" in intents:
            sentences.append("Customer requests accessibility assistance for upcoming travel.")
        elif "technical_issue" in intents:
            sentences.append("Customer reports a technical issue affecting access or booking management.")
        elif "loyalty_question" in intents:
            sentences.append("Customer submitted a routine loyalty-program inquiry.")
        else:
            sentences.append(f"Customer request includes: {', '.join(intents)}.")

        if missing_information:
            sentences.append(f"Missing information: {', '.join(missing_information)}.")

        summary = " ".join(sentences)
        return self._limit_words(summary, 100)

    def _build_customer_response(
        self,
        intents: List[str],
        missing_information: List[str],
    ) -> str:
        topic = self._customer_topic(intents)

        if missing_information:
            requested_items = ", ".join(missing_information)
            return (
                f"Thank you for contacting HolidayAssist AI. We are sorry for the trouble you have described regarding {topic}. "
                f"We have logged your request for review by the appropriate team. Please provide {requested_items} so they can verify the details and advise on the next steps."
            )

        return (
            f"Thank you for contacting HolidayAssist AI. We have logged your request regarding {topic} for review by the appropriate team. "
            "They will review your case and advise on the next steps."
        )

    def _customer_topic(self, intents: List[str]) -> str:
        if "special_assistance_request" in intents:
            return "your accessibility request"

        if "payment_problem" in intents or "refund_request" in intents:
            return "your payment or refund concern"

        if "hotel_change" in intents or "hotel_issue" in intents:
            return "your hotel booking"

        if "baggage_issue" in intents or "flight_delay" in intents or "cancellation_request" in intents:
            return "your travel disruption"

        if "technical_issue" in intents:
            return "the technical issue"

        if "loyalty_question" in intents:
            return "your loyalty question"

        return "your request"

    def _compute_sentiment(self, lowered: str, requires_escalation: bool) -> tuple[str, int]:
        positive_tokens = ["thanks", "thank you", "appreciate", "grateful"]
        negative_tokens = ["angry", "terrible", "awful", "unacceptable"]

        sentiment = "neutral"
        frustration_level = 2

        if any(token in lowered for token in positive_tokens):
            sentiment = "positive"
            frustration_level = 1

        if any(token in lowered for token in negative_tokens):
            sentiment = "negative"
            frustration_level = 4

        if requires_escalation:
            sentiment = "negative"
            frustration_level = 5

        return sentiment, frustration_level

    def _contains_booking_reference(self, lowered: str) -> bool:
        return self._contains_any(
            lowered,
            ["booking reference", "confirmation", "reservation code", "pnr", "record locator"],
        )

    def _contains_travel_dates(self, lowered: str) -> bool:
        return self._contains_any(
            lowered,
            [
                "january",
                "february",
                "march",
                "april",
                "may",
                "june",
                "july",
                "august",
                "september",
                "october",
                "november",
                "december",
                "next week",
                "next month",
                " on ",
                "/",
                "-202",
            ],
        )

    def _contains_passenger_names(self, lowered: str) -> bool:
        return self._contains_any(
            lowered,
            [
                "mr ",
                "mrs ",
                "ms ",
                "passenger name",
                "traveler name",
                "name is ",
                "names are ",
            ],
        )

    def _contains_whole_word(self, text: str, token: str) -> bool:
        return re.search(rf"\b{re.escape(token)}\b", text) is not None

    def _contains_any(self, lowered: str, tokens: List[str]) -> bool:
        return any(token in lowered for token in tokens)

    def _limit_words(self, value: str, max_words: int) -> str:
        words = value.split()
        if len(words) <= max_words:
            return value
        return " ".join(words[:max_words])
