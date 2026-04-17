def normalize_pdf_text(text):
    """
    ULTRA-STRICT text normalization layer for insurance PDF extraction.
    Converts messy PDF text into clean, structured, machine-readable format.
    """
    import re
    
    if not text or not isinstance(text, str):
        return ""
    
    print("=== TEXT NORMALIZATION START ===")
    print("ORIGINAL TEXT SAMPLE:", text[:500])
    
    # PART 1: BASIC CLEANING
    print("\n--- PART 1: BASIC CLEANING ---")
    
    # Convert to lowercase
    text = text.lower()
    print("Lowercase applied")
    
    # Replace multiple spaces with single space
    text = re.sub(r"\s+", " ", text)
    print("Multiple spaces normalized")
    
    # Remove tabs, newlines → normalize to single space
    text = re.sub(r"[\t\n\r]", " ", text)
    print("Tabs and newlines normalized")
    
    # PART 2: CURRENCY STANDARDIZATION (VERY IMPORTANT)
    print("\n--- PART 2: CURRENCY STANDARDIZATION ---")
    
    # Convert ALL currency formats to "rs"
    currency_patterns = [
        (r"₹", "rs"),
        (r"rs\.?", "rs"),
        (r"inr", "rs"),
        (r"rupees", "rs"),
        (r"rs/-", "rs")
    ]
    
    for pattern, replacement in currency_patterns:
        text = re.sub(pattern, replacement, text)
    
    print("Currency standardized to 'rs'")
    print("Currency example: '₹ 50,000' → 'rs 50000'")
    
    # PART 3: NUMBER NORMALIZATION
    print("\n--- PART 3: NUMBER NORMALIZATION ---")
    
    # Remove commas from numbers - apply repeatedly until clean
    original_commas = len(re.findall(r"(\d),(\d)", text))
    while re.search(r"(\d),(\d)", text):
        text = re.sub(r"(\d),(\d)", r"\1\2", text)
    
    print(f"Removed {original_commas} comma(s) from numbers")
    print("Number example: '50,000' → '50000'")
    
    # PART 4: FIX OCR SPLIT NUMBERS
    print("\n--- PART 4: FIX OCR SPLIT NUMBERS ---")
    
    # Fix broken numbers like "5 0 0 0 0" → "50000"
    # Run multiple passes if needed
    original_splits = len(re.findall(r"(\d)\s+(\d)", text))
    passes = 0
    max_passes = 5
    
    while re.search(r"(\d)\s+(\d)", text) and passes < max_passes:
        text = re.sub(r"(\d)\s+(\d)", r"\1\2", text)
        passes += 1
    
    print(f"Fixed OCR splits in {passes} passes")
    print("OCR example: '5 0 0 0 0' → '50000'")
    
    # PART 5: REMOVE NON-RELEVANT SYMBOLS
    print("\n--- PART 5: REMOVE NON-RELEVANT SYMBOLS ---")
    
    # Remove special characters except digits, alphabets, "rs"
    # Keep: a-z, 0-9, spaces, and the letters r,s (for "rs")
    original_symbols = len(re.findall(r"[^a-z0-9\srs]", text))
    text = re.sub(r"[^a-z0-9\srs]", " ", text)
    
    print(f"Removed {original_symbols} non-relevant symbols")
    print("Kept only: a-z, 0-9, spaces, and 'rs'")
    
    # PART 6: STANDARDIZE KEY PHRASES
    print("\n--- PART 6: STANDARDIZE KEY PHRASES ---")
    
    # Map variations → standard form
    phrase_mapping = {
        r"annual premium|yearly premium|premium per year|premium payable|premium amount": "annual_premium",
        r"maturity benefit|benefit at maturity|maturity value|guaranteed benefit|sum assured|death benefit": "maturity_value",
        r"policy term|term of policy|policy duration|policy period|term": "policy_term",
        r"premium payment term|ppt|premium paying term|payment term|paying term": "payment_term",
        r"sum assured|assured sum|insurance amount|coverage amount|sum insured": "sum_assured",
        r"surrender value|surrender amount": "surrender_value",
        r"death benefit|death cover": "death_benefit"
    }
    
    for pattern, replacement in phrase_mapping.items():
        matches = len(re.findall(pattern, text))
        if matches > 0:
            text = re.sub(pattern, replacement, text)
            print(f"Standardized '{pattern}' → '{replacement}' ({matches} matches)")
    
    # PART 7: REMOVE NOISE WORDS
    print("\n--- PART 7: REMOVE NOISE WORDS ---")
    
    # Remove useless words that don't contribute to extraction
    noise_words = [
        "page", "policy number", "customer id", "customer identification", "age", "years old",
        "date of birth", "dob", "name", "address", "mobile", "phone", "email", "nominee",
        "policyholder", "insured", "beneficiary", "document", "form", "application",
        "signature", "date", "time", "place", "city", "state", "pin", "postal", "code",
        "office", "branch", "agent", "advisor", "executive", "manager", "company",
        "limited", "ltd", "private", "public", "sector", "bank", "insurance", "life",
        "corporation", "corporate", "business", "commercial", "personal", "individual",
        "mr", "mrs", "ms", "dr", "prof", "sir", "madam", "title", "gender", "male",
        "female", "other", "married", "single", "divorced", "widowed", "education",
        "occupation", "profession", "income", "salary", "earnings", "employment",
        "self", "employed", "businessman", "service", "retired", "student", "housewife"
    ]
    
    # Create regex pattern for noise words
    noise_pattern = r'\b(?:' + '|'.join(noise_words) + r')\b'
    original_noise = len(re.findall(noise_pattern, text))
    text = re.sub(noise_pattern, " ", text)
    
    print(f"Removed {original_noise} noise words")
    
    # PART 8: NORMALIZE UNITS
    print("\n--- PART 8: NORMALIZE UNITS ---")
    
    # Convert various year formats to standard
    unit_patterns = [
        (r"(\d+)\s*(years|yrs|yr)", r"\1"),
        (r"(\d+)\s*(months|month|mnth)", r"\1"),  # Though months shouldn't appear in our context
        (r"(\d+)\s*(days|day)", r"\1"),  # Though days shouldn't appear in our context
    ]
    
    for pattern, replacement in unit_patterns:
        matches = len(re.findall(pattern, text))
        if matches > 0:
            text = re.sub(pattern, replacement, text)
            print(f"Normalized units: {pattern} → {replacement} ({matches} matches)")
    
    # PART 9: FINAL SANITY CHECK
    print("\n--- PART 9: FINAL SANITY CHECK ---")
    
    # Clean up any remaining multiple spaces
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    
    # Verify normalization quality
    checks = {
        "No commas": not bool(re.search(r"\d,\d", text)),
        "No ₹ symbol": "₹" not in text,
        "All numbers clean": not bool(re.search(r"\d\s+\d", text)),  # No space-separated digits
        "Keywords standardized": "annual_premium" in text or "maturity_value" in text,
        "No special symbols": not bool(re.search(r"[^a-z0-9\srs]", text))
    }
    
    print("SANITY CHECKS:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    
    # Final statistics
    final_length = len(text)
    word_count = len(text.split())
    
    print(f"\nNORMALIZATION COMPLETE:")
    print(f"  Final text length: {final_length} characters")
    print(f"  Final word count: {word_count} words")
    print(f"  Compression ratio: {(final_length / len(text) * 100):.1f}% of original")
    
    print("\n=== TEXT NORMALIZATION END ===")
    print("NORMALIZED TEXT SAMPLE:", text[:500])
    
    return text


def remove_noise(text):
    """Helper function to remove noise words."""
    import re
    
    # Additional noise words specific to insurance documents
    additional_noise = [
        "please", "thank", "you", "dear", "sir", "madam", "regards", "sincerely",
        "yours", "faithfully", "truly", "respectfully", "submitted", "received",
        "approved", "rejected", "pending", "processing", "processed", "completed",
        "cancelled", "terminated", "suspended", "active", "inactive", "valid",
        "invalid", "expired", "renewed", "renewal", "lapsed", "surrendered",
        "claimed", "settled", "paid", "unpaid", "due", "overdue", "outstanding",
        "balance", "amount", "total", "subtotal", "tax", "gst", "service", "charge",
        "fee", "cost", "price", "rate", "percentage", "percent", "interest", "discount",
        "bonus", "reward", "cash", "money", "payment", "installment", "emi", "loan",
        "credit", "debit", "account", "number", "reference", "id", "identification",
        "proof", "document", "certificate", "statement", "report", "record", "file",
        "paper", "copy", "original", "duplicate", "xerox", "print", "signature",
        "stamp", "seal", "mark", "initial", "sign", "witness", "attested", "verified",
        "authenticated", "authorized", "approved", "signed", "dated", "effective",
        "from", "to", "valid", "period", "duration", "term", "condition", "terms",
        "conditions", "clause", "section", "article", "paragraph", "point", "item",
        "detail", "particulars", "information", "data", "fact", "figure", "statistic",
        "calculation", "computation", "analysis", "assessment", "evaluation", "review",
        "examination", "inspection", "audit", "check", "verify", "confirm", "acknowledge",
        "accept", "agree", "disagree", "object", "protest", "complaint", "grievance",
        "dispute", "resolution", "settlement", "compromise", "agreement", "contract",
        "policy", "plan", "scheme", "program", "offer", "proposal", "suggestion",
        "recommendation", "advice", "guidance", "instruction", "direction", "order",
        "request", "application", "form", "format", "template", "sample", "example",
        "specimen", "model", "type", "kind", "variety", "category", "class", "group",
        "section", "division", "department", "unit", "branch", "office", "headquarters",
        "location", "address", "contact", "communication", "correspondence", "letter",
        "email", "fax", "telephone", "mobile", "phone", "call", "message", "notification",
        "alert", "reminder", "notice", "announcement", "declaration", "statement",
        "proclamation", "circular", "bulletin", "newsletter", "magazine", "journal",
        "publication", "book", "manual", "handbook", "guide", "handout", "brochure",
        "pamphlet", "leaflet", "flyer", "poster", "banner", "advertisement", "promo"
    ]
    
    # Combine main noise words with additional ones
    main_noise = [
        "page", "policy number", "customer id", "age", "years old",
        "date of birth", "dob", "name", "address", "mobile", "phone", "email", "nominee"
    ]
    
    all_noise = main_noise + additional_noise
    
    # Create regex pattern for all noise words
    noise_pattern = r'\b(?:' + '|'.join(all_noise) + r')\b'
    text = re.sub(noise_pattern, " ", text)
    
    # Clean up extra spaces
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    
    return text
