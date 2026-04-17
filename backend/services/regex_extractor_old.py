"""
Regex-based financial data extraction from policy text.

Used as fallback when AI returns null for numeric fields.
"""

import re
from typing import Any

from backend.core.logger import get_logger

logger = get_logger(__name__)


def extract_financial_values(text: str) -> dict[str, Any]:
    """
    Extract premium, tenure, maturity, sum assured using regex.

    Args:
        text: Policy document text.

    Returns:
        Dict with premium_amount, tenure_years, maturity_amount, sum_assured.
    """
    result: dict[str, Any] = {
        "premium_amount": None,
        "tenure_years": None,
        "maturity_amount": None,
        "sum_assured": None,
    }

    # Premium patterns (₹X or Rs X or X INR)
    premium_patterns = [
        r"(?:premium|annual\s+premium|yearly\s+premium)[\s:]*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)",
        r"(?:premium\s+of|payable\s+premium)[\s:]*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)",
        r"₹\s*([\d,]+(?:\.\d+)?)\s*(?:per\s+year|p\.?a\.?|annual)",
        r"Rs\.?\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac|per\s+annum)",
    ]
    for pat in premium_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["premium_amount"] = _parse_number(m.group(1))
            break

    # Tenure patterns
    tenure_patterns = [
        r"(?:tenure|term|policy\s+term)[\s:]*(\d+)\s*(?:years?|yrs?)",
        r"(\d+)\s*(?:years?|yrs?)\s*(?:term|tenure|policy)",
        r"(\d+)\s*-\s*(?:year|yr)\s*(?:plan|policy)",
    ]
    for pat in tenure_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["tenure_years"] = int(m.group(1))
            break

    # Maturity patterns
    maturity_patterns = [
        r"(?:maturity\s+(?:amount|value|benefit)|maturity\s+payable)[\s:]*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)",
        r"maturity[\s:]*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)",
        r"([\d,]+(?:\.\d+)?)\s*(?:on\s+maturity|at\s+maturity)",
        r"guaranteed\s+maturity[\s:]*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)",
    ]
    for pat in maturity_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["maturity_amount"] = _parse_number(m.group(1))
            break

    # Sum assured
    sa_patterns = [
        r"(?:sum\s+assured|death\s+benefit|cover)[\s:]*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)",
        r"([\d,]+(?:\.\d+)?)\s*(?:sum\s+assured|lakh\s+cover)",
        r"(?:cover\s+of|cover\s+amount)[\s:]*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)",
    ]
    for pat in sa_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["sum_assured"] = _parse_number(m.group(1))
            break

    return result


def _parse_number(s: str) -> float:
    """Parse number string (handles commas)."""
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0


def merge_with_ai(ai_data: dict[str, Any], regex_data: dict[str, Any]) -> None:
    """
    Fill AI data with regex values where AI returned null.

    Modifies ai_data in place.
    """
    filled = []
    for key in ("premium_amount", "tenure_years", "maturity_amount", "sum_assured"):
        if ai_data.get(key) is None and regex_data.get(key) is not None:
            ai_data[key] = regex_data[key]
            filled.append(key)
    if filled:
        logger.debug("Regex filled missing fields: %s", filled)
