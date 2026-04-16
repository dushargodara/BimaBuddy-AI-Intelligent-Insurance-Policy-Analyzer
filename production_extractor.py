def extract_policy_data(file):
    """
    Production-level extraction engine for insurance policy PDFs.
    Hybrid AI + regex + validation system for maximum accuracy.
    """
    import pdfplumber
    import re
    import json
    
    def extract_full_text(file):
        """Extract full text from PDF using pdfplumber."""
        text = ""
        
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print("PDF extraction error:", e)
            return ""
        
        return text.lower()
    
    def extract_with_context(text):
        """Context-aware regex extraction with smart filtering."""
        
        premium_patterns = [
            r"(annual premium|yearly premium|premium payable|premium amount)[^\d]*(\d[\d,]+)",
            r"premium[^\d]{0,20}(\d[\d,]+)",
            r"(premium)[^\d]*(\d[\d,]+)",
            r"(annual amount)[^\d]*(\d[\d,]+)",
            r"(yearly amount)[^\d]*(\d[\d,]+)"
        ]
        
        maturity_patterns = [
            r"(maturity benefit|sum assured|guaranteed benefit|death benefit|surrender value)[^\d]*(\d[\d,]+)",
            r"(benefit amount)[^\d]*(\d[\d,]+)",
            r"(maturity value)[^\d]*(\d[\d,]+)",
            r"(sum assured amount)[^\d]*(\d[\d,]+)",
            r"(guaranteed amount)[^\d]*(\d[\d,]+)"
        ]
        
        term_patterns = [
            r"(policy term|policy duration|policy period)[^\d]*(\d+)",
            r"(term)[^\d]*(\d+)",
            r"(policy for)[^\d]*(\d+)\s*years?",
            r"(duration)[^\d]*(\d+)"
        ]
        
        ppt_patterns = [
            r"(premium payment term|ppt|premium paying term|payment term)[^\d]*(\d+)",
            r"(paying term)[^\d]*(\d+)",
            r"(premium for)[^\d]*(\d+)\s*years?"
        ]
        
        def find_best(patterns, min_value=1000):
            """Find best values from patterns with filtering."""
            values = []
            for p in patterns:
                matches = re.findall(p, text, re.IGNORECASE)
                for m in matches:
                    # Handle tuple matches from groups
                    val_str = m[-1] if isinstance(m, tuple) else m
                    val_str = re.sub(r"[^\d]", "", val_str)
                    
                    if val_str:
                        try:
                            val = int(val_str)
                            # Filter unrealistic small values
                            if val >= min_value:
                                values.append(val)
                        except ValueError:
                            continue
            return values
        
        premium_vals = find_best(premium_patterns, 1000)
        maturity_vals = find_best(maturity_patterns, 10000)  # Higher threshold for maturity
        term_vals = find_best(term_patterns, 1)  # Lower threshold for years
        ppt_vals = find_best(ppt_patterns, 1)
        
        return {
            "premium": min(premium_vals) if premium_vals else None,
            "maturity_value": max(maturity_vals) if maturity_vals else None,
            "policy_term": max(term_vals) if term_vals else None,
            "payment_term": max(ppt_vals) if ppt_vals else None
        }
    
    def ai_extract(text):
        """AI fallback extraction for missing data."""
        try:
            # Import AI model (assuming it's available)
            import google.generativeai as genai
            from core.config import GEMINI_API_KEY
            
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            Extract the following from this insurance policy text:

            - Annual Premium
            - Policy Term (years)
            - Premium Payment Term
            - Maturity Value

            Return ONLY JSON:
            {{
                "premium": number,
                "policy_term": number,
                "payment_term": number,
                "maturity_value": number
            }}

            Text:
            {text[:4000]}
            """
            
            response = model.generate_content(prompt)
            
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return {}
                
        except Exception as e:
            print("AI extraction error:", e)
            return {}
    
    def merge_data(regex_data, ai_data):
        """Hybrid merge logic with smart fallback."""
        final = {}
        
        for key in ["premium", "policy_term", "payment_term", "maturity_value"]:
            val = regex_data.get(key)
            
            # Fallback to AI if regex fails
            if not val and ai_data:
                val = ai_data.get(key)
            
            final[key] = val
        
        return final
    
    def validate(data):
        """Intelligent validation with business logic."""
        premium = data.get("premium")
        maturity = data.get("maturity_value")
        ppt = data.get("payment_term")
        term = data.get("policy_term")
        
        # Fix missing payment term
        if not ppt and term:
            data["payment_term"] = term
        
        # Remove unrealistic values
        if premium and premium < 1000:
            data["premium"] = None
        
        if premium and premium > 10000000:  # More than 1 crore per year
            data["premium"] = None
        
        if maturity and maturity < premium:
            data["maturity_value"] = None
        
        if term and (term < 5 or term > 50):  # Unrealistic policy terms
            data["policy_term"] = None
        
        if ppt and (ppt < 1 or ppt > term if term else ppt > 30):  # Unrealistic PPT
            data["payment_term"] = None
        
        return data
    
    # MAIN PIPELINE
    text = extract_full_text(file)
    
    if not text:
        print("No text extracted from PDF")
        return {}
    
    print("TEXT SAMPLE:", text[:500])
    
    regex_data = extract_with_context(text)
    print("REGEX DATA:", regex_data)
    
    ai_data = ai_extract(text)
    print("AI DATA:", ai_data)
    
    merged = merge_data(regex_data, ai_data)
    print("MERGED DATA:", merged)
    
    validated = validate(merged)
    print("FINAL DATA:", validated)
    
    return validated
