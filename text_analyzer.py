import os
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class PolicyInsights(BaseModel):
    policy_summary: str = Field(description="A concise 3-5 line simple summary of the policy.")
    key_benefits: list[str] = Field(description="List of key benefits in simple, user-friendly bullet points (under 20 words each).")
    exclusions: list[str] = Field(description="List of exclusions in simple, user-friendly bullet points (under 20 words each).")
    hidden_clauses: list[str] = Field(description="List of hidden clauses or catch elements into simple, user-friendly bullet points (under 20 words each).")

def analyze_policy_text(text: str) -> dict:
    """
    AI-based policy text analysis using Gemini Structured Outputs.
    
    Args:
        text (string): full extracted PDF text
    
    Returns:
        dict: {
            "policy_summary": string,
            "key_benefits": list[str],
            "exclusions": list[str],
            "hidden_clauses": list[str]
        }
    """
    result = {
        "policy_summary": "Policy details extracted.",
        "key_benefits": ["No specific benefits extracted."],
        "exclusions": ["No explicit exclusions identified."],
        "hidden_clauses": ["No hidden clauses identified."]
    }
    
    try:
        if not text or not isinstance(text, str) or len(text.strip()) < 50:
            return result
            
        print("TEXT ANALYSIS START - Text length:", len(text))
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY is not set.")
            return result
            
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Analyze the following insurance policy text. Extract the policy summary, key benefits, exclusions, and hidden clauses.
        
        IMPORTANT RULES:
        1. Ignore all template variables like {{{{NOMINEE_NAME_1}}}} or {{{{TEXT}}}} tags.
        2. Ignore broken sentences or administrative artifact text.
        3. Rewrite the actual policy features into simple, user-friendly bullet points (under 20 words each).
        
        Policy Text:
        ---
        {text[:35000]}
        ---
        """
        
        # Attempt 1: structured schema output
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PolicyInsights,
                ),
            )
            data = json.loads(response.text)
        except Exception as schema_err:
            print("Structured schema failed, trying plain JSON fallback:", schema_err)
            # Attempt 2: plain JSON prompt (no schema) — works for all models
            fallback_prompt = f"""Analyze this insurance policy and return ONLY a valid JSON object with exactly these keys:
{{
  "policy_summary": "3-5 sentence plain-English summary of the policy",
  "key_benefits": ["benefit 1", "benefit 2", "..."],
  "exclusions": ["exclusion 1", "exclusion 2", "..."],
  "hidden_clauses": ["clause 1", "clause 2", "..."]
}}

Rules:
- Keep each point under 20 words
- Ignore template variables like {{NOMINEE_NAME}} or {{TEXT}}
- Return ONLY the JSON, no extra text

Policy Text:
---
{text[:20000]}
---"""
            response2 = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=fallback_prompt,
            )
            raw = response2.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw.strip())

        result["policy_summary"] = data.get("policy_summary") or result["policy_summary"]
        result["key_benefits"]   = data.get("key_benefits")   or result["key_benefits"]
        result["exclusions"]     = data.get("exclusions")     or result["exclusions"]
        result["hidden_clauses"] = data.get("hidden_clauses") or result["hidden_clauses"]

        print("TEXT ANALYSIS OK - Benefits:", len(result["key_benefits"]),
              "Exclusions:", len(result["exclusions"]),
              "Clauses:", len(result["hidden_clauses"]))

    except Exception as e:
        print("TEXT ANALYSIS FAILED (both attempts):", e)
        # Keep the safe default result set at the top of the function
    
    return result

def extract_policy_insights(text):
    """
    Alternative function name for backward compatibility.
    """
    return analyze_policy_text(text)

if __name__ == "__main__":
    # Test function for development
    sample_text = "This policy pays Rs 10000 to {{NOMINEE_NAME}}. Suicide is not covered."
    res = analyze_policy_text(sample_text)
    print(res)

