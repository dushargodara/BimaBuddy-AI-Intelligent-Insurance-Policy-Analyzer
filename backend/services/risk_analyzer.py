"""
Risk analyzer for insurance policy.

Calculates risk score and level based on clauses and features.
"""

import logging
from typing import List, Dict, Any

# ✅ FIX: Removed backend.core dependency
logger = logging.getLogger(__name__)


def detect_risky_clauses(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter only high-risk clauses.

    Args:
        clauses: List of detected clauses

    Returns:
        List of risky clauses
    """
    risky = [c for c in clauses if c.get("severity") == "high"]
    logger.info("Detected %d risky clauses", len(risky))
    return risky


def get_risk_level(score: float) -> str:
    """
    Convert numeric score to risk level.

    Args:
        score: Risk score (0–10)

    Returns:
        Risk level string
    """
    if score <= 3:
        return "Low"
    elif score <= 6:
        return "Medium"
    else:
        return "High"


def calculate_risk_score(clauses: List[Dict[str, Any]]) -> float:
    """
    Calculate overall risk score.

    Args:
        clauses: List of detected clauses

    Returns:
        Risk score (0–10)
    """
    score = 0

    for clause in clauses:
        severity = clause.get("severity", "low")

        if severity == "high":
            score += 3
        elif severity == "medium":
            score += 2
        else:
            score += 1

    # Normalize score to 0–10
    score = min(score, 10)

    logger.info("Calculated risk score: %s", score)
    return score
