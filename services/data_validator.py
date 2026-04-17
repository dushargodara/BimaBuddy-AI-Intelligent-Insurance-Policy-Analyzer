def validate_policy_data(data):
    """
    Validation layer for policy data before financial calculations.
    Ensures data integrity and fixes common issues without overriding valid values.
    """
    try:
        # Extract values without forced defaults - preserve originals
        premium = data.get("premium")
        policy_term = data.get("policy_term")
        payment_term = data.get("payment_term")
        maturity_benefit = data.get("maturity_value")
        
        validation_issues = []
        
        print("=== BUSINESS VALIDATION START ===")
        print("INPUT DATA:", data)
        
        # Validate premium
        if premium is not None:
            if premium <= 0:
                validation_issues.append("Premium must be greater than 0")
            elif premium > 10000000:  # More than 1 crore per year
                validation_issues.append("Premium seems unusually high")
        else:
            validation_issues.append("Premium is None")
        
        # Validate policy term
        if policy_term is not None:
            if policy_term <= 0:
                validation_issues.append("Policy term must be greater than 0")
            elif policy_term > 50:  # More than 50 years
                validation_issues.append("Policy term seems unusually long")
        else:
            validation_issues.append("Policy term is None")
        
        # Validate payment term
        if payment_term is not None:
            if payment_term <= 0:
                validation_issues.append("Payment term must be greater than 0")
            elif policy_term is not None and payment_term > policy_term:
                validation_issues.append("Payment term cannot exceed policy term")
        else:
            validation_issues.append("Payment term is None")
        
        # Validate maturity benefit
        if maturity_benefit is not None:
            if maturity_benefit < 0:
                validation_issues.append("Maturity benefit cannot be negative")
            elif maturity_benefit > 100000000:  # More than 10 crore
                validation_issues.append("Maturity benefit seems unusually high")
        else:
            validation_issues.append("Maturity benefit is None")
        
        # Additional business logic validations - only if values exist
        if premium is not None and maturity_benefit is not None:
            if maturity_benefit < premium:
                validation_issues.append("Maturity benefit seems too low compared to premiums")
        
        if premium is not None and payment_term is not None:
            total_investment = premium * payment_term
            if maturity_benefit is not None and maturity_benefit > 0 and maturity_benefit < total_investment * 0.5:
                validation_issues.append("Maturity benefit seems too low compared to total investment")
        
        print("VALIDATION ISSUES:", validation_issues)
        
        # Return original data with validation issues - NO OVERRIDING
        result = {
            "premium": premium,  # Preserve original
            "policy_term": policy_term,  # Preserve original
            "payment_term": payment_term,  # Preserve original
            "maturity_value": maturity_benefit,  # Preserve original
            "validation_issues": validation_issues
        }
        
        print("BUSINESS VALIDATION RESULT:", result)
        print("=== BUSINESS VALIDATION END ===")
        
        return result
        
    except Exception as e:
        print("BUSINESS VALIDATION ERROR:", e)
        # Return safe fallback with original data
        return {
            "premium": data.get("premium"),
            "policy_term": data.get("policy_term"),
            "payment_term": data.get("payment_term"),
            "maturity_value": data.get("maturity_value"),
            "validation_issues": ["Business validation system error occurred"]
        }
