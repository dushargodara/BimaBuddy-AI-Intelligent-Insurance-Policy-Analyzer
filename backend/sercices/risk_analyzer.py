"""
Enhanced risk analysis service for insurance policies.

Comprehensive risk scoring with multiple factors and policy type considerations.
"""

import re
from typing import Any, List, Dict

from backend.services.clause_analyzer import detect_hidden_clauses
from backend.core.logger import get_logger

logger = get_logger(__name__)


def detect_risky_clauses(text: str) -> list[dict[str, Any]]:
    """
    Detect and highlight risky clauses using enhanced analysis.
    
    Args:
        text: Policy document text.
        
    Returns:
        List of dicts with clause information.
    """
    # Use the new clause analyzer for comprehensive detection
    return detect_hidden_clauses(text)


def calculate_risk_score(
    cagr_percent: float = 0,
    policy_term: int = 0,
    is_guaranteed_return: bool = True,
    premium_payment_term: int = 0,
    policy_type: str = "endowment",
    risky_clauses_count: int = 0,
    sum_assured: float = 0,
    yearly_premium: float = 0,
) -> int:
    """
    Calculate comprehensive risk score from 1 (low) to 10 (high).
    
    Enhanced risk rules based on policy characteristics:
    
    Args:
        cagr_percent: CAGR percentage
        policy_term: Policy term in years
        is_guaranteed_return: Whether returns are guaranteed
        premium_payment_term: Years premium is paid
        policy_type: Type of insurance policy
        risky_clauses_count: Number of risky clauses detected
        sum_assured: Sum assured amount
        yearly_premium: Annual premium amount
        
    Returns:
        Risk score 1-10
    """
    score = 0.0
    risk_factors = []
    
    # Rule 1: Low CAGR (< 5%) → add 3 risk points
    if cagr_percent < 5 and cagr_percent > 0:
        score += 3
        risk_factors.append("Low CAGR (< 5%)")
    elif cagr_percent < 7 and cagr_percent > 0:
        score += 1
        risk_factors.append("Moderate CAGR (< 7%)")
    
    # Rule 2: Long policy term (> 20 years) → add 2 points
    if policy_term > 20:
        score += 2
        risk_factors.append("Long policy term (> 20 years)")
    elif policy_term > 15:
        score += 1
        risk_factors.append("Moderately long policy term (> 15 years)")
    
    # Rule 3: Non-guaranteed returns → add 2 points
    if not is_guaranteed_return:
        score += 2
        risk_factors.append("Non-guaranteed returns")
    
    # Rule 4: Long premium payment term (> 15 years) → add 1 point
    if premium_payment_term > 15:
        score += 1
        risk_factors.append("Long premium payment term (> 15 years)")
    
    # Rule 5: ULIP policies → add 2 points (market risk)
    if policy_type.lower() == "ulip":
        score += 2
        risk_factors.append("ULIP (market-linked risk)")
    
    # Rule 6: High premium to sum assured ratio
    if sum_assured > 0 and yearly_premium > 0:
        premium_ratio = (yearly_premium * premium_payment_term) / sum_assured
        if premium_ratio > 0.5:  # Premium > 50% of sum assured
            score += 2
            risk_factors.append("High premium to sum assured ratio")
        elif premium_ratio > 0.3:
            score += 1
            risk_factors.append("Moderate premium to sum assured ratio")
    
    # Rule 7: Money Back policies (complexity risk)
    if policy_type.lower() == "money_back":
        score += 1
        risk_factors.append("Money Back policy (complex structure)")
    
    # Rule 8: Child policies (long-term commitment)
    if policy_type.lower() == "child_plan":
        score += 1
        risk_factors.append("Child plan (long-term commitment)")
    
    # Rule 9: Pension policies (interest rate risk)
    if policy_type.lower() == "pension":
        score += 1
        risk_factors.append("Pension plan (interest rate risk)")
    
    # Rule 10: Risky clauses count
    if risky_clauses_count >= 5:
        score += 2
        risk_factors.append("Multiple risky clauses")
    elif risky_clauses_count >= 3:
        score += 1
        risk_factors.append("Some risky clauses")
    
    # Rule 11: Term insurance with low sum assured
    if policy_type.lower() == "term" and sum_assured < 1000000:
        score += 1
        risk_factors.append("Term insurance with low coverage")
    
    # Rule 12: Whole life policies (very long term)
    if policy_type.lower() == "whole_life":
        score += 1
        risk_factors.append("Whole life policy (very long term)")
    
    # Ensure minimum score of 1 and maximum of 10
    final_score = max(1, min(10, int(round(score))))
    
    logger.info("Risk score calculated: %d (factors: %s)", final_score, ", ".join(risk_factors))
    
    return final_score


def get_risk_level(score: int) -> str:
    """
    Map risk score to level description.
    
    Risk scale:
    0-3: Low Risk
    4-6: Medium Risk  
    7-10: High Risk
    
    Args:
        score: Risk score 1-10
        
    Returns:
        Risk level string with emoji indicator
    """
    if score <= 3:
        return "🟢 Low Risk"
    elif score <= 6:
        return "🟡 Medium Risk"
    else:
        return "🔴 High Risk"


def get_risk_factors_description(score: int, policy_type: str = "") -> Dict[str, Any]:
    """
    Get detailed risk factor descriptions based on score and policy type.
    
    Args:
        score: Risk score
        policy_type: Type of policy
        
    Returns:
        Dictionary with risk analysis
    """
    analysis = {
        "score": score,
        "level": get_risk_level(score),
        "factors": [],
        "recommendations": [],
        "suitable_for": [],
    }
    
    # Add factor descriptions based on score ranges
    if score >= 7:
        analysis["factors"].extend([
            "High risk profile with multiple concerns",
            "Requires careful consideration before investment",
            "May not be suitable for risk-averse investors"
        ])
        analysis["recommendations"].extend([
            "Review all policy terms carefully",
            "Consider alternative investment options",
            "Ensure you understand all risks involved"
        ])
        analysis["suitable_for"] = ["High-risk tolerance investors"]
        
    elif score >= 4:
        analysis["factors"].extend([
            "Moderate risk with some concerns",
            "Balanced risk-reward profile",
            "Suitable for most investors with some risk tolerance"
        ])
        analysis["recommendations"].extend([
            "Understand the risk factors",
            "Compare with guaranteed return options",
            "Consider your financial goals"
        ])
        analysis["suitable_for"] = ["Moderate risk tolerance investors"]
        
    else:
        analysis["factors"].extend([
            "Low risk profile",
            "Conservative investment approach",
            "Suitable for risk-averse investors"
        ])
        analysis["recommendations"].extend([
            "Good for conservative investors",
            "Stable returns expected",
            "Lower risk of capital loss"
        ])
        analysis["suitable_for"] = ["Risk-averse investors", "Conservative investors"]
    
    # Add policy-type specific recommendations
    if policy_type.lower() == "ulip":
        analysis["recommendations"].append("ULIP returns depend on market performance")
    elif policy_type.lower() == "money_back":
        analysis["recommendations"].append("Money Back policies have complex structures")
    elif policy_type.lower() == "term":
        analysis["recommendations"].append("Term insurance provides pure protection")
    
    return analysis


def generate_risk_report(
    score: int,
    policy_type: str = "",
    cagr_percent: float = 0,
    clauses: List[Dict] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive risk report.
    
    Args:
        score: Risk score
        policy_type: Policy type
        cagr_percent: CAGR percentage
        clauses: List of risky clauses
        
    Returns:
        Complete risk analysis report
    """
    if clauses is None:
        clauses = []
    
    report = get_risk_factors_description(score, policy_type)
    
    # Add clause analysis
    if clauses:
        high_severity = sum(1 for c in clauses if c.get("severity") == "high")
        medium_severity = sum(1 for c in clauses if c.get("severity") == "medium")
        
        report["clause_analysis"] = {
            "total_clauses": len(clauses),
            "high_severity": high_severity,
            "medium_severity": medium_severity,
            "main_concerns": [c["description"] for c in clauses[:3]]
        }
    
    # Add performance analysis
    if cagr_percent > 0:
        if cagr_percent < 5:
            report["performance_analysis"] = "Low returns relative to risk"
        elif cagr_percent < 8:
            report["performance_analysis"] = "Moderate returns for risk level"
        else:
            report["performance_analysis"] = "Good returns for risk level"
    
    return report
