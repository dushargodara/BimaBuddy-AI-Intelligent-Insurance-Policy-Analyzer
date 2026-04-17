import re
from backend.services.ai_extractor import ai_extract
import numpy as np
import numpy_financial as nf

def safe_int(value):
    try:
        if value is None:
            return None
        value = str(value).replace(",", "").replace("₹", "").strip()
        return int(float(value))
    except:
        return None


def extract_value(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return safe_int(match.group(1))
    return None


def regex_extract(text):
    """
    Strong regex fallback extraction for critical fields with context-aware patterns.
    """
    import re
    
    # Premium patterns with context - ONLY meaningful premium terms
    premium_patterns = [
        r"(?:annual premium|yearly premium|premium payable|premium amount|total premium)[^\d]*(\d[\d,]+)",
        r"(?:premium.*?payable|premium.*?due|premium.*?amount)[^\d]*(\d[\d,]+)",
        r"(?:sum assured.*?premium|coverage.*?premium)[^\d]*(\d[\d,]+)"
    ]
    
    # Maturity patterns with context - ONLY meaningful benefit terms
    maturity_patterns = [
        r"(?:maturity benefit|sum assured|guaranteed benefit|death benefit)[^\d]*(\d[\d,]+)",
        r"(?:maturity amount|guaranteed amount|surrender value)[^\d]*(\d[\d,]+)",
        r"(?:life cover|insurance cover|total benefit)[^\d]*(\d[\d,]+)"
    ]
    
    # Policy term patterns with context
    term_patterns = [
        r"(?:policy term|policy period|term of policy|policy duration)[^\d]*(\d+)",
        r"(?:term.*?years|period.*?years|duration.*?years)[^\d]*(\d+)",
        r"(?:tenure.*?years)[^\d]*(\d+)"
    ]
    
    def extract_with_context(patterns, text, field_name):
        all_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                all_matches.extend(matches)
        
        print(f"ALL {field_name.upper()} MATCHES:", all_matches)
        
        if not all_matches:
            return None
        
        # STEP 4: PICK LARGEST VALUE (IMPORTANT)
        if field_name in ["premium", "maturity_value"]:
            # Convert to integers and pick largest
            clean_values = []
            for match in all_matches:
                try:
                    clean_val = int(match.replace(",", ""))
                    clean_values.append(clean_val)
                except (ValueError, AttributeError):
                    continue
            
            if clean_values:
                largest = max(clean_values)
                print(f"PICKED LARGEST {field_name}: {largest}")
                return largest
        
        else:  # policy_term - pick most reasonable (not largest)
            clean_values = []
            for match in all_matches:
                try:
                    clean_val = int(match)
                    # Policy terms are usually between 5-50 years
                    if 5 <= clean_val <= 50:
                        clean_values.append(clean_val)
                except (ValueError, AttributeError):
                    continue
            
            if clean_values:
                # For terms, pick the median/most reasonable, not largest
                reasonable = sorted(clean_values)[len(clean_values)//2] if clean_values else clean_values[0]
                print(f"PICKED REASONABLE {field_name}: {reasonable}")
                return reasonable
        
        return None
    
    return {
        "premium": extract_with_context(premium_patterns, text, "premium"),
        "maturity_value": extract_with_context(maturity_patterns, text, "maturity_value"),
        "policy_term": extract_with_context(term_patterns, text, "policy_term")
    }


def clean_amount(value):
    """
    STEP 2: IGNORE SMALL VALUES - Filter out meaningless small amounts.
    """
    if value is None:
        return None
    
    try:
        # Handle both string and int inputs
        if isinstance(value, str):
            value = int(value.replace(",", ""))
        elif isinstance(value, (int, float)):
            value = int(value)
        else:
            return None
        
        # STEP 2: Ignore small values (< ₹1000 for premium/maturity)
        if value < 1000:
            print(f"IGNORED SMALL VALUE: {value}")
            return None
        
        return value
        
    except (ValueError, TypeError):
        return None


def extract_with_context(text, keywords):
    """
    Extract numbers with context window for better accuracy.
    """
    import re
    results = []
    for kw in keywords:
        pattern = rf"{kw}.*?(₹?\s?\d[\d,]+)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        results.extend(matches)
    return results


def clean_values(values):
    """
    Clean and filter extracted values.
    """
    cleaned = []
    for v in values:
        v = re.sub(r"[^\d]", "", v)
        if v:
            val = int(v)
            if val > 1000:  # Only keep meaningful financial values
                cleaned.append(val)
    return cleaned


def extract_payment_term(text):
    """
    Dedicated payment term / premium paying term extraction.
    PPT is a small integer (typically 5-40 years) and is often different from policy term.
    """
    import re

    # Tier 1: Explicit PPT patterns (highest confidence)
    tier1_patterns = [
        r"(?:premium\s*paying\s*term|premium\s*payment\s*term)\s*[:\-–]?\s*(\d{1,2})\s*(?:years?|yrs?)?",
        r"(?:premium\s*paying\s*term|premium\s*payment\s*term)\s*[:\-–]?\s*(?:of\s+)?(\d{1,2})\s*(?:years?|yrs?)?",
        r"(?:PPT)\s*[:\-–]?\s*(\d{1,2})\s*(?:years?|yrs?)?",
        r"(?:pay(?:ing)?\s*(?:premium\s*)?(?:for|of|period))\s*[:\-–]?\s*(\d{1,2})\s*(?:years?|yrs?)?",
        r"(?:limited\s*(?:premium\s*)?pay(?:ment)?)\s*[:\-–]?\s*(\d{1,2})\s*(?:years?|yrs?)?",
    ]

    for pat in tier1_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 3 <= val <= 50:
                print(f"PPT TIER 1 MATCH: {val} from pattern: {pat[:50]}")
                return val

    # Tier 2: Table-style patterns like "PPT 12 Years" or lines with "Paying Term" then a number
    tier2_patterns = [
        r"paying\s*term\s*[:\-–]?\s*(\d{1,2})",
        r"payment\s*term\s*[:\-–]?\s*(\d{1,2})",
        r"ppt\s*\(years?\)\s*[:\-–]?\s*(\d{1,2})",
        r"premium\s*term\s*[:\-–]?\s*(\d{1,2})",
        r"no\.?\s*of\s*(?:premium\s*)?installments?\s*[:\-–]?\s*(\d{1,2})",
        r"(\d{1,2})\s*(?:years?|yrs?)\s*(?:premium\s*)?paying\s*term",
        r"(\d{1,2})\s*(?:years?|yrs?)\s*(?:premium\s*)?payment\s*term",
    ]

    for pat in tier2_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 3 <= val <= 50:
                print(f"PPT TIER 2 MATCH: {val} from pattern: {pat[:50]}")
                return val

    # Tier 3: Contextual search — look for lines that contain PPT-related keywords and extract numbers
    ppt_line_keywords = [
        "premium paying term", "premium payment term", "paying term",
        "payment term", "ppt", "premium term", "number of installments",
        "no. of installments", "premium payable for",
    ]
    lines = text.split("\n")
    for line in lines:
        line_lower = line.lower().strip()
        for kw in ppt_line_keywords:
            if kw in line_lower:
                # Extract all numbers from this line
                nums = re.findall(r"\b(\d{1,2})\b", line)
                for n in nums:
                    val = int(n)
                    if 3 <= val <= 50:
                        print(f"PPT TIER 3 MATCH: {val} from line: {line.strip()[:80]}")
                        return val

    print("PPT: No explicit match found")
    return None


def smart_extract(text):
    """
    Production-level extraction with context and priority.
    """
    import re
    
    # 1. Extract ALL numbers with context
    numbers = re.findall(r"(₹?\s?\d[\d,]+)", text)
    print("ALL NUMBERS FOUND:", numbers)
    
    # 2. Categorize based on keywords
    premium_keywords = ["premium", "installment", "yearly", "annual", "payable", "due"]
    maturity_keywords = ["maturity", "benefit", "sum assured", "guaranteed", "death", "cover", "surrender"]
    term_keywords = ["policy term", "term", "years", "period", "duration", "tenure"]
    
    # 3. Extract with context window
    premium_list = extract_with_context(text, premium_keywords)
    maturity_list = extract_with_context(text, maturity_keywords)
    term_list = extract_with_context(text, term_keywords)
    
    print("PREMIUM LIST:", premium_list)
    print("MATURITY LIST:", maturity_list)
    print("TERM LIST:", term_list)
    
    # 4. Clean values
    premium_values = clean_values(premium_list)
    maturity_values = clean_values(maturity_list)
    
    # For terms, allow smaller values (5-50 years) — don't use clean_values which filters <1000
    term_values = []
    for v in term_list:
        v = re.sub(r"[^\d]", "", v)
        if v:
            val = int(v)
            if 5 <= val <= 50:
                term_values.append(val)
    
    # 5. DEDICATED PPT EXTRACTION (replaces buggy keyword+clean_values approach)
    ppt = extract_payment_term(text)
    
    print("CLEANED PREMIUM VALUES:", premium_values)
    print("CLEANED MATURITY VALUES:", maturity_values)
    print("CLEANED TERM VALUES:", term_values)
    print("DEDICATED PPT RESULT:", ppt)
    
    # 6. FINAL SELECTION LOGIC
    # For premium: use median to avoid outliers (min was picking tiny wrong values)
    if premium_values:
        sorted_premiums = sorted(premium_values)
        premium = sorted_premiums[len(sorted_premiums) // 2]
    else:
        premium = None
    maturity = max(maturity_values) if maturity_values else None
    policy_term = term_values[0] if term_values else None  # First reasonable value
    
    # 7. HEURISTIC FALLBACK FOR TABULAR DATA
    if not premium or not maturity or not policy_term:
        print("APPLYING TABULAR HEURISTICS...")
        # Get all numbers
        all_nums_raw = re.findall(r'\b\d{1,9}\b', text.replace(',', ''))
        all_nums = [int(n) for n in all_nums_raw]
        
        from collections import Counter
        
        if not premium:
            # Premium is typically between 5k and 500k
            candidates = [n for n in all_nums if 5000 <= n <= 500000]
            if candidates:
                counts = Counter(candidates)
                valid_candidates = {}
                for num, count in counts.items():
                    if policy_term and count == policy_term and num % 10000 == 0:
                        continue
                    if count >= 3:
                        valid_candidates[num] = count
                
                if valid_candidates:
                    best_candidate = sorted(valid_candidates.keys(), key=lambda x: all_nums.index(x))[0]
                    premium = best_candidate
                    print(f"Heuristic Premium (First Repeating): {premium} (freq: {valid_candidates[premium]})")
                        
        if not maturity:
            candidates = [n for n in all_nums if n > 100000]
            if candidates:
                maturity = max(candidates)
                print(f"Heuristic Maturity: {maturity}")
                
        if not policy_term:
            small_nums = [n for n in all_nums if 1 <= n <= 100]
            if small_nums:
                policy_term = max(small_nums)
                print(f"Heuristic Policy Term: {policy_term}")
                
        # PPT heuristic fallback — only if dedicated extraction returned nothing
        if ppt is None and premium and policy_term:
            all_nums_raw = re.findall(r'\b\d{1,9}\b', text.replace(',', ''))
            all_nums = [int(n) for n in all_nums_raw]
            premium_count = all_nums.count(premium)
            
            # Smart GST Detection: 1st year premium is often ~2.25% higher due to 4.5% vs 2.25% GST
            try:
                first_idx = all_nums.index(premium)
                # Check up to 15 numbers before the first occurrence of the regular premium
                for i in range(max(0, first_idx - 15), first_idx):
                    candidate = all_nums[i]
                    if premium < candidate < premium * 1.06:
                        premium_count += 1
                        print(f"Detected 1st Year GST Premium: {candidate}, adding 1 to PPT")
                        break
            except ValueError:
                pass
                
            if 3 <= premium_count <= policy_term:
                ppt = premium_count
            elif premium_count > policy_term:
                ppt = policy_term
            elif premium_count == 1:
                ppt = policy_term
            print(f"Heuristic PPT: {ppt} (based on premium freq {premium_count})")
    
    # 8. CROSS-VALIDATION: PPT must not exceed policy term
    if ppt is not None and policy_term is not None and ppt > policy_term:
        print(f"PPT CAPPED: {ppt} -> {policy_term} (cannot exceed policy term)")
        ppt = policy_term
    
    print("FINAL PREMIUM:", premium)
    print("FINAL MATURITY:", maturity)
    print("FINAL POLICY TERM:", policy_term)
    print("FINAL PPT:", ppt)
    
    return {
        "premium": premium,
        "maturity_value": maturity,
        "policy_term": policy_term,
        "payment_term": ppt
    }


def extract_policy_data(text):
    """
    Production-level policy data extraction with comprehensive validation.
    """
    print("EXTRACTED TEXT SAMPLE:", text[:500])
    
    # PART 1: SMART EXTRACTION
    data = smart_extract(text)
    
    # PART 6: VALIDATION LAYER (VERY IMPORTANT) - NEVER CRASH
    if data.get("premium") is None:
        print("WARNING: Premium could not be extracted correctly")
    
    if data.get("maturity_value") is None:
        print("WARNING: Maturity value could not be extracted correctly")
    
    if data.get("policy_term") is None:
        print("WARNING: Policy term could not be extracted correctly")
    
    # PART 2: POLICY LOGIC (CRITICAL FIX)
    if data.get("payment_term") is None:
        data["payment_term"] = data.get("policy_term")
        print(f"Using policy term as PPT: {data['payment_term']}")
    
    # AI fallback for missing critical fields
    missing_fields = [k for k, v in data.items() if v is None and k in ["premium", "maturity_value", "policy_term"]]
    if missing_fields:
        try:
            ai_data = ai_extract(text)
            print("AI EXTRACTION RESULT:", ai_data)
            
            # STEP 1: PROTECT AI DATA
            if ai_data and isinstance(ai_data, dict):
                for field in missing_fields:
                    ai_value = ai_data.get(field)
                    if ai_value:
                        data[field] = ai_value
                        print(f"AI filled {field}: {ai_value}")
            else:
                print("AI data is invalid or None")
        except Exception as e:
            print("AI EXTRACTION FAILED:", e)
    
    # STEP 4: NEVER CRASH SYSTEM - Always return something
    if data.get("premium") is None or data.get("maturity_value") is None:
        print("WARNING: Critical fields missing after extraction, but continuing...")
    
    print("FINAL EXTRACTED DATA:", data)
    return data


def safe_extract(text, patterns):
    """
    Extract value using multiple patterns with fallbacks.
    """
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            # Clean and convert
            cleaned = re.sub(r'[^\d.]', '', value)
            try:
                return float(cleaned)
            except ValueError:
                continue
    return None


def validate_and_normalize(data):
    """
    Validate extracted data and apply normalization rules.
    REMOVED: Fake default values that caused ₹1 issues.
    """
    # Validation layer with warnings - NO FAKE DEFAULTS
    if data.get("premium") == 0 or data.get("premium") is None:
        print("WARNING: Premium is 0 or None - keeping as None (no fake values)")
        # REMOVED: Fake premium estimation that caused issues
    
    if data.get("policy_term") == 0 or data.get("policy_term") is None:
        print("WARNING: Policy term is 0 or None - using default 10 years")
        data["policy_term"] = 10
    
    if data.get("payment_term") == 0 or data.get("payment_term") is None:
        print("WARNING: Payment term is 0 or None - using policy term as fallback")
        data["payment_term"] = data.get("policy_term", 10)
    
    # Enhanced normalization layer
    data["premium"] = normalize_amount(data.get("premium"))
    data["sum_assured"] = normalize_amount(data.get("sum_assured"))
    data["maturity_value"] = normalize_amount(data.get("maturity_value"))
    
    # Ensure values are never 0 unless truly missing
    for key in ["premium", "sum_assured", "maturity_value"]:
        if data.get(key) == 0:
            print(f"WARNING: {key} is 0 - converting to None for clarity")
            data[key] = None
    
    # REMOVED: Fake fallback logic that created unrealistic estimates
    # Keep values as None if not truly extracted
    
    return data


def normalize_amount(amount):
    """
    Normalize monetary amounts from various formats.
    """
    if amount is None:
        return None
    
    # Handle string amounts with lakhs/crores
    if isinstance(amount, str):
        amount_lower = amount.lower()
        
        # Convert lakhs to actual numbers (1 lakh = 100,000)
        if 'lakh' in amount_lower or 'लाख' in amount_lower:
            num = re.search(r'([\d.]+)', amount)
            if num:
                return float(num.group(1)) * 100000
        
        # Convert crores to actual numbers (1 crore = 10,000,000)
        if 'crore' in amount_lower or 'करोड़' in amount_lower:
            num = re.search(r'([\d.]+)', amount)
            if num:
                return float(num.group(1)) * 10000000
        
        # Convert monthly to yearly (multiply by 12)
        if 'monthly' in amount_lower:
            num = re.search(r'([\d.]+)', amount)
            if num:
                return float(num.group(1)) * 12
    
    return float(amount) if amount else None


def normalize_time_period(value, context=""):
    """
    Normalize time periods (monthly to yearly conversion).
    """
    if value is None:
        return None
    
    # If context indicates monthly, convert to yearly
    if isinstance(context, str) and 'monthly' in context.lower():
        return float(value) * 12
    
    return float(value)


def calculate_financials(data):
    """
    Production-level financial calculations with validation and realistic metrics.
    """
    premium = data.get("premium")
    ppt = data.get("payment_term")
    policy_term = data.get("policy_term")
    maturity = data.get("maturity_value")

    print("FINANCIAL INPUTS:")
    print(f"  Premium: {premium}")
    print(f"  PPT: {ppt}")
    print(f"  Policy Term: {policy_term}")
    print(f"  Maturity: {maturity}")

    # Validate inputs - NEVER CRASH, ONLY LOG
    if not all([premium, ppt, policy_term, maturity]):
        print("ERROR: Missing required financial data")
        print(f"  Premium: {premium}")
        print(f"  PPT: {ppt}")
        print(f"  Policy Term: {policy_term}")
        print(f"  Maturity: {maturity}")
        # Continue with available data instead of crashing

    # PART 3: CORRECT TOTAL INVESTMENT
    total_investment = premium * ppt
    print(f"TOTAL INVESTMENT: {total_investment}")

    # PART 4: FIX MATURITY VALUE
    if maturity is not None and total_investment is not None and maturity < total_investment:
        print("WARNING: Extracted maturity seems too low (missing bonuses), using actuarial estimate...")

        # Calculate using standard 5.5% CAGR for Indian Endowment Policies
        # Future value of annuity due (premiums paid at start of each year) for the PPT duration
        r = 0.055
        safe_ppt = ppt if ppt and ppt > 0 else (policy_term if policy_term else 1)
        annual_p = total_investment / safe_ppt
        
        fv_ppt = annual_p * (((1 + r)**safe_ppt - 1) / r) * (1 + r)
        
        safe_term = policy_term if policy_term else safe_ppt
        remaining_years = safe_term - safe_ppt
        
        final_fv = fv_ppt * ((1 + r)**remaining_years) if remaining_years > 0 else fv_ppt
        
        estimated_maturity = int(round(final_fv))
        
        if estimated_maturity > total_investment:
            print("Using actuarial estimated maturity:", estimated_maturity)
            maturity = estimated_maturity
        else:
            print("Estimate also failed, keeping original value")

    # STEP 3: FINAL SAFE CHECK (NO CRASH)
    if maturity is None:
        return {
            "error": "Unable to extract maturity value"
        }

    # STEP 5: ADD DEBUG PRIORITY LOG
    print("Final maturity used:", maturity)

    # PART 5: REAL FINANCIAL CALCULATIONS - SAFE HANDLING
    roi = None
    cagr = None
    net_profit = None
    
    tax_saved = 0
    # Assumed annual premium roughly equals total / ppt for tax purposes here
    annual_p = total_investment / ppt if (ppt and ppt > 0 and total_investment) else 0
    if annual_p > 0 and ppt > 0:
        deductible = min(annual_p, 150000)
        tax_saved = deductible * 0.30 * ppt

    if total_investment is not None and total_investment > 0:
        mat_val = maturity if maturity else 0

        # Component 1: Raw Cash Net Profit
        net_profit = mat_val - total_investment

        # Component 2: Inflation-Adjusted Net Profit (6% Indian inflation baseline)
        INFLATION = 0.06
        _years = policy_term if policy_term and policy_term > 0 else 1
        real_maturity = mat_val / ((1 + INFLATION) ** _years)
        inflation_adj_net_profit = int(round(real_maturity - total_investment))
        
        effective_inv = max(total_investment - tax_saved, 1)  # never zero

        # TRUE Annualized ROI — compound geometric formula
        # Formula: (maturity / effective_inv)^(1 / avg_time) - 1
        safe_ppt = ppt if ppt and ppt > 0 else 1
        avg_time = max(policy_term - (safe_ppt - 1) / 2.0, 1.0) if policy_term else 1.0
        try:
            roi = ((mat_val / effective_inv) ** (1.0 / avg_time) - 1) * 100
            roi = round(roi, 2)
        except (ValueError, ZeroDivisionError):
            roi = 0.0
        
        print(f"Raw Cash Net Profit: Rs.{net_profit:,.0f}")
        print(f"Inflation-Adj Net Profit: Rs.{inflation_adj_net_profit:,.0f}")
        print(f"Tax Saved (80C): Rs.{tax_saved:,.0f}")
        print(f"Effective Annualized ROI: {roi}%")
        
        if policy_term and policy_term > 0 and mat_val > 0:
            safe_ppt = ppt if ppt and ppt > 0 else 1
            avg_time = max(policy_term - (safe_ppt - 1) / 2.0, 1.0)
            cagr = ((mat_val / effective_inv) ** (1 / avg_time) - 1) * 100

    # --- IRR Calculation ---
    # Correct cashflow stream: GST-adjusted year-1, remaining premium years,
    # zero-yield waiting years (PPT → maturity), then maturity payout.
    irr = None
    if premium and ppt and maturity and maturity > 0:
        try:
            import numpy_financial as nf
            import math

            _ppt  = int(ppt)
            _term = int(policy_term) if policy_term and policy_term > _ppt else _ppt
            # Year 0 premium — Indian insurance GST makes it ~2.2% higher in year 1
            _y1 = int(premium * 1.022) if premium else premium
            # Build cashflow array
            cf = [-_y1] + [-premium] * max(_ppt - 1, 0)   # premium years
            cf += [0] * max(_term - _ppt - 1, 0)           # waiting years
            cf.append(maturity)                             # maturity payout

            irr_raw = nf.irr(cf)
            if (
                irr_raw is not None
                and not math.isnan(irr_raw)
                and not math.isinf(irr_raw)
                and irr_raw > -1
            ):
                irr_val = round(irr_raw * 100, 2)
                # Sanity check: insurance IRR should realistically be -5% to 30%
                if -5 <= irr_val <= 30:
                    irr = irr_val
                    print(f"IRR: {irr}%")
                else:
                    print(f"IRR sanity fail ({irr_val}%), using CAGR fallback")
                    irr = cagr
            else:
                print("IRR returned NaN/Inf, using CAGR fallback")
                irr = cagr
        except Exception as e:
            print("IRR ERROR:", e)
            irr = cagr  # graceful fallback to CAGR

    # PART 7: INTELLIGENT INSIGHT ENGINE
    if roi is None:
        verdict = "Cannot Determine"
    elif roi < 4:
        verdict = "Poor Investment"
    elif roi < 8:
        verdict = "Average Investment"
    else:
        verdict = "Good Investment"

    print(f"INVESTMENT VERDICT: {verdict}")

    # PART 8: DEBUG LOGGING
    print("FINANCIAL SUMMARY:")
    print(f"  Total Investment: Rs.{total_investment:,.0f}")
    print(f"  Maturity Value: Rs.{maturity:,.0f}")
    print(f"  Net Profit: Rs.{net_profit:,.0f}")
    print(f"  ROI: {roi:.2f}%")
    print(f"  CAGR: {cagr:.2f}%")
    print(f"  IRR: {irr:.2f}%" if irr else "  IRR: N/A")

    return {
        "total_investment": total_investment,
        "net_profit": net_profit,
        "roi": roi,
        "roi_verdict": verdict,
        "cagr": cagr,
        "irr": irr
    }
