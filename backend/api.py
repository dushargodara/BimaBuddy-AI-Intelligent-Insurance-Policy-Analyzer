"""
Flask REST API for Insurance Policy Analyzer.

Exposes endpoints for PDF upload and policy analysis with production-grade error handling.
"""

import json
import sys
import time
import io
from pathlib import Path
from typing import Any

# ── Force UTF-8 output so the rupee symbol (₹) never crashes on Windows ──────
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure project root is in path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env from project root before any config imports
_env_file = ROOT / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file, override=True)
    except ImportError:
        pass

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

import os
FLASK_HOST = "0.0.0.0"
FLASK_PORT = int(os.getenv("PORT", 10000))
FLASK_DEBUG = False
ALLOWED_EXTENSIONS = {"pdf"}

def validate_config():
    return None

from backend.services.pdf_service import get_processed_text
from backend.services.ai_service import extract_policy_data, extract_structured_from_chunks
from backend.services.regex_extractor import extract_financial_values, merge_with_ai
from backend.services.model import train_model, predict_risk
from backend.services.policy_classifier import detect_policy_type, is_term_insurance
from backend.services.risk_analyzer import (
    detect_risky_clauses,
    calculate_risk_score,
    get_risk_level,
)
from backend.services.clause_analyzer import detect_hidden_clauses
from backend.services.ai_validator import validate_financial_values, validate_policy_consistency
from backend.core.exceptions import (
    PolicyAnalyzerError,
    PDFProcessingError,
    AIAnalysisError,
    ConfigurationError,
)
from backend.core.logger import get_logger

logger = get_logger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# region agent log
def _debug_log(hypothesis_id: str, message: str, data: dict[str, Any] | None = None) -> None:
    """
    Append a single NDJSON debug line to debug-ffb454.log for this session.
    """
    payload = {
        "sessionId": "ffb454",
        "runId": "analyze-run",
        "hypothesisId": hypothesis_id,
        "location": "backend/api.py:analyze",
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    try:
        log_path = Path("debug-ffb454.log")
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        pass
# endregion


def _allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    err = validate_config()
    return jsonify({"status": "ok" if not err else "degraded", "error": err}), 200


@app.route("/", methods=["GET"])
def index():
    """Root endpoint for browser users."""
    return jsonify({
        "success": True,
        "message": "Intelligent Insurance Policy Analyzer Backend API is running.",
        "endpoints": ["GET /health", "POST /analyze", "POST /diagnose"]
    }), 200


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        result = process_policy(request)

        return jsonify({
            "status": "success",
            "data": result,
            "message": "Analysis completed"
        })

    except Exception as e:
        import traceback

        print("\n===== ERROR START =====")
        print("Error Message:", str(e))
        print("Full Traceback:")
        traceback.print_exc()
        print("===== ERROR END =====\n")

        return jsonify({
            "status": "error",
            "message": str(e),
            "data": {
                "error": True,
                "message": "Analysis failed but system handled gracefully"
            }
        }), 200


def clean_json(data):
    """Clean JSON data to remove NaN, Infinity, and other invalid values."""
    import math
    if isinstance(data, dict):
        return {k: clean_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_json(v) for v in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
    return data


def process_policy(request):
    """Process policy PDF and return full analysis result."""
    print("---- ANALYZE START ----")

    file = request.files.get("file")

    if not file:
        return {"error": "No file uploaded"}

    print("File received:", file.filename)

    # ── Step 1: Extract text from PDF ────────────────────────────────────────
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        file.save(tmp_file.name)
        tmp_path = tmp_file.name

    try:
        full_text, chunks, _ = get_processed_text(tmp_path)
        print("\n====== PIPELINE DEBUG START ======")
        print("\nSTEP 1: TEXT LENGTH:", len(full_text) if full_text else 0)
        print("STEP 1 SAMPLE:", full_text[:300] if full_text else "NO TEXT")
    finally:
        os.unlink(tmp_path)

    if not full_text:
        return {"error": "Could not extract text from PDF"}

    from backend.services.policy_classifier import is_insurance_policy
    if not is_insurance_policy(full_text):
        return {"error": "The uploaded document does not appear to be an insurance policy. Please upload a valid insurance document."}

    # ── Step 2: Extract financial data ───────────────────────────────────────
    try:
        # 2a. AI extraction — Gemini understands context, tables, and prose
        from backend.services.ai_extractor import ai_extract
        ai_data = ai_extract(full_text)
        print("\nSTEP 2a: AI EXTRACTED DATA:", ai_data)

        # 2b. Regex extraction — fast heuristic fallback
        from backend.services.extraction_engine import extract_policy_data as engine_extract
        regex_data = engine_extract(full_text)
        print("STEP 2b: REGEX EXTRACTED DATA:", regex_data)

        # 2c. Smart merge: AI is PRIMARY source (understands context),
        #     regex only fills gaps where AI returned nothing.
        def pick_best(ai_val, regex_val, is_term=False):
            """Return best valid value: AI preferred over regex."""
            def is_valid(v, term_mode):
                if v is None:
                    return False
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    return False
                if v <= 0:
                    return False
                if term_mode:
                    return 1 <= v <= 100    # years: 1–100
                else:
                    return v >= 1000        # amounts ≥ ₹1,000

            if is_valid(ai_val, is_term):
                return int(float(ai_val))
            if is_valid(regex_val, is_term):
                return int(float(regex_val))
            return None

        premium        = pick_best(ai_data.get("premium"),        regex_data.get("premium"),        is_term=False)
        policy_term    = pick_best(ai_data.get("policy_term"),    regex_data.get("policy_term"),    is_term=True)
        payment_term   = pick_best(ai_data.get("payment_term"),   regex_data.get("payment_term"),   is_term=True)
        maturity_value = pick_best(ai_data.get("maturity_value"), regex_data.get("maturity_value"), is_term=False)
        sum_assured    = pick_best(ai_data.get("sum_assured"),    regex_data.get("sum_assured"),    is_term=False)

        premium_frequency = (ai_data.get("premium_frequency") or "yearly") if isinstance(ai_data, dict) else "yearly"
        premium_frequency = str(premium_frequency).lower().strip()

        # Default payment_term to policy_term if still missing
        if payment_term is None and policy_term is not None:
            payment_term = policy_term

        extracted_data = {
            "premium":        premium,
            "policy_term":    policy_term,
            "payment_term":   payment_term,
            "maturity_value": maturity_value,
            "sum_assured":    sum_assured,
        }

        print(f"\nSTEP 2: MERGED EXTRACTED DATA: {extracted_data}")
        print(f"  Premium: {premium}  |  Policy Term: {policy_term}  |  Payment Term: {payment_term}")
        print(f"  Maturity: {maturity_value}  |  Sum Assured: {sum_assured}")

        # ── Step 3: Financial calculations ─────────────────────────────────────
        result   = {}
        warnings = []

        # Frequency multiplier (premium stored per-period, annualize it)
        freq_multiplier = 1
        if "month" in premium_frequency:
            freq_multiplier = 12
        elif "quarter" in premium_frequency:
            freq_multiplier = 4
        elif "half" in premium_frequency or "semi" in premium_frequency:
            freq_multiplier = 2

        annualized_premium = 0
        first_year_premium = 0
        total_investment   = 0

        if premium and payment_term:
            annualized_premium = premium * freq_multiplier
            # Indian insurance GST: year-1 is ~2.2% higher (4.5% vs 2.25% on subsequent years)
            first_year_premium = int(round(annualized_premium * 1.022))
            total_investment   = first_year_premium + annualized_premium * (payment_term - 1)
        else:
            warnings.append("Could not calculate total investment (missing premium or payment term)")

        # ── Actuarial maturity estimate for endowment plans ────────────────────
        is_term_plan = False
        try:
            is_term_plan = is_term_insurance(detect_policy_type(full_text))
        except Exception:
            pass

        if not is_term_plan and total_investment > 0 and policy_term and policy_term > 0:
            if not maturity_value or maturity_value < total_investment:
                r       = 0.055  # standard Indian endowment yield
                ppt     = payment_term if payment_term and payment_term > 0 else policy_term
                annual_p = annualized_premium if annualized_premium > 0 else (total_investment / ppt if ppt else 0)
                if annual_p > 0:
                    fv_ppt          = annual_p * (((1 + r) ** ppt - 1) / r) * (1 + r)
                    remaining_years = policy_term - ppt
                    final_fv        = fv_ppt * ((1 + r) ** remaining_years) if remaining_years > 0 else fv_ppt
                    maturity_value  = int(round(final_fv))
                    warnings.append(
                        f"Maturity value actuarially estimated at Rs.{maturity_value:,} "
                        f"(5.5% compounding; bonuses not in document)."
                    )

        # ── Import financial engine functions ──────────────────────────────────
        from backend.services.financial_engine import (
            calculate_cagr,
            calculate_inflation_adjusted_cagr,
            calculate_annualized_roi,
            calculate_irr,
            calculate_tax_effective_irr,
            calculate_break_even_year,
            calculate_net_profit,
            calculate_inflation_adjusted_profit,
        )

        roi                    = None
        cagr                   = None
        net_profit             = None
        irr                    = None
        tax_effective_irr      = None
        inflation_adjusted_cagr = None
        break_even_year        = None
        inflation_adj_net_profit = 0
        tax_saved              = 0

        INFLATION    = 0.06    # 6% Indian baseline
        TAX_RATE     = 0.312   # 30% slab + 4% cess
        SEC80C_LIMIT = 150_000.0

        # Section 80C tax benefit
        if annualized_premium > 0 and payment_term and payment_term > 0:
            deductible = min(annualized_premium, SEC80C_LIMIT)
            tax_saved  = deductible * TAX_RATE * payment_term

        if total_investment > 0:
            mat_val    = maturity_value if maturity_value else 0
            ppt_eval   = max(int(payment_term or 1), 1)
            _term_eval = max(int(policy_term or ppt_eval), ppt_eval)
            avg_time   = max(_term_eval - (ppt_eval - 1) / 2.0, 1.0)

            net_profit = int(round(calculate_net_profit(mat_val, total_investment)))
            inflation_adj_net_profit = int(round(
                calculate_inflation_adjusted_profit(mat_val, total_investment, _term_eval, INFLATION)
            ))

            cagr = calculate_cagr(total_investment, mat_val, avg_time)
            inflation_adjusted_cagr = (
                calculate_inflation_adjusted_cagr(cagr, INFLATION) if cagr is not None else None
            )

            roi = calculate_annualized_roi(
                total_investment=total_investment,
                maturity=mat_val,
                avg_holding_years=avg_time,
                tax_saved=tax_saved,
            )

            irr = calculate_irr(
                premium=annualized_premium,
                pay_years=ppt_eval,
                policy_term=_term_eval,
                maturity=mat_val,
                gst_adjusted_first_year=first_year_premium if first_year_premium > annualized_premium else None,
            )
            if irr is None:
                irr = cagr  # graceful fallback

            tax_effective_irr = calculate_tax_effective_irr(
                annual_premium=annualized_premium,
                pay_years=ppt_eval,
                policy_term=_term_eval,
                maturity=mat_val,
                tax_rate=TAX_RATE,
                sec80c_limit=SEC80C_LIMIT,
                gst_adjusted_first_year=first_year_premium if first_year_premium > annualized_premium else None,
            )
            # Preference: tax IRR → annualized ROI → CAGR
            roi = tax_effective_irr if tax_effective_irr is not None else (roi if roi is not None else cagr)

            break_even_year = calculate_break_even_year(
                annual_premium=annualized_premium,
                pay_years=ppt_eval,
                policy_term=_term_eval,
                maturity=mat_val,
                cagr_pct=cagr,
            )

        # Comparison projections
        fd_projection = 0
        mf_projection = 0
        if total_investment and policy_term:
            fd_projection = round(total_investment * ((1 + 0.07) ** policy_term), 2)
            mf_projection = round(total_investment * ((1 + 0.12) ** policy_term), 2)

        # ROI verdict
        if roi is None:
            roi_verdict = "Cannot Determine"
        elif roi < 4:
            roi_verdict = "Poor Investment"
        elif roi < 8:
            roi_verdict = "Average Investment"
        else:
            roi_verdict = "Good Investment"

        # ── ML Risk prediction ─────────────────────────────────────────────────
        ml_risk = "medium"
        try:
            ml_risk = predict_risk({
                "premium":          premium or 0,
                "policy_term":      policy_term or 0,
                "payment_term":     payment_term or 0,
                "total_investment": total_investment or 0,
                "maturity_value":   maturity_value or 0,
                "roi":              roi or 0,
                "cagr":             cagr or 0,
                "irr":              irr or 0,
                "claim_ratio":      90,
            })
        except Exception as _ml_err:
            print("ML RISK ERROR:", _ml_err)

        _ml_label = str(ml_risk).lower().strip()
        if _ml_label == "low":
            risk_score = 2
        elif _ml_label == "medium":
            risk_score = 5
        elif _ml_label == "high":
            risk_score = 8
        else:
            if roi is not None:
                if roi < 0:   risk_score = 9
                elif roi < 4: risk_score = 7
                elif roi < 8: risk_score = 5
                else:         risk_score = 3
            else:
                risk_score = 5

        # Policy rating
        if roi is not None and roi > 8:
            policy_rating = "Good"
        elif roi is not None and roi > 4:
            policy_rating = "Average"
        elif roi is not None:
            policy_rating = "Below Average"
        else:
            policy_rating = "Insufficient Data"

        result = {
            "total_investment":          total_investment or 0,
            "maturity_value":            maturity_value or 0,
            "net_profit":                net_profit or 0,
            "absolute_return":           net_profit or 0,
            "inflation_adj_net_profit":  inflation_adj_net_profit if total_investment > 0 else 0,
            "tax_benefit_80c":           int(round(tax_saved)) if tax_saved else 0,
            # rate metrics — store under ALL keys the frontend might read
            "roi":                       roi,
            "roi_percent":               roi,
            "tax_effective_irr":         tax_effective_irr,
            "roi_verdict":               roi_verdict,
            "cagr":                      cagr,
            "cagr_percent":              cagr,
            "irr":                       irr,
            "irr_percent":               irr,
            "break_even_year":           break_even_year,
            "risk_score":                risk_score,
            "policy_rating":             policy_rating,
            "fd_projection":             fd_projection,
            "mf_projection":             mf_projection,
            "premium_details": {
                "amount":       premium,
                "frequency":    premium_frequency,
                "payment_term": payment_term,
            },
            "advanced_metrics": {
                "inflation_adjusted_cagr":      inflation_adjusted_cagr,
                "total_premium_paid":           total_investment,
                "tax_saved_estimated":          int(round(tax_saved)) if tax_saved else 0,
                "inflation_adj_net_profit":     inflation_adj_net_profit if total_investment > 0 else 0,
                "effective_net_profit_with_tax": int(round(net_profit + tax_saved)) if (net_profit is not None and tax_saved) else (net_profit or 0),
            },
            "tenure_years": policy_term,
            "warnings":     warnings,
        }

        print("\nSTEP 3: FINANCIAL RESULT:", result)

        # ── Step 4: Text analysis (qualitative insights via Gemini) ───────────
        try:
            from backend.services.text_analyzer import analyze_policy_text
            text_analysis = analyze_policy_text(full_text)
            result["text_analysis"] = text_analysis
            result["policy_summary"] = {"simple_summary": text_analysis.get("policy_summary", "")}
            result["key_benefits"]   = text_analysis.get("key_benefits", [])
            result["exclusions"]     = text_analysis.get("exclusions", [])
            result["hidden_clauses"] = text_analysis.get("hidden_clauses", [])
            print("STEP 4: TEXT ANALYSIS OK")
        except Exception as e:
            print("TEXT ANALYSIS ERROR:", e)
            result["text_analysis"] = {
                "policy_summary": "Text analysis unavailable",
                "key_benefits":   [],
                "exclusions":     [],
                "hidden_clauses": []
            }
            result["policy_summary"] = {"simple_summary": ""}
            result["key_benefits"]   = []
            result["exclusions"]     = []
            result["hidden_clauses"] = []

        # ── Step 5: Policy type ────────────────────────────────────────────────
        try:
            policy_type = detect_policy_type(full_text)
            result["policy_type_detected"] = policy_type
        except Exception as e:
            print("POLICY TYPE ERROR:", e)
            result["policy_type_detected"] = "Unknown"

        # ── Step 6: Risk analysis ──────────────────────────────────────────────
        try:
            risky_clauses = detect_risky_clauses(full_text)
            result["risky_clauses"] = risky_clauses
            result["risk_level"]    = get_risk_level(result["risk_score"])
        except Exception as e:
            print("RISK ANALYSIS ERROR:", e)
            result["risky_clauses"] = []
            result["risk_level"]    = "Medium"

        # Step 7: ML prediction (already computed)
        result["ml_risk_prediction"] = ml_risk

        # Step 8: Comparison
        result["comparison"] = {
            "fd_7pct_maturity":       fd_projection,
            "mf_sip_12pct_projection": mf_projection,
        }

        # Guaranteed vs Non-Guaranteed
        text_lower = full_text.lower()
        if "guaranteed" in text_lower:
            result["guaranteed_vs_non_guaranteed"] = "Guaranteed"
        elif "non-guaranteed" in text_lower or "non guaranteed" in text_lower:
            result["guaranteed_vs_non_guaranteed"] = "Non-Guaranteed"
        else:
            result["guaranteed_vs_non_guaranteed"] = "Unknown"

        # Recommendation
        if roi is not None and roi < 4:
            result["recommendation"] = "This policy offers below-average returns. Consider alternatives like Fixed Deposits or Mutual Fund SIPs for better returns."
        elif roi is not None and roi < 8:
            result["recommendation"] = "This policy offers moderate returns. It may be suitable for conservative investors who prefer guaranteed returns with insurance cover."
        elif roi is not None:
            result["recommendation"] = "This policy offers competitive returns along with insurance coverage. Good choice for risk-averse investors."
        else:
            result["recommendation"] = "Unable to determine returns. Please verify the policy details manually."

        result["validated_data"] = extracted_data

        print("\n====== PIPELINE DEBUG END ======")
        print("FINAL RESULT:", {k: v for k, v in result.items() if k != "text_analysis"})

        return clean_json(result)

    except Exception as e:
        print("PIPELINE ERROR:", e)
        import traceback
        traceback.print_exc()

        fallback = {
            "total_investment": 0.0,
            "maturity_value":   0.0,
            "absolute_return":  0.0,
            "net_profit":       0.0,
            "irr":              0.0,
            "risk_score":       9,
            "policy_rating":    "Error",
            "fd_projection":    0.0,
            "mf_projection":    0.0,
            "warnings":         [f"Pipeline error: {str(e)}"],
        }
        try:
            from backend.services.text_analyzer import analyze_policy_text
            fallback["text_analysis"] = analyze_policy_text(full_text)
        except Exception:
            fallback["text_analysis"] = {
                "policy_summary": "Analysis failed",
                "key_benefits":   [],
                "exclusions":     [],
                "hidden_clauses": []
            }
        return fallback


@app.errorhandler(Exception)
def handle_error(e):
    import traceback
    print("\n UNCAUGHT ERROR")
    traceback.print_exc()

    return jsonify({
        "status": "error",
        "message": "Something went wrong",
        "details": str(e),
        "data": {
            "error": True,
            "message": "Analysis failed but system handled gracefully"
        }
    }), 200


@app.route("/diagnose", methods=["POST"])
def diagnose():
    """
    Debug endpoint: run each stage and report where it fails.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file"}), 400
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400
    if not _allowed_file(file.filename):
        return jsonify({"success": False, "error": "Only PDF allowed"}), 400

    report = {"stages": {}, "error": None}

    try:
        filename    = secure_filename(file.filename) or "upload.pdf"
        upload_path = Path(ROOT) / "uploads"
        upload_path.mkdir(exist_ok=True)
        filepath    = upload_path / filename
        file.save(str(filepath))

        try:
            full_text, chunks, _ = get_processed_text(str(filepath))
            report["stages"]["pdf_extraction"] = "ok"
            report["text_length"]   = len(full_text or "")
            report["chunks_count"]  = len(chunks)
        except PDFProcessingError as e:
            report["stages"]["pdf_extraction"] = "failed"
            report["error"] = e.message
            try:
                filepath.unlink(missing_ok=True)
            except OSError:
                pass
            return jsonify(report), 422

        if not full_text:
            report["stages"]["pdf_extraction"] = "empty"
            report["error"] = "No text extracted (pdfplumber + OCR both failed)"
            try:
                filepath.unlink(missing_ok=True)
            except OSError:
                pass
            return jsonify(report), 422

        try:
            ai_data = extract_policy_data(full_text) if not (chunks and len(chunks) > 1) else extract_structured_from_chunks(chunks)
            report["stages"]["ai_extraction"] = "ok" if ai_data else "empty"
        except AIAnalysisError as e:
            report["stages"]["ai_extraction"] = "failed"
            report["error"] = e.message
        except Exception as e:
            report["stages"]["ai_extraction"] = "error"
            report["error"] = str(e)

        try:
            filepath.unlink(missing_ok=True)
        except OSError:
            pass

        return jsonify(report), 200
    except Exception as e:
        report["error"] = str(e)
        return jsonify(report), 500


@app.errorhandler(413)
def too_large(e):
    """Handle file too large."""
    return jsonify({"success": False, "error": "File too large (max 16MB)"}), 413


@app.errorhandler(404)
def not_found(e):
    """Handle 404."""
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500."""
    logger.error("Internal server error: %s", e)
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    try:
        train_model()
        logger.info("ML Risk model trained successfully")
    except Exception as e:
        logger.warning("Failed to train ML model: %s", e)

    port = int(os.getenv("PORT", 10000))
    logger.info("Starting Intelligent Insurance Policy Analyzer API on %s:%s", "0.0.0.0", port)
    app.run(host="0.0.0.0", port=port)
