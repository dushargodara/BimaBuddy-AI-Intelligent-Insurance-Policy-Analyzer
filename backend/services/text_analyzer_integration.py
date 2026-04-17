"""
Integration example for text analyzer in the API pipeline.
This shows how to integrate the analyze_policy_text function into the existing API.
"""

def analyze_policy_with_text_insights(policy_text, financial_data=None):
    """
    Complete policy analysis combining text insights with financial data.
    
    Args:
        policy_text (str): Raw text extracted from PDF
        financial_data (dict, optional): Financial calculation results
    
    Returns:
        dict: Complete analysis results
    """
    from .text_analyzer import analyze_policy_text
    
    # Get textual insights
    text_insights = analyze_policy_text(policy_text)
    
    # Combine with financial data if available
    complete_analysis = {
        "text_analysis": text_insights,
        "financial_analysis": financial_data or {},
        "policy_health_score": _calculate_policy_health_score(text_insights, financial_data)
    }
    
    return complete_analysis


def _calculate_policy_health_score(text_insights, financial_data):
    """
    Calculate a simple health score based on text insights and financial data.
    """
    score = 50  # Base score
    
    # Positive indicators
    if text_insights.get("key_benefits"):
        score += min(len(text_insights["key_benefits"]) * 2, 20)
    
    # Negative indicators
    if text_insights.get("exclusions"):
        score -= min(len(text_insights["exclusions"]) * 3, 15)
    
    if text_insights.get("hidden_clauses"):
        score -= min(len(text_insights["hidden_clauses"]) * 2, 20)
    
    # Financial indicators
    if financial_data:
        roi = financial_data.get("roi", 0)
        if roi and roi > 50:  # Good ROI
            score += 15
        elif roi and roi < 20:  # Poor ROI
            score -= 10
    
    return max(0, min(100, score))


# Example usage in API route
def example_api_integration():
    """
    Example of how to integrate text analysis into the existing API pipeline.
    """
    
    # In your existing API route after extracting text:
    """
    # After getting full_text from PDF
    financial_result = compute_financials(data)
    
    # Add text analysis
    text_insights = analyze_policy_text(full_text)
    
    # Combine results
    final_result = {
        **financial_result,
        "policy_summary": text_insights["policy_summary"],
        "key_benefits": text_insights["key_benefits"],
        "exclusions": text_insights["exclusions"],
        "hidden_clauses": text_insights["hidden_clauses"]
    }
    
    return jsonify(final_result)
    """
    pass
