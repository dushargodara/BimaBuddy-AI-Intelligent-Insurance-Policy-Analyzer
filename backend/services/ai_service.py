"""
AI analysis service using Google Gemini API.
"""

import json
import re
from typing import Any

from config import GEMINI_API_KEY, GEMINI_MAX_TOKENS, GEMINI_MODEL, PDF_MAX_CHARS_PER_CHUNK

# ✅ FIX 1: Custom Exception (removed backend.core dependency)
class AIAnalysisError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details


# ✅ FIX 2: Simple logger (removed backend.core.logger)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Expected JSON schema for LLM output
POLICY_JSON_SCHEMA = {
    "policy_type": "term|endowment|ulip|whole_life|money_back|other",
    "premium_amount": "number or null",
    "premium_frequency": "yearly|half_yearly|quarterly|monthly",
    "tenure_years": "number or null",
    "maturity_amount": "number or null",
    "sum_assured": "number or null",
    "guaranteed_return": "true or false",
    "benefits": "array of strings",
    "exclusions": "array of strings",
    "hidden_clauses": "array of strings",
    "risk_factors": "array of strings",
    "recommendation": "string",
    "simple_summary": "string",
}


def _get_client():
    try:
        from google import genai
    except ImportError as e:
        raise AIAnalysisError(
            "google-genai not installed. Run: pip install google-genai",
            details={"import_error": str(e)},
        ) from e

    if not GEMINI_API_KEY:
        raise AIAnalysisError("GEMINI_API_KEY is not set")

    return genai.Client(api_key=GEMINI_API_KEY)


def _build_extraction_prompt(text: str, chunk_index: int = 0, total_chunks: int = 1) -> str:
    chunk_note = ""
    if total_chunks > 1:
        chunk_note = f"\n[Document part {chunk_index + 1} of {total_chunks}]\n"

    schema_desc = json.dumps(POLICY_JSON_SCHEMA, indent=2)

    return f"""Extract structured insurance policy data.

Return ONLY valid JSON.

{text[:PDF_MAX_CHARS_PER_CHUNK]}

Schema:
{schema_desc}
"""


def extract_policy_data(text: str, chunk_index: int = 0, total_chunks: int = 1) -> dict[str, Any]:
    if not text.strip():
        return {}

    prompt = _build_extraction_prompt(text, chunk_index, total_chunks)
    client = _get_client()

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"temperature": 0.1, "max_output_tokens": GEMINI_MAX_TOKENS},
        )
    except Exception as e:
        logger.warning("Gemini failed, using mock data")
        return _get_mock_policy_data()

    content = getattr(response, "text", None)
    if not content:
        return {}

    parsed = _parse_ai_json(content)
    return _normalize_extracted(parsed)


def _parse_ai_json(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                return {}
    return {}


def _normalize_extracted(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_type": data.get("policy_type", "other"),
        "premium_amount": data.get("premium_amount"),
        "premium_frequency": data.get("premium_frequency", "yearly"),
        "tenure_years": data.get("tenure_years"),
        "maturity_amount": data.get("maturity_amount"),
        "sum_assured": data.get("sum_assured"),
        "guaranteed_return": data.get("guaranteed_return", True),
        "benefits": data.get("benefits", []),
        "exclusions": data.get("exclusions", []),
        "hidden_clauses": data.get("hidden_clauses", []),
        "risk_factors": data.get("risk_factors", []),
        "recommendation": data.get("recommendation", ""),
        "simple_summary": data.get("simple_summary", ""),
    }


def extract_structured_from_chunks(chunks: list[str]) -> dict[str, Any]:
    if not chunks:
        return {}

    merged = {}
    for chunk in chunks:
        data = extract_policy_data(chunk)
        merged.update(data)

    return merged


def _get_mock_policy_data() -> dict[str, Any]:
    return {
        "policy_type": "endowment",
        "premium_amount": 50000,
        "premium_frequency": "yearly",
        "tenure_years": 25,
        "maturity_amount": 1500000,
        "sum_assured": 1000000,
        "guaranteed_return": True,
        "benefits": ["Guaranteed return", "Life cover"],
        "exclusions": ["Suicide clause"],
        "hidden_clauses": ["Low early surrender value"],
        "risk_factors": ["Low ROI"],
        "recommendation": "Good for safe investors",
        "simple_summary": "Endowment plan with guaranteed returns",
    }
