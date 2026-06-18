from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv

from models import AnalyzeResponse
from prompts import SYSTEM_PROMPT
from services.fallback_analyzer import FallbackAnalyzer
from services.llm_client import ClaudeClient
from services.normalizer import normalize_missing_information


load_dotenv()


class EmailAnalyzer:
    """Orchestrates email analysis using LLM or fallback analyzer."""

    def __init__(self) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self.claude_client = ClaudeClient(self.api_key, self.model) if self.api_key else None
        self.fallback_analyzer = FallbackAnalyzer()

    def analyze(self, email_text: str) -> AnalyzeResponse:
        analysis_payload = self._analyze_email(email_text)
        analysis_payload = self._apply_frustration_elevation(analysis_payload)
        analysis_payload = normalize_missing_information(analysis_payload)
        return AnalyzeResponse.model_validate(analysis_payload)

    def _analyze_email(self, email_text: str) -> Dict[str, Any]:
        if not self.claude_client:
            print("No API key; using fallback analysis")
            return self.fallback_analyzer.analyze(email_text)
        
        try:
            return self.claude_client.call_api(SYSTEM_PROMPT, email_text)
        except Exception:
            print("Claude unavailable; using fallback analysis")
            return self.fallback_analyzer.analyze(email_text)

    def _apply_frustration_elevation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Elevate P3 to P2 if frustration level is high."""
        if payload.get("frustration_level", 0) >= 4 and payload["priority"] == "P3":
            payload["priority"] = "P2"
            payload["priority_reason"] = (
                f"{payload['priority_reason']} Elevated to P2 due to high frustration."
            )
        return payload