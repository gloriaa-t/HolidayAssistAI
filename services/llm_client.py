from __future__ import annotations

import json
from typing import Any, Dict

import httpx


class ClaudeClient:
    """Claude API client for email analysis."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self.api_key = api_key
        self.model = model

    def call_api(self, system_prompt: str, email_text: str) -> Dict[str, Any]:
        """
        Call Claude API with system prompt and email text.
        
        Returns parsed JSON response as dict.
        Raises httpx.HTTPError on API failure.
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 450,
            "system": system_prompt,
            "messages": [{"role": "user", "content": email_text}],
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

        body = response.json()
        text_segments = [
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        ]

        json_text = "".join(text_segments).strip()
        return json.loads(json_text)
