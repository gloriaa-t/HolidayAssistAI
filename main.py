from __future__ import annotations

from fastapi import FastAPI

from analyzer import EmailAnalyzer
from models import AnalyzeRequest, AnalyzeResponse
from validator import apply_escalation_rules


app = FastAPI(title="HolidayAssist AI", version="0.1.0")
analyzer = EmailAnalyzer()


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_email(request: AnalyzeRequest) -> AnalyzeResponse:
    result = analyzer.analyze(request.email_text)
    return apply_escalation_rules(result, request.email_text)
