# HolidayAssist AI

HolidayAssist AI is a proof-of-concept FastAPI service for customer email triage in a travel and holiday booking platform. It accepts raw customer email text and returns structured JSON containing detected intents, priority, department routing, missing information, an internal agent summary, a customer response draft, escalation status, sentiment, and frustration level.

## Part A - Solution Design

### Architecture and Workflow

The service exposes a single `POST /analyze` endpoint. Incoming requests are validated using Pydantic models and passed to `EmailAnalyzer`, which orchestrates the analysis workflow by delegating to specialized service modules.

The `ClaudeClient` service handles API communication with Claude using a structured prompt and few-shot examples. If the API key is unavailable or the call fails, `EmailAnalyzer` routes to `FallbackAnalyzer`, which applies deterministic rule-based heuristics. The `Normalizer` service ensures consistent output formatting across both analysis paths. After Pydantic validation, `validator.py` applies rule-based escalation overrides for high-risk cases such as legal threats, discrimination complaints, safety issues, or media involvement.

```text
Customer Email
    |
    v
FastAPI /analyze (main.py)
    |
    v
EmailAnalyzer (analyzer.py) ─── orchestration layer
    |
    ├─> ClaudeClient (services/llm_client.py)
    |       └─> Claude API call
    |
    ├─> FallbackAnalyzer (services/fallback_analyzer.py)
    |       └─> Rule-based classification
    |
    └─> Normalizer (services/normalizer.py)
            └─> Output normalization
    |
    v
Pydantic Validation (models.py)
    |
    v
Escalation Override (validator.py)
    |
    v
Structured JSON Response
```

### Code Structure

The codebase follows a service-oriented architecture with clear separation of concerns:

- **`main.py`** - FastAPI application and `/analyze` endpoint definition
- **`analyzer.py`** - Orchestrates the analysis workflow; routes between LLM and fallback
- **`services/llm_client.py`** - Claude API communication (HTTP requests and JSON parsing)
- **`services/fallback_analyzer.py`** - Rule-based email classification when LLM unavailable
- **`services/normalizer.py`** - Output normalization for API consistency
- **`validator.py`** - Deterministic escalation overrides for critical cases
- **`models.py`** - Pydantic schemas for request/response validation
- **`prompts.py`** - System prompts and few-shot examples for Claude
- **`rules.py`** - Business rules (intents, departments, escalation keywords)
- **`tests/test_cases.py`** - Parametrized test suite with 5 assessment scenarios

## Approach Rationale

The system combines probabilistic LLM reasoning with deterministic business rules while maintaining clear architectural boundaries.

**Service separation** improves maintainability and testability. Each service module has a single responsibility: `ClaudeClient` handles only API communication, `FallbackAnalyzer` contains only rule-based logic, and `Normalizer` performs only output formatting. This separation allows independent testing, easier debugging, and isolated changes to external dependencies.

**Claude** handles nuanced multi-intent classification and natural language understanding that would be difficult to encode in rules. **Pydantic validation** prevents malformed responses from reaching downstream systems. **The deterministic escalation override** ensures critical cases are never missed, even if the LLM misclassifies them. **The fallback analyzer** keeps the service operational when the LLM is unavailable and enables testing without external dependencies.

## Trade-offs

- **The single API call** reduces latency and cost by ~50% compared to separate calls for sentiment and analysis, but a failure requires a full retry rather than partial recovery
- **Strict Pydantic** validation improves reliability but rejects malformed LLM outputs that might be partially useful.
- **Rule-based escalation** provides 100% consistency for critical cases but requires manual maintenance as policies evolve.
- **Fallback heuristics** is deterministic and intended for service continuity. Results may differ slightly from Claude outputs because the fallback uses simplified heuristic rules."

## Production Challenges

- External LLM services may introduce variable response times due to network latency, model load, or rate limiting.
- LLM behavior changes with model updates, requiring regression testing and prompt versioning.
- Customer emails contain PII requiring encryption at rest and in transit, plus GDPR/CCPA compliance measures.
- Without CRM integration, the system cannot access customer history or verify booking details.
- P1 escalations require real-time alerting infrastructure. The system lacks multi-language support, attachment analysis, and conversation threading.
- Current missing-information detection relies on prompt instructions and heuristic rules rather than entity extraction models.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

## Testing

### Run Test Suite

Execute the assessment test cases:

```bash
python -m pytest tests/test_cases.py -v -s
```

### Test via FastAPI Docs

Start the API:

```bash
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Use the interactive Swagger UI to submit sample customer emails and inspect the structured JSON response.

### Test via PowerShell (Windows)

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/analyze" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"email_text":"I need to move my hotel booking and was charged twice."}'
```

### Test via curl (Linux/macOS)

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"email_text":"I need to move my hotel booking and was charged twice."}'
```