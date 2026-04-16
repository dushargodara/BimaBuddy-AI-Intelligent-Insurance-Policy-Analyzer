"""
Hidden clause analyzer for insurance policy documents.

Detects risky clauses, penalties, and unfavorable terms.
"""

import re
from typing import List, Dict, Any

from backend.core.logger import get_logger

logger = get_logger(__name__)


def detect_hidden_clauses(text: str) -> List[Dict[str, Any]]:
    """
    Detect hidden clauses and risky terms in policy document.
    
    Args:
        text: Policy document text
        
    Returns:
        List of detected clauses with descriptions
    """
    text_lower = text.lower()
    hidden_clauses = []
    
    # High surrender penalties
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
    
    # Non-guaranteed returns
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
                "recommendation": "Returns depend on company performance. Not suitable for risk-averse investors."
            })
    
    # Market-linked returns
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
                "recommendation": "Market-linked returns can be volatile. Understand the risk-reward profile."
            })
    
    # Mortality charges
    mortality_patterns = [
        r"mortality\s*charge",
        r"cost\s*of\s*insurance",
        r"mortality\s*deduction",
        r"policy\s*account\s*charge",
    ]
    
    for pattern in mortality_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            hidden_clauses.append({
                "type": "mortality_charges",
                "severity": "medium",
                "description": "Mortality charges reduce returns",
                "snippet": match.group(0),
                "recommendation": "Mortality charges reduce effective returns. Compare with term insurance + investment."
            })
    
    # Policy lapse risk
    lapse_patterns = [
        r"policy\s*lapse",
        r"lapse\s*if\s*premium.*?not\s*paid",
        r"revival\s*period",
        r"grace\s*period.*?lapse",
    ]
    
    for pattern in lapse_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            hidden_clauses.append({
                "type": "lapse_risk",
                "severity": "high",
                "description": "Policy can lapse if premiums missed",
                "snippet": match.group(0),
                "recommendation": "Ensure premium payment discipline to avoid policy lapse and loss of benefits."
            })
    
    # Limited premium guarantee
    guarantee_patterns = [
        r"guarantee.*?limited",
        r"guaranteed.*?for\s*only\s*(\d+)\s*years?",
        r"premium\s*guarantee.*?limited",
        r"capital\s*guarantee.*?conditional",
    ]
    
    for pattern in guarantee_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            hidden_clauses.append({
                "type": "limited_guarantee",
                "severity": "medium",
                "description": "Premium guarantee is limited or conditional",
                "snippet": match.group(0),
                "recommendation": "Guarantees are limited. Understand the conditions and time period."
            })
    
    # High allocation charges
    allocation_patterns = [
        r"allocation\s*charge.*?(\d+)%?",
        r"premium\s*allocation.*?(\d+)%?",
        r"entry\s*load.*?(\d+)%?",
        r"initial\s*charge.*?(\d+)%?",
    ]
    
    for pattern in allocation_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            charge_percent = match.group(1) if match.groups() else "high"
            severity = "high" if charge_percent != "high" and int(charge_percent) > 5 else "medium"
            hidden_clauses.append({
                "type": "allocation_charges",
                "severity": severity,
                "description": f"High allocation charges ({charge_percent}%)",
                "snippet": match.group(0),
                "recommendation": "High allocation charges reduce initial investment. Compare with other options."
            })
    
    # Fund switching restrictions
    switching_patterns = [
        r"limited\s*switching",
        r"switching\s*charge",
        r"fund\s*switch.*?restricted",
        r"switching.*?only\s*(\d+)\s*times?",
    ]
    
    for pattern in switching_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            hidden_clauses.append({
                "type": "switching_restrictions",
                "severity": "low",
                "description": "Fund switching restrictions or charges",
                "snippet": match.group(0),
                "recommendation": "Limited fund switching flexibility. Consider if this matches your investment strategy."
            })
    
    # Withdrawal restrictions
    withdrawal_patterns = [
        r"withdrawal.*?restricted",
        r"partial\s*withdrawal.*?not\s*allowed",
        r"withdrawal.*?only\s*after\s*(\d+)\s*years?",
        r"lock\s*in\s*period.*?(\d+)\s*years?",
    ]
    
    for pattern in withdrawal_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            hidden_clauses.append({
                "type": "withdrawal_restrictions",
                "severity": "medium",
                "description": "Withdrawal restrictions or lock-in period",
                "snippet": match.group(0),
                "recommendation": "Limited liquidity. Ensure this aligns with your cash flow needs."
            })
    
    # Remove duplicates based on type
    unique_clauses = []
    seen_types = set()
    
    for clause in hidden_clauses:
        if clause["type"] not in seen_types:
            unique_clauses.append(clause)
            seen_types.add(clause["type"])
    
    logger.info("Detected %d hidden clauses", len(unique_clauses))
    return unique_clauses


def analyze_clause_severity(clauses: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Analyze severity distribution of detected clauses.
    
    Args:
        clauses: List of detected clauses
        
    Returns:
        Dictionary with severity counts
    """
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    
    for clause in clauses:
        severity = clause.get("severity", "low")
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    return severity_counts


def get_clause_recommendations(clauses: List[Dict[str, Any]]) -> List[str]:
    """
    Generate overall recommendations based on detected clauses.
    
    Args:
        clauses: List of detected clauses
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    severity_counts = analyze_clause_severity(clauses)
    
    if severity_counts["high"] > 0:
        recommendations.append("⚠️ Policy has multiple high-risk clauses. Review carefully before investing.")
    
    clause_types = [clause["type"] for clause in clauses]
    
    if "market_linked" in clause_types:
        recommendations.append("📈 Market-linked returns mean volatility. Ensure you understand the risks.")
    
    if "surrender_penalty" in clause_types:
        recommendations.append("💸 High surrender charges reduce flexibility. Consider your liquidity needs.")
    
    if "lapse_risk" in clause_types:
        recommendations.append("⏰ Policy lapse risk exists. Maintain premium payment discipline.")
    
    if "non_guaranteed_returns" in clause_types:
        recommendations.append("🎯 Returns are not guaranteed. Compare with guaranteed options.")
    
    if severity_counts["medium"] > 2:
        recommendations.append("📋 Multiple medium-risk clauses detected. Read all terms carefully.")
    
    if not clauses:
        recommendations.append("✅ No significant hidden clauses detected. Policy terms appear straightforward.")
    
    return recommendations
