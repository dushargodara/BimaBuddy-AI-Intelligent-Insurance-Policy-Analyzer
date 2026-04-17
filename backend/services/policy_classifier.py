"""
Policy type classifier using regex and heuristics.

Detects Term, Endowment, ULIP, Money Back, Whole Life, Child Plan, and Pension policies.
"""

import re
from typing import Optional


def detect_policy_type(text: str, ai_policy_type: Optional[str] = None) -> str:
    """
    Detect policy type from document text and optional AI hint.

    Args:
        text: Policy document text.
        ai_policy_type: Optional AI-detected policy type.

    Returns:
        One of: "term", "endowment", "ulip", "whole_life", "money_back", "child_plan", "pension", "other".
    """
    text_lower = text.lower().strip()

    # AI hint takes precedence if present and valid
    if ai_policy_type:
        normalized = ai_policy_type.lower().strip()
        for ptype in ("term", "endowment", "ulip", "whole_life", "money_back", "child_plan", "pension"):
            if ptype in normalized:
                if "term" in normalized and "ulip" not in normalized:
                    return "term"
                if "ulip" in normalized or "unit linked" in normalized:
                    return "ulip"
                if "endowment" in normalized:
                    return "endowment"
                if "money back" in normalized:
                    return "money_back"
                if "whole" in normalized or "whole life" in normalized:
                    return "whole_life"
                if "child" in normalized:
                    return "child_plan"
                if "pension" in normalized or "retirement" in normalized:
                    return "pension"
                return ptype

    # Regex patterns for policy type detection
    patterns = {
        "ulip": [
            r"\bulip\b",
            r"unit\s+linked\s+insurance",
            r"unit\s+linked",
            r"fund\s+options?",
            r"nav\s*\(net\s+asset",
            r"allocation\s+charge",
            r"market\s+linked",
        ],
        "term": [
            r"\bterm\s+(?:life\s+)?insurance\b",
            r"\bterm\s+plan\b",
            r"pure\s+protection",
            r"no\s+maturity\s+benefit",
            r"death\s+benefit\s+only",
        ],
        "endowment": [
            r"\bendowment\s+(?:plan|policy)\b",
            r"\bendowment\s+insurance\b",
            r"maturity\s+benefit",
            r"guaranteed\s+maturity",
            r"survival\s+benefit",
        ],
        "whole_life": [
            r"whole\s+life",
            r"whole\s+life\s+insurance",
            r"lifelong\s+coverage",
        ],
        "money_back": [
            r"money\s+back",
            r"money\s+back\s+plan",
            r"intermediate\s+benefit",
            r"survival\s+benefit.*\d+.*%",
        ],
        "child_plan": [
            r"child\s+plan",
            r"child\s+insurance",
            r"education\s+plan",
            r"marriage\s+benefit",
            r"future\s+protect",
        ],
        "pension": [
            r"pension\s+plan",
            r"retirement\s+plan",
            r"annuity\s+plan",
            r"post\s+retirement",
            r"senior\s+citizen",
        ],
    }

    scores: dict[str, int] = {k: 0 for k in patterns}
    for ptype, pats in patterns.items():
        for pat in pats:
            if re.search(pat, text_lower, re.IGNORECASE):
                scores[ptype] += 1

    # ULIP and Term can co-occur; prefer ULIP if fund options mentioned
    if scores["ulip"] > 0:
        return "ulip"
    if scores["term"] > 0 and scores["endowment"] == 0 and scores["money_back"] == 0 and scores["child_plan"] == 0 and scores["pension"] == 0:
        return "term"
    if scores["money_back"] > 0:
        return "money_back"
    if scores["child_plan"] > 0:
        return "child_plan"
    if scores["pension"] > 0:
        return "pension"
    if scores["whole_life"] > 0:
        return "whole_life"
    if scores["endowment"] > 0:
        return "endowment"

    return "other"


def is_term_insurance(policy_type: str) -> bool:
    """
    Check if policy type is term (pure protection, no maturity).

    Args:
        policy_type: Detected policy type.

    Returns:
        True if term insurance.
    """
    return policy_type.lower() == "term"


def is_insurance_policy(text: str) -> bool:
    """
    Check if the document is likely an insurance policy based on keywords.
    """
    if not text:
        return False
        
    text_lower = text.lower()
    
    keywords = [
        "insurance", "policy", "premium", "assured", "maturity",
        "insurer", "insured", "endorsement", "bima", "jeevan",
        "surrender", "annuity", "nominee", "coverage", "death benefit",
        "policyholder", "sum assured"
    ]
    
    match_count = sum(1 for kw in keywords if kw in text_lower)
    
    return match_count >= 3
