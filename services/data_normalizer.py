def normalize_policy_data(raw_data):
    """
    Production-ready data normalizer for extracted PDF data.
    Converts messy extracted data into clean, structured, numeric format.
    Handles Indian number formats like "15 lakh", "2 crore", "50k".
    """
    import re
    
    def parse_amount(value):
        """
        Convert strings into float, handling Indian number formats.
        Handles: lakh → ×100000, crore → ×10000000, k → ×1000, million → ×1000000
        """
        if value is None:
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            return 0.0
        
        # Clean the text
        cleaned = value.strip().lower()
        
        # Remove currency symbols and common prefixes
        prefixes_to_remove = ['rs.', 'rs', '₹', 'inr', 'rs/-', 'rs.']
        for prefix in prefixes_to_remove:
            cleaned = cleaned.replace(prefix, '')
        
        # Remove common suffixes
        suffixes_to_remove = ['per year', '/year', 'p.a.', 'annually', 'per annum']
        for suffix in suffixes_to_remove:
            cleaned = cleaned.replace(suffix, '')
        
        # Remove approximation words
        cleaned = re.sub(r'\b(approx|approximately|about|around)\b\.?', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        
        # Handle Indian number formats
        multiplier = 1.0
        
        # Check for crore
        crore_match = re.search(r'(\d+\.?\d*)\s*crore', cleaned)
        if crore_match:
            number = float(crore_match.group(1).replace(',', ''))
            return number * 10000000  # 1 crore = 1,00,00,000
        
        # Check for lakh
        lakh_match = re.search(r'(\d+\.?\d*)\s*lakh', cleaned)
        if lakh_match:
            number = float(lakh_match.group(1).replace(',', ''))
            return number * 100000  # 1 lakh = 1,00,000
        
        # Check for thousands (k)
        k_match = re.search(r'(\d+\.?\d*)\s*k', cleaned)
        if k_match:
            number = float(k_match.group(1).replace(',', ''))
            return number * 1000
        
        # Check for million
        million_match = re.search(r'(\d+\.?\d*)\s*million', cleaned)
        if million_match:
            number = float(million_match.group(1).replace(',', ''))
            return number * 1000000
        
        # Extract regular number with commas
        number_match = re.search(r'[\d,]+(?:\.\d+)?', cleaned)
        if not number_match:
            return 0.0
        
        # Remove commas and convert to float
        number_str = number_match.group().replace(',', '')
        
        try:
            return float(number_str) * multiplier
        except ValueError:
            return 0.0
    
    def parse_years(value):
        """
        Extract numeric years from strings like "20 years".
        Returns int, 0 if not found.
        """
        if value is None:
            return 0
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, float):
            return int(value)
        
        if not isinstance(value, str):
            return 0
        
        cleaned = value.strip().lower()
        
        # Extract years using various patterns
        patterns = [
            r'(\d+)\s*years?',
            r'term\s*[:\-]?\s*(\d+)',
            r'policy\s+term\s*[:\-]?\s*(\d+)',
            r'policy\s+for\s*(\d+)\s*years?',
            r'duration\s*[:\-]?\s*(\d+)',
            r'(\d+)\s*yrs?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return 0
    
    try:
        # Extract and clean each field using enhanced parsing
        premium = parse_amount(raw_data.get("premium"))
        policy_term = parse_years(raw_data.get("policy_term"))
        payment_term = parse_years(raw_data.get("payment_term"))
        sum_assured = parse_amount(raw_data.get("sum_assured"))
        maturity_benefit = parse_amount(raw_data.get("maturity_benefit"))
        
        # Smart defaults
        if payment_term == 0 and policy_term > 0:
            payment_term = policy_term
        
        # Validate ranges and apply reasonable limits
        if premium < 0:
            premium = 0.0
        elif premium > 10000000:  # Cap at 1 crore for safety
            premium = 10000000.0
        
        if policy_term < 0:
            policy_term = 0
        elif policy_term > 100:  # Cap at 100 years
            policy_term = 100
        
        if payment_term < 0:
            payment_term = 0
        elif payment_term > policy_term:  # Payment term can't exceed policy term
            payment_term = policy_term
        
        if sum_assured < 0:
            sum_assured = 0.0
        elif sum_assured > 100000000:  # Cap at 10 crore
            sum_assured = 100000000.0
        
        if maturity_benefit < 0:
            maturity_benefit = 0.0
        elif maturity_benefit > 100000000:  # Cap at 10 crore
            maturity_benefit = 100000000.0
        
        return {
            "premium": round(premium, 2),
            "policy_term": int(policy_term),
            "payment_term": int(payment_term),
            "sum_assured": round(sum_assured, 2),
            "maturity_benefit": round(maturity_benefit, 2)
        }
        
    except Exception as e:
        # Fallback for any unexpected errors
        return {
            "premium": 0.0,
            "policy_term": 0,
            "payment_term": 0,
            "sum_assured": 0.0,
            "maturity_benefit": 0.0
        }
