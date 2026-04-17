"""
Hidden clause analyzer for insurance policy documents.

Detects risky clauses, penalties, and unfavorable terms.
"""

import re
import logging
from typing import List, Dict, Any

# ✅ FIX: Replace broken import with standard logger
logger = logging.getLogger(__name__)


def detect_hidden_clauses(text: str) -> List[Dict[str, Any]]:
    text_lower = text.lower()
    hidden_clauses = []
    
    surrender_patterns = [
        r"surrender\s*charge.*?(\d+)%?\s*of\s*premium",
        r"surrender\s*penalty.*?(\d+)%?",
        r"high\s*surrender\s*charges?",
        r"surrender\s*value.*?less\s*than\s*premium",
    ]
    
    for pattern in surrender_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            hidden_clauses.append({
                "type": "surrender_penalty",
                "severity": "high",
                "description": "High surrender penalties",
                "snippet": match.group(0),
                "recommendation": "Policy has high surrender charges. Consider liquidity needs before investing."
            })
    
    non_guaranteed_patterns = [
        r"non\s*guaranteed\s*bonus",
        r"bonus.*?not\s*guaranteed",
        r"returns.*?not\s*guaranteed",
        r"subject\s*to\s*market\s*risk",
        r"bonus.*?depends\s*on\s*company\s*performance",
    ]
    
    for pattern in non_guaranteed_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            hidden_clauses.append({
                "type": "non_guaranteed_returns",
                "severity": "medium",
                "description": "Returns are not guaranteed",
                "snippet": match.group(0),
                "recommendation": "Returns depend on company performance."
            })
    
    market_linked_patterns = [
        r"market\s*linked",
        r"unit\s*linked",
        r"nav\s*based",
        r"depends\s*on\s*market\s*performance",
        r"subject\s*to\s*market\s*risk",
    ]
    
    for pattern in market_linked_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            hidden_clauses.append({
                "type": "market_linked",
                "severity": "high",
                "description": "Returns depend on market performance",
                "snippet": match.group(0),
                "recommendation": "Market-linked returns can be volatile."
            })
    
    lapse_patterns = [
        r"policy\s*lapse",
        r"lapse\s*if\s*premium.*?not\s*paid",
        r"revival\s*period",
    ]
    
    for pattern in lapse_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            hidden_clauses.append({
                "type": "lapse_risk",
                "severity": "high",
                "description": "Policy can lapse",
                "snippet": match.group(0),
                "recommendation": "Ensure premium payment discipline."
            })
    
    unique_clauses = []
    seen_types = set()
    
    for clause in hidden_clauses:
        if clause["type"] not in seen_types:
            unique_clauses.append(clause)
            seen_types.add(clause["type"])
    
    logger.info("Detected %d hidden clauses", len(unique_clauses))
    return unique_clauses


def analyze_clause_severity(clauses: List[Dict[str, Any]]) -> Dict[str, int]:
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    
    for clause in clauses:
        severity = clause.get("severity", "low")
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    return severity_counts


def get_clause_recommendations(clauses: List[Dict[str, Any]]) -> List[str]:
    recommendations = []
    severity_counts = analyze_clause_severity(clauses)
    
    if severity_counts["high"] > 0:
        recommendations.append("⚠️ High-risk clauses detected.")
    
    if not clauses:
        recommendations.append("✅ No major hidden clauses detected.")
    
    return recommendations
