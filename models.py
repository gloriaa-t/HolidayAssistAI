from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

from rules import VALID_DEPARTMENTS, VALID_INTENTS


class AnalyzeRequest(BaseModel):
    email_text: str = Field(min_length=1, description="Raw customer email text")


class AnalyzeResponse(BaseModel):
    intents: List[str] = Field(min_length=1, description="All detected intents")
    priority: Literal["P1", "P2", "P3", "P4"]
    priority_reason: str = Field(min_length=1)
    department: str = Field(min_length=1)
    department_reason: str = Field(min_length=1)
    missing_information: List[str] = Field(default_factory=list)
    agent_summary: str = Field(min_length=1)
    customer_response: str = Field(min_length=1)
    requires_escalation: bool
    escalation_reason: str = Field(default="")
    sentiment: Literal["positive", "neutral", "negative"]
    frustration_level: int = Field(ge=1, le=5)

    @field_validator("intents")
    @classmethod
    def validate_intents(cls, value: List[str]) -> List[str]:
        invalid = [intent for intent in value if intent not in VALID_INTENTS]
        if invalid:
            raise ValueError(f"intents contain unsupported labels: {invalid}")
        return value

    @field_validator("department")
    @classmethod
    def validate_department(cls, value: str) -> str:
        if value not in VALID_DEPARTMENTS:
            raise ValueError(f"department must be one of {sorted(VALID_DEPARTMENTS)}")
        return value

    @field_validator("missing_information")
    @classmethod
    def validate_missing_information(cls, value: List[str]) -> List[str]:
        if not isinstance(value, list):
            raise ValueError("missing_information must be a list")
        return value

    @field_validator("agent_summary")
    @classmethod
    def validate_agent_summary_length(cls, value: str) -> str:
        if len(value.split()) > 100:
            raise ValueError("agent_summary must be 100 words or fewer")
        return value
