"""
AI validation layer for financial number verification.

Validates and corrects extracted financial values using AI.
"""

from typing import Dict, Any, Optional

from backend.core.exceptions import AIAnalysisError
from backend.core.logger import get_logger

logger = get_logger(__name__)


def validate_financial_values(
    text: str,
    extracted_values: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate extracted financial values using AI.
    
    Args:
        text: Original policy document text
        extracted_values: Values extracted by regex
        
    Returns:
        Validated and corrected financial values
        
    Raises:
        AIAnalysisError: If AI validation fails
    """
    try:
        from google import genai
    except ImportError as e:
        raise AIAnalysisError(
            "google-genai not installed. Run: pip install google-genai",
            details={"import_error": str(e)},
        ) from e
    
    from config import GEMINI_API_KEY, GEMINI_MODEL
    
    if not GEMINI_API_KEY:
        raise AIAnalysisError("GEMINI_API_KEY is not set")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Build validation prompt
    prompt = _build_validation_prompt(text, extracted_values)
    
    try:
        logger.info("Requesting AI validation of financial values")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "temperature": 0.1,
                "top_p": 0.95,
                "max_output_tokens": 2048,
            },
        )
        
        if not response.text:
            logger.warning("AI validation returned empty response")
            return extracted_values
        
        # Parse AI response
        validated_values = _parse_validation_response(response.text)
        
        # Merge with original values, preferring AI corrections
        merged_values = _merge_validated_data(extracted_values, validated_values)
        
        logger.info("AI validation completed successfully")
        return merged_values
        
    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "429" in error_msg:
            logger.warning("AI quota exceeded during validation, using extracted values")
            return extracted_values
        elif "404" in error_msg or "not found" in error_msg:
            raise AIAnalysisError(
                f"Gemini model '{GEMINI_MODEL}' not found. Set GEMINI_MODEL in .env",
                details={"error": str(e)},
            ) from e
        else:
            logger.warning("AI validation failed: %s", e)
            return extracted_values


def _build_validation_prompt(text: str, values: Dict[str, Any]) -> str:
    """
    Build comprehensive validation prompt for AI.
    
    Args:
        text: Original policy text
        values: Extracted financial values
        
    Returns:
        Validation prompt string
    """
    # Format extracted values for display
    formatted_values = []
    for key, value in values.items():
        if value is not None:
            formatted_values.append(f"{key}: {value}")
    
    values_text = "\\n".join(formatted_values)
    
    prompt = f"""You are an expert insurance policy analyst. 

I have extracted the following financial values from an insurance policy document:

{values_text}

Please verify these values against the policy document text below and correct them if necessary:

DOCUMENT TEXT:
---
{text[:5000]}
---

VALIDATION RULES:
1. Check if each value matches the document text exactly
2. Correct any obvious errors (decimal points, commas, etc.)
3. If a value is clearly wrong, provide the correct value
4. If a value cannot be found in the document, set it to null
5. Ensure all currency amounts are in numbers (no symbols)
6. Verify that premium_payment_term <= policy_term
7. Verify that maturity_value >= sum_assured (for non-term policies)
8. Return ONLY valid JSON response

Return JSON with the same structure as input but with corrected values:

{{
    "yearly_premium": number or null,
    "premium_payment_term": number or null,
    "policy_term": number or null,
    "sum_assured": number or null,
    "guaranteed_maturity_value": number or null,
    "non_guaranteed_maturity_value": number or null,
    "bonus_rate": number or null,
    "reversionary_bonus": number or null,
    "terminal_bonus": number or null,
    "death_benefit": number or null,
    "survival_benefit": number or null,
    "policy_start_age": number or null,
    "maturity_age": number or null
}}

Return ONLY the JSON object, no explanations or markdown."""
    
    return prompt


def _parse_validation_response(response_text: str) -> Dict[str, Any]:
    """
    Parse AI validation response and extract JSON.
    
    Args:
        response_text: AI response text
        
    Returns:
        Parsed financial values dictionary
    """
    import json
    import re
    
    # Try to extract JSON from response
    json_match = re.search(r'\\{.*\\}', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse AI validation JSON: %s", e)
    
    # Fallback: try parsing entire response
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        logger.warning("AI validation response is not valid JSON")
        return {}
    
    return {}


def _merge_validated_data(
    original: Dict[str, Any], 
    validated: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge original and validated financial values.
    
    Args:
        original: Originally extracted values
        validated: AI-validated values
        
    Returns:
        Merged values with AI corrections prioritized
    """
    merged = original.copy()
    corrections = []
    
    for key, value in validated.items():
        if value is not None:
            if original.get(key) is None:
                # AI found a value that was missing
                merged[key] = value
                corrections.append(f"Added {key}: {value}")
            elif original.get(key) != value:
                # AI corrected a value
                merged[key] = value
                corrections.append(f"Corrected {key}: {original.get(key)} → {value}")
    
    if corrections:
        logger.info("AI validation corrections: %s", ", ".join(corrections))
    
    return merged


def validate_policy_consistency(values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate internal consistency of financial values.
    
    Args:
        values: Financial values to validate
        
    Returns:
        Validation results with any corrections
    """
    validation_results = values.copy()
    corrections = []
    
    # Check premium payment term vs policy term
    ppt = values.get("premium_payment_term")
    pt = values.get("policy_term")
    
    if ppt and pt and ppt > pt:
        validation_results["premium_payment_term"] = pt
        corrections.append(f"Corrected premium_payment_term: {ppt} → {pt}")
    
    # Check maturity vs sum assured for non-term policies
    maturity = values.get("guaranteed_maturity_value")
    sa = values.get("sum_assured")
    
    if maturity and sa and maturity < sa:
        # For non-term policies, maturity should typically be >= sum assured
        logger.warning("Maturity value less than sum assured: %s < %s", maturity, sa)
    
    # Check age consistency
    start_age = values.get("policy_start_age")
    maturity_age = values.get("maturity_age")
    term = values.get("policy_term")
    
    if start_age and maturity_age and term:
        expected_maturity_age = start_age + term
        if abs(maturity_age - expected_maturity_age) > 2:
            corrections.append(f"Age inconsistency detected: {start_age} + {term} ≠ {maturity_age}")
    
    if corrections:
        logger.info("Consistency validation corrections: %s", ", ".join(corrections))
    
    return validation_results


def create_validation_summary(
    original: Dict[str, Any],
    validated: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create summary of validation changes.
    
    Args:
        original: Original extracted values
        validated: Validated values
        
    Returns:
        Validation summary with changes
    """
    changes = []
    
    for key in validated:
        orig_val = original.get(key)
        val_val = validated.get(key)
        
        if orig_val != val_val:
            if orig_val is None:
                changes.append({
                    "field": key,
                    "type": "added",
                    "original": None,
                    "validated": val_val
                })
            elif val_val is None:
                changes.append({
                    "field": key,
                    "type": "removed",
                    "original": orig_val,
                    "validated": None
                })
            else:
                changes.append({
                    "field": key,
                    "type": "corrected",
                    "original": orig_val,
                    "validated": val_val
                })
    
    return {
        "total_changes": len(changes),
        "changes": changes,
        "validation_confidence": "high" if len(changes) < 3 else "medium"
    }
