def extract_policy_data(text):
    """
    Extract structured insurance data from PDF text using pattern matching and heuristics.
    Returns raw string values for further normalization.
    """
    import re
    
    def extract_by_patterns(text, patterns):
        """Extract value using multiple regex patterns."""
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                return matches[0].strip()
        return ""
    
    def extract_currency_value(text, keywords):
        """Extract currency value near specific keywords."""
        for keyword in keywords:
            # Look for currency values near the keyword
            patterns = [
                rf'{keyword}.*?([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
                rf'([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+?)).*?{keyword}',
                rf'{keyword}[\s]*[:\-]?\s*([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
                rf'([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+?))',
            ]
            value = extract_by_patterns(text, patterns)
            if value:
                return value
        return ""
    
    def extract_year_value(text, keywords):
        """Extract year value near specific keywords."""
        for keyword in keywords:
            patterns = [
                rf'{keyword}.*?(\d+)\s*years?',
                rf'(\d+)\s*years?.*?{keyword}',
                rf'{keyword}[\s]*[:\-]?\s*(\d+)',
                rf'term\s*[:\-]?\s*(\d+)',
                rf'policy\s+term\s*[:\-]?\s*(\d+)',
            ]
            value = extract_by_patterns(text, patterns)
            if value:
                return value
        return ""
    
    try:
        if not text or not isinstance(text, str):
            return {
                "premium": "",
                "policy_term": "",
                "payment_term": "",
                "sum_assured": "",
                "maturity_benefit": ""
            }
        
        # Convert text to lowercase for pattern matching but preserve original for extraction
        text_lower = text.lower()
        
        # Extract premium
        premium_keywords = [
            "premium", "annual premium", "yearly premium", "premium amount",
            "annual amount", "yearly amount", "premium per year"
        ]
        premium = extract_currency_value(text, premium_keywords)
        
        # Extract policy term
        policy_term_keywords = [
            "policy term", "term", "policy duration", "policy period",
            "term of policy", "policy for", "policy years"
        ]
        policy_term = extract_year_value(text, policy_term_keywords)
        
        # Extract payment term
        payment_term_keywords = [
            "payment term", "premium payment term", "premium paying term",
            "paying term", "payment years", "premium for"
        ]
        payment_term = extract_year_value(text, payment_term_keywords)
        
        # Extract sum assured
        sum_assured_keywords = [
            "sum assured", "sum assured amount", "assured sum",
            "insurance amount", "coverage amount", "sum insured"
        ]
        sum_assured = extract_currency_value(text, sum_assured_keywords)
        
        # Extract maturity benefit
        maturity_keywords = [
            "maturity benefit", "maturity value", "maturity amount",
            "maturity", "surrender value", "death benefit",
            "maturity proceeds", "policy proceeds"
        ]
        maturity_benefit = extract_currency_value(text, maturity_keywords)
        
        # Fallback: Look for any currency values in order of likelihood
        if not premium:
            # Try to find the first annual premium pattern
            annual_patterns = [
                r'annual.*?([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
                r'yearly.*?([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
                r'([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+?)).*?annual',
                r'([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+?)).*?yearly',
            ]
            premium = extract_by_patterns(text, annual_patterns)
        
        if not sum_assured:
            # Try to find large sum values
            sum_patterns = [
                r'sum.*?([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
                r'assured.*?([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
                r'coverage.*?([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
            ]
            sum_assured = extract_by_patterns(text, sum_patterns)
        
        if not maturity_benefit:
            # Try to find maturity/guaranteed values
            maturity_patterns = [
                r'maturity.*?([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
                r'guaranteed.*?([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
                r'surrender.*?([₹rsrs\.]?[\s]*[\d,]+(?:\.\d+)?)',
            ]
            maturity_benefit = extract_by_patterns(text, maturity_patterns)
        
        return {
            "premium": premium,
            "policy_term": policy_term,
            "payment_term": payment_term,
            "sum_assured": sum_assured,
            "maturity_benefit": maturity_benefit
        }
        
    except Exception as e:
        # Fallback for any unexpected errors
        return {
            "premium": "",
            "policy_term": "",
            "payment_term": "",
            "sum_assured": "",
            "maturity_benefit": ""
        }
