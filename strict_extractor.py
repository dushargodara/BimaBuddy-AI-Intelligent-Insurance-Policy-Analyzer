def extract_policy_data(file):
    """
    ULTRA-STRICT insurance policy extraction engine.
    Extracts ONLY HIGH-CONFIDENCE financial values.
    Rejects weak, ambiguous, or incorrect data completely.
    """
    import pdfplumber
    import re
    import json
    
    def extract_full_text(file):
        """Extract full text from PDF."""
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
        
        return text
    
    # MAIN EXTRACTION PIPELINE
    print("=== ULTRA-STRICT EXTRACTION START ===")
    
    # Step 1: Extract raw text from PDF
    raw_text = extract_full_text(file)
    if not raw_text:
        return {"error": "No text extracted from PDF"}
    
    # Step 2: Apply ULTRA-STRICT text normalization
    from services.text_normalizer import normalize_pdf_text
    normalized_text = normalize_pdf_text(raw_text)
    
    if not normalized_text:
        return {"error": "Text normalization failed"}
    
    print("=== USING NORMALIZED TEXT FOR EXTRACTION ===")
    
    def strict_context_match(text):
        """Strict context matching with mandatory keywords."""
        
        # STRICT KEYWORD REQUIREMENTS (now using standardized phrases)
        premium_keywords = ["annual_premium"]
        maturity_keywords = ["maturity_value"]
        term_keywords = ["policy_term"]
        ppt_keywords = ["payment_term"]
        
        def extract_with_strict_rules(keywords, min_digits=4):
            """Extract values with strict context matching."""
            candidates = []
            
            for keyword in keywords:
                # STRICT REGEX: keyword + max 40 chars + at least 4 digits
                pattern = rf"({keyword})[^\d]{{0,40}}(\d{{{min_digits},}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    keyword_found, value_str = match
                    value = int(value_str)
                    
                    candidates.append({
                        'value': value,
                        'keyword': keyword_found,
                        'context': text[text.find(keyword_found)-50:text.find(keyword_found)+len(keyword_found)+50]
                    })
            
            return candidates
        
        # Extract candidates for each field
        premium_candidates = extract_with_strict_rules(premium_keywords)
        maturity_candidates = extract_with_strict_rules(maturity_keywords)
        term_candidates = extract_with_strict_rules(term_keywords, min_digits=1)  # Years can be 1-2 digits
        ppt_candidates = extract_with_strict_rules(ppt_keywords, min_digits=1)
        
        print("PREMIUM CANDIDATES:", premium_candidates)
        print("MATURITY CANDIDATES:", maturity_candidates)
        print("TERM CANDIDATES:", term_candidates)
        print("PPT CANDIDATES:", ppt_candidates)
        
        return {
            'premium': premium_candidates,
            'maturity': maturity_candidates,
            'term': term_candidates,
            'ppt': ppt_candidates
        }
    
    def score_candidates(candidates, field_type):
        """Multi-candidate scoring system."""
        if not candidates:
            return None
        
        scored_candidates = []
        
        for candidate in candidates:
            score = 0
            value = candidate['value']
            context = candidate['context']
            
            # +50 → exact keyword match (already guaranteed by strict matching)
            score += 50
            
            # +30 → nearby "rs"
            if 'rs' in context:
                score += 30
            
            # +20 → larger value (for premium/maturity)
            if field_type in ['premium', 'maturity'] and value > 10000:
                score += 20
            
            # -50 → value < 1000
            if value < 1000:
                score -= 50
            
            # -30 → appears near words like "age", "year", "page"
            negative_words = ['age', 'year', 'page', 'date', 'birth']
            if any(word in context for word in negative_words):
                score -= 30
            
            scored_candidates.append({
                'value': value,
                'score': score,
                'context': context
            })
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"SCORED {field_type.upper()} CANDIDATES:", scored_candidates)
        
        # Return only the highest scoring candidate
        return scored_candidates[0] if scored_candidates else None
    
    def hard_filtering(data):
        """Hard filtering rules with strict rejection."""
        premium = data.get('premium')
        maturity = data.get('maturity')
        term = data.get('term')
        ppt = data.get('ppt')
        
        filtered_data = {}
        rejections = []
        
        # Premium filtering
        if premium and premium['value'] >= 1000:
            filtered_data['premium'] = premium['value']
        else:
            filtered_data['premium'] = None
            if premium:
                rejections.append(f"Premium {premium['value']} < 1000")
        
        # Maturity filtering
        if maturity and maturity['value'] >= 1000:
            filtered_data['maturity'] = maturity['value']
        else:
            filtered_data['maturity'] = None
            if maturity:
                rejections.append(f"Maturity {maturity['value']} < 1000")
        
        # Term filtering
        if term and term['value'] <= 100:
            filtered_data['term'] = term['value']
        else:
            filtered_data['term'] = None
            if term:
                rejections.append(f"Term {term['value']} > 100")
        
        # PPT filtering
        if ppt and ppt['value'] <= 100:
            filtered_data['ppt'] = ppt['value']
        else:
            filtered_data['ppt'] = None
            if ppt:
                rejections.append(f"PPT {ppt['value']} > 100")
        
        # Cross-validation rules
        if filtered_data.get('premium') and filtered_data.get('maturity'):
            if filtered_data['maturity'] < filtered_data['premium']:
                filtered_data['maturity'] = None
                rejections.append("Maturity < Premium")
        
        if filtered_data.get('ppt') and filtered_data.get('term'):
            if filtered_data['ppt'] > filtered_data['term']:
                filtered_data['ppt'] = None
                rejections.append("PPT > Term")
        
        print("HARD FILTERING REJECTIONS:", rejections)
        return filtered_data
    
    def ai_validator(data):
        """AI as validator, not primary extractor."""
        try:
            import google.generativeai as genai
            from core.config import GEMINI_API_KEY
            
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            # Prepare validation prompt
            prompt = f"""
            Validate these extracted values from insurance policy:
            
            premium = {data.get('premium', 'Not found')}
            maturity = {data.get('maturity', 'Not found')}
            term = {data.get('term', 'Not found')}
            ppt = {data.get('ppt', 'Not found')}
            
            Correct them if wrong. Return JSON only:
            {{
                "premium": number or null,
                "maturity": number or null,
                "term": number or null,
                "ppt": number or null
            }}
            """
            
            response = model.generate_content(prompt)
            
            try:
                ai_result = json.loads(response.text)
                print("AI VALIDATION RESULT:", ai_result)
                return ai_result
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    ai_result = json.loads(json_match.group())
                    print("AI VALIDATION RESULT (extracted):", ai_result)
                    return ai_result
                return {}
                
        except Exception as e:
            print("AI validation error:", e)
            return {}
    
    def calculate_confidence(data):
        """Calculate confidence score."""
        confidence = 0
        
        if data.get('premium'):
            confidence += 30
        if data.get('maturity'):
            confidence += 30
        if data.get('term'):
            confidence += 20
        if data.get('ppt'):
            confidence += 20
        
        return confidence
    
    # Step 3: Strict context matching on normalized text
    candidates = strict_context_match(normalized_text)
    
    # Step 4: Score candidates
    scored_data = {
        'premium': score_candidates(candidates['premium'], 'premium'),
        'maturity': score_candidates(candidates['maturity'], 'maturity'),
        'term': score_candidates(candidates['term'], 'term'),
        'ppt': score_candidates(candidates['ppt'], 'ppt')
    }
    
    print("SCORED DATA:", scored_data)
    
    # Step 5: Hard filtering
    filtered_data = hard_filtering(scored_data)
    print("FILTERED DATA:", filtered_data)
    
    # Step 6: AI validation
    ai_validated = ai_validator(filtered_data)
    
    # Merge AI validation (use AI values if they disagree)
    final_data = {}
    for key in ['premium', 'maturity', 'term', 'ppt']:
        if ai_validated.get(key) is not None:
            final_data[key] = ai_validated[key]
        else:
            final_data[key] = filtered_data.get(key)
    
    print("FINAL DATA:", final_data)
    
    # Step 7: Calculate confidence
    confidence = calculate_confidence(final_data)
    print("CONFIDENCE SCORE:", confidence)
    
    # Step 8: Return based on confidence
    if confidence < 60:
        return {
            "error": "Low confidence extraction",
            "data": final_data,
            "confidence": confidence
        }
    
    # Map to expected output format
    result = {
        "premium": final_data.get('premium'),
        "payment_term": final_data.get('ppt'),
        "policy_term": final_data.get('term'),
        "maturity_value": final_data.get('maturity'),
        "confidence": confidence
    }
    
    print("FINAL EXTRACTED DATA:", result)
    print("=== ULTRA-STRICT EXTRACTION END ===")
    return result
