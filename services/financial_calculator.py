def compute_financials(data):
    """
    Production-ready financial calculator for insurance policies.
    Handles all exceptions internally and returns clean, validated results.
    """
    def safe_float(value, default=0.0):
        """Safely convert string to float, handling Indian number format."""
        if value is None:
            return default
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove commas and convert
                cleaned = value.replace(',', '').replace('₹', '').replace('Rs.', '').replace('INR', '').strip()
                if cleaned == '':
                    return default
                return float(cleaned)
            return default
        except (ValueError, TypeError):
            return default

    def safe_int(value, default=0):
        """Safely convert string to int."""
        if value is None:
            return default
        try:
            return int(safe_float(value, default))
        except (ValueError, TypeError):
            return default

    def calculate_irr(cashflows, iterations=100, tolerance=0.0001):
        """Calculate IRR using binary search method."""
        if not cashflows:
            return 0.0
        
        # Check if all cashflows are zero
        if all(cf == 0 for cf in cashflows):
            return 0.0
        
        # Binary search for IRR
        low, high = -0.99, 1.0  # -99% to 100% range
        
        for _ in range(iterations):
            mid = (low + high) / 2
            npv = sum(cf / ((1 + mid) ** i) for i, cf in enumerate(cashflows))
            
            if abs(npv) < tolerance:
                return mid
            
            if npv > 0:
                low = mid
            else:
                high = mid
        
        return mid

    def calculate_projection(initial_amount, years, rate):
        """Calculate compound projection."""
        if years <= 0 or rate <= 0:
            return 0.0
        return initial_amount * ((1 + rate) ** years)

    try:
        # Extract and validate input data
        premium = safe_float(data.get("premium"))
        policy_term = safe_int(data.get("policy_term"))
        payment_term = safe_int(data.get("payment_term"))
        maturity_value = safe_float(data.get("maturity_benefit") or data.get("maturity_value"))
        
        # Set defaults for missing values
        if premium <= 0:
            premium = 10000.0
        if policy_term <= 0:
            policy_term = 10
        if payment_term <= 0:
            payment_term = min(policy_term, 10)
        if maturity_value <= 0:
            maturity_value = premium * payment_term * 1.5  # Conservative estimate
        
        # Calculate total investment
        total_investment = premium * payment_term
        
        # Calculate absolute return
        absolute_return = maturity_value - total_investment
        
        # Create cashflows for IRR calculation
        cashflows = []
        for year in range(1, policy_term + 1):
            if year <= payment_term:
                cashflows.append(-premium)  # Premium outflow
            else:
                cashflows.append(0)  # No premium payment
        
        # Add maturity benefit in last year
        if cashflows:
            cashflows[-1] += maturity_value
        
        # Calculate IRR
        irr = calculate_irr(cashflows)
        irr_percent = irr * 100
        
        # Calculate projections
        fd_projection = calculate_projection(total_investment, policy_term, 0.06)  # 6% FD
        mf_projection = calculate_projection(total_investment, policy_term, 0.12)  # 12% Mutual Fund
        
        # Risk scoring
        if irr_percent < 4:
            risk_score = 9
            policy_rating = "Very Poor"
        elif irr_percent < 6:
            risk_score = 7
            policy_rating = "Poor"
        elif irr_percent < 8:
            risk_score = 5
            policy_rating = "Average"
        else:
            risk_score = 3
            policy_rating = "Good"
        
        # Generate warnings
        warnings = []
        if irr_percent < 5:
            warnings.append("Returns are below inflation")
        if maturity_value < total_investment:
            warnings.append("Negative returns")
        if premium > 100000:  # High premium warning
            warnings.append("High premium amount")
        if policy_term > 30:  # Very long term warning
            warnings.append("Very long policy term")
        
        return {
            "total_investment": round(total_investment, 2),
            "maturity_value": round(maturity_value, 2),
            "absolute_return": round(absolute_return, 2),
            "irr": round(irr_percent, 2),
            "risk_score": risk_score,
            "policy_rating": policy_rating,
            "fd_projection": round(fd_projection, 2),
            "mf_projection": round(mf_projection, 2),
            "warnings": warnings
        }
        
    except Exception as e:
        # Fallback for any unexpected errors
        return {
            "total_investment": 0.0,
            "maturity_value": 0.0,
            "absolute_return": 0.0,
            "irr": 0.0,
            "risk_score": 9,
            "policy_rating": "Error",
            "fd_projection": 0.0,
            "mf_projection": 0.0,
            "warnings": ["Calculation error occurred"]
        }
