"""
AI-powered policy data extraction using Google Gemini.
Uses the modern google.genai SDK.
"""
import json
import re
import os

def ai_extract(text):
    """
    Extract policy financial data using Gemini AI.
    
    Args:
        text: Full extracted text from the insurance PDF
        
    Returns:
        dict with keys: premium, payment_term, policy_term, maturity_value
    """
    try:
        from google import genai
        
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            print("AI EXTRACT: No GEMINI_API_KEY set")
            return {}
        
        client = genai.Client(api_key=api_key)
        
        prompt = f"""You are an insurance policy data extraction expert.

Extract the following financial values from this insurance policy text.
Return ONLY a valid JSON object with these exact keys:

{{
    "premium": <annual premium amount as integer, or null if not found>,
    "payment_term": <premium paying term (PPT) in years as integer, or null if not found>,
    "policy_term": <total policy term / coverage duration in years as integer, or null if not found>,
    "maturity_value": <maturity benefit amount as integer, or null if not found>,
    "sum_assured": <sum assured / death benefit as integer, or null if not found>,
    "benefits": <array of strings, listing ALL key benefits and advantages explicitly mentioned in the policy (e.g., Death Benefit, Maturity Benefit), or [] if not found>
}}

CRITICAL RULES:
- Extract ONLY numbers, no text
- Premium should be the ANNUAL premium amount
- If you see a table with yearly values, the premium is the repeating annual payment
- Maturity value is the final benefit received at the end of the policy

IMPORTANT - payment_term vs policy_term:
- "payment_term" is the PREMIUM PAYING TERM (PPT) - how many years premiums are paid. Look for "Premium Paying Term", "PPT", "Premium Payment Term", "paying term", "number of installments"
- "policy_term" is the TOTAL POLICY TERM - how many years the policy runs/provides coverage. Look for "Policy Term", "Term of Policy", "Coverage Period"
- These are often DIFFERENT. For example: PPT might be 12 years while policy term is 24 years (limited-pay policy)
- If only one term is mentioned and it's labeled as "policy term", set payment_term to null (do NOT copy policy_term into payment_term)
- If not found, use null
- Return ONLY the JSON, no explanation

Policy Text:
{text[:8000]}
"""
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        
        response_text = response.text.strip()
        print("AI RAW RESPONSE:", response_text[:500])
        
        # Try to parse JSON directly
        try:
            result = json.loads(response_text)
            print("AI EXTRACT RESULT:", result)
            return result
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                print("AI EXTRACT RESULT (from code block):", result)
                return result
            
            # Try to find raw JSON object
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                print("AI EXTRACT RESULT (raw):", result)
                return result
        
        print("AI EXTRACT: Could not parse response")
        return {}
        
    except Exception as e:
        print("AI EXTRACT ERROR:", str(e))
        return {}
