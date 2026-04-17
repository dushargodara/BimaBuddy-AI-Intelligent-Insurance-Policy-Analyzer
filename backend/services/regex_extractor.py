"""
Regex-based financial data extraction from policy documents.

Enhanced with comprehensive patterns for all insurance policy financial fields.
"""

import re
from typing import Any

from backend.core.logger import get_logger

logger = get_logger(__name__)


def extract_financial_values(text: str) -> dict[str, Any]:
    """
    Extract comprehensive financial values from policy text using regex patterns.

    Args:
        text: Policy document text.

    Returns:
        Dict with all extracted financial fields.
    """
    result: dict[str, Any] = {
        "yearly_premium": None,
        "premium_payment_term": None,
        "policy_term": None,
        "sum_assured": None,
        "guaranteed_maturity_value": None,
        "non_guaranteed_maturity_value": None,
        "bonus_rate": None,
        "reversionary_bonus": None,
        "terminal_bonus": None,
        "death_benefit": None,
        "survival_benefit": None,
        "policy_start_age": None,
        "maturity_age": None,
    }

    # Premium patterns - enhanced with multiple keywords
    premium_patterns = [
        r"annual premium[^0-9]*([\d,]+)",
        r"yearly premium[^0-9]*([\d,]+)",
        r"modal premium[^0-9]*([\d,]+)",
        r"premium payable[^0-9]*([\d,]+)",
        r"premium amount[^0-9]*([\d,]+)",
        r"installment premium[^0-9]*([\d,]+)",
        r"total premium[^0-9]*([\d,]+)",
        r"premium.*?₹?\s?([\d,]+(?:\.\d+)?)\s*(?:per\s+year|p\.?a\.?|annual)",
        r"₹?\s*([\d,]+(?:\.\d+)?)\s*(?:per\s+annum|p\.?a\.?)",
        r"rs\.?\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac)\s*(?:per\s+year|annual)",
    ]
    
    for pat in premium_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["yearly_premium"] = normalize_amount(m.group(1))
            break

    # Premium Payment Term patterns - enhanced with multiple keywords
    ppt_patterns = [
        r"premium payment term[^0-9]*(\d+)",
        r"premium paying term[^0-9]*(\d+)",
        r"ppt[^0-9]*(\d+)",
        r"premium\s*payment\s*term.*?(\d+)\s*years?",
        r"pay\s*premium\s*for.*?(\d+)\s*years?",
        r"premium\s*paying\s*term.*?(\d+)\s*years?",
        r"limited\s*premium\s*payment.*?(\d+)\s*years?",
    ]
    
    for pat in ppt_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["premium_payment_term"] = int(m.group(1))
            break

    # Policy Term patterns
    policy_term_patterns = [
        r"policy\s*term.*?(\d+)\s*years?",
        r"term\s*of\s*policy.*?(\d+)\s*years?",
        r"policy\s*period.*?(\d+)\s*years?",
        r"coverage\s*period.*?(\d+)\s*years?",
        r"(\d+)\s*years?\s*(?:policy|plan|term)",
    ]
    
    for pat in policy_term_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["policy_term"] = int(m.group(1))
            break

    # Sum Assured patterns
    sum_assured_patterns = [
        r"(?:sum\s*assured|basic\s*sum\s*assured).*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"death\s*benefit.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"sum\s*assured[\s:]*₹?\s?([\d,]+(?:\.\d+)?)",
        r"basic\s*sum\s*assured[\s:]*₹?\s?([\d,]+(?:\.\d+)?)",
        r"₹?\s*([\d,]+(?:\.\d+)?)\s*(?:sum\s*assured|lakh\s*cover)",
    ]
    
    for pat in sum_assured_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["sum_assured"] = normalize_amount(m.group(1))
            break

    # Maturity Value patterns
    maturity_patterns = [
        r"(?:maturity\s*(?:benefit|value)|maturity\s*payable).*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"guaranteed\s*maturity.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"maturity[\s:]*₹?\s?([\d,]+(?:\.\d+)?)",
        r"([\d,]+(?:\.\d+)?)\s*(?:on\s+maturity|at\s+maturity)",
        r"guaranteed\s*additions.*?₹?\s?([\d,]+(?:\.\d+)?)",
    ]
    
    for pat in maturity_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["guaranteed_maturity_value"] = normalize_amount(m.group(1))
            break

    # Non-Guaranteed Maturity patterns
    non_guaranteed_patterns = [
        r"non\s*guaranteed\s*maturity.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"projected\s*maturity.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"illustrated\s*maturity.*?₹?\s?([\d,]+(?:\.\d+)?)",
    ]
    
    for pat in non_guaranteed_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["non_guaranteed_maturity_value"] = normalize_amount(m.group(1))
            break

    # Bonus Rate patterns
    bonus_rate_patterns = [
        r"bonus\s*rate.*?(\d+(?:\.\d+)?)\s*%?",
        r"reversionary\s*bonus.*?(\d+(?:\.\d+)?)\s*%?",
        r"simple\s*reversionary\s*bonus.*?(\d+(?:\.\d+)?)\s*%?",
        r"bonus.*?(\d+(?:\.\d+)?)\s*%?\s*(?:per\s*annum|p\.?a\.?)",
    ]
    
    for pat in bonus_rate_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["bonus_rate"] = float(m.group(1))
            break

    # Reversionary Bonus patterns
    reversionary_patterns = [
        r"reversionary\s*bonus.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"simple\s*reversionary\s*bonus.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"annual\s*bonus.*?₹?\s?([\d,]+(?:\.\d+)?)",
    ]
    
    for pat in reversionary_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["reversionary_bonus"] = normalize_amount(m.group(1))
            break

    # Terminal Bonus patterns
    terminal_patterns = [
        r"terminal\s*bonus.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"final\s*bonus.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"maturity\s*bonus.*?₹?\s?([\d,]+(?:\.\d+)?)",
    ]
    
    for pat in terminal_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["terminal_bonus"] = normalize_amount(m.group(1))
            break

    # Death Benefit patterns
    death_benefit_patterns = [
        r"death\s*benefit.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"on\s*death.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"nominee\s*gets.*?₹?\s?([\d,]+(?:\.\d+)?)",
    ]
    
    for pat in death_benefit_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["death_benefit"] = normalize_amount(m.group(1))
            break

    # Survival Benefit patterns
    survival_patterns = [
        r"survival\s*benefit.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"survives?\s*the\s*term.*?₹?\s?([\d,]+(?:\.\d+)?)",
        r"intermediate\s*benefit.*?₹?\s?([\d,]+(?:\.\d+)?)",
    ]
    
    for pat in survival_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["survival_benefit"] = normalize_amount(m.group(1))
            break

    # Age patterns
    age_patterns = [
        r"entry\s*age.*?(\d+)\s*years?",
        r"minimum\s*age.*?(\d+)\s*years?",
        r"age\s*at\s*entry.*?(\d+)\s*years?",
        r"maturity\s*age.*?(\d+)\s*years?",
        r"age\s*at\s*maturity.*?(\d+)\s*years?",
    ]
    
    for pat in age_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            age = int(m.group(1))
            if "maturity" in pat.lower():
                result["maturity_age"] = age
            else:
                result["policy_start_age"] = age

    return result


def normalize_amount(value: str) -> int:
    """
    Normalize amount string to integer.
    
    Handles commas, currency symbols, and lakh/lac conversions.
    
    Args:
        value: Amount string with potential formatting.
        
    Returns:
        Normalized integer amount.
    """
    if not value:
        return 0
        
    # Remove currency symbols and whitespace
    cleaned = str(value).replace(",", "").replace("₹", "").replace("Rs", "").replace("rs", "").strip()
    
    # Handle lakh/lac conversions
    if "lakh" in cleaned.lower() or "lac" in cleaned.lower():
        number_match = re.search(r"([\d.]+)", cleaned)
        if number_match:
            return int(float(number_match.group(1)) * 100000)
    
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def merge_with_ai(ai_data: dict[str, Any], regex_data: dict[str, Any]) -> None:
    """
    Fill AI data with regex values where AI returned null.

    Modifies ai_data in place.
    """
    filled = []
    field_mapping = {
        "yearly_premium": "premium_amount",
        "policy_term": "tenure_years",
        "guaranteed_maturity_value": "maturity_amount",
    }
    
    for regex_key, ai_key in field_mapping.items():
        if ai_data.get(ai_key) is None and regex_data.get(regex_key) is not None:
            ai_data[ai_key] = regex_data[regex_key]
            filled.append(regex_key)
    
    # Add other fields directly
    for key in ["premium_payment_term", "sum_assured", "bonus_rate", "death_benefit"]:
        if ai_data.get(key) is None and regex_data.get(key) is not None:
            ai_data[key] = regex_data[key]
            filled.append(key)
    
    if filled:
        logger.debug("Regex filled missing fields: %s", filled)
