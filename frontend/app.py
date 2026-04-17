import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
import streamlit as st


st.set_page_config(
    page_title="BimaBuddy AI — Insurance Policy Analyzer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: #f8fafc;
}

[data-testid="stAppViewContainer"] {
    background: #f8fafc;
}

/* Header */
.top-header {
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 1.5rem 2rem;
    margin: -4rem -4rem 2rem -4rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.header-icon {
    font-size: 2rem;
    background: #eff6ff;
    padding: 0.5rem;
    border-radius: 12px;
    color: #2563eb;
}
.header-titles h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
    padding: 0;
}
.header-titles p {
    font-size: 0.9rem;
    color: #64748b;
    margin: 0;
}

/* Cards */
.fin-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    height: 100%;
}
.fin-card-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}
.fin-card-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
}
.fin-card-sub {
    font-size: 0.85rem;
    color: #94a3b8;
}
/* Highlighted Card */
.fin-card.highlight {
    background: #eff6ff;
    border-color: #bfdbfe;
}
.fin-card.highlight .fin-card-title { color: #1e40af; }
.fin-card.highlight .fin-card-value { color: #1e3a8a; }

/* Status Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-good { background: #dcfce7; color: #166534; }
.badge-warning { background: #fef9c3; color: #854d0e; }
.badge-danger { background: #fee2e2; color: #991b1b; }
.badge-neutral { background: #f1f5f9; color: #475569; }

hr {
    border-color: #e2e8f0;
    margin: 2rem 0;
}

.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 8px;
    font-weight: 500;
    padding: 0.5rem 1rem;
    border: none;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    transition: all 0.2s;
}
.stButton>button:hover {
    background-color: #1d4ed8;
    box-shadow: 0 6px 8px -1px rgba(37, 99, 235, 0.3);
}

.section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 1rem;
}

/* Pills */
.pill {
    display: inline-flex;
    align-items: center;
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    font-size: 0.875rem;
    margin: 0.25rem;
    font-weight: 500;
}
.pill-green { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.pill-red { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
.pill-yellow { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }

.text-sm { font-size: 0.875rem; }
.text-muted { color: #64748b; }

</style>
""", unsafe_allow_html=True)


def call_analyze_api(uploaded_file) -> dict | None:
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        resp  = requests.post(f"{API_BASE}/analyze", files=files, timeout=300)
        resp.raise_for_status()
        res = resp.json()
        if res.get("status") == "success":
            return res.get("data", {})
        else:
            st.error(res.get("message", "Analysis failed"))
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to backend at `{API_BASE}`. Ensure the Flask API is running.")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. Try a smaller PDF or wait and retry.")
        return None
    except requests.exceptions.HTTPError as e:
        try:
            err_data = e.response.json() if e.response else {}
            msg      = err_data.get("error", str(e))
            st.error(f"**Analysis failed:** {msg}")
        except Exception:
            st.error(str(e))
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def fmt_inr(value):
    if value is None:
        return "N/A"
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "N/A"

def fmt_pct(value, decimals=2):
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"

def draw_card(title, value, subtext="", highlight=False, tooltip=""):
    hl_class = " highlight" if highlight else ""
    icon = ' <span style="font-size:0.8rem; cursor:help;">ⓘ</span>' if tooltip else ""
    title_attr = f' title="{tooltip}"' if tooltip else ""
    
    st.markdown(f"""
    <div class="fin-card{hl_class}"{title_attr} style="{ 'cursor:help;' if tooltip else '' }">
        <div class="fin-card-title" style="display:flex; justify-content:space-between; align-items:center;">
            <span>{title}</span>
            {icon}
        </div>
        <div class="fin-card-value">{value}</div>
        <div class="fin-card-sub">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

def render_result(data: dict) -> None:
    if data.get("degraded_analysis"):
        st.warning("⚠️ Partial analysis: AI could not fully parse the document.")

    policy_type = data.get("policy_type_detected", "N/A").upper()
    gvng        = data.get("guaranteed_vs_non_guaranteed", "N/A")
    roi_verdict = data.get("roi_verdict", "Unknown")
    
    badge_cls = "badge-neutral"
    if "Good" in roi_verdict: badge_cls = "badge-good"
    elif "Average" in roi_verdict: badge_cls = "badge-warning"
    elif "Poor" in roi_verdict: badge_cls = "badge-danger"

    st.markdown(f"""
    <div style="display:flex; gap:1rem; margin-bottom:1.5rem; align-items:center;">
        <span class="badge badge-neutral">Policy Type: {policy_type}</span>
        <span class="badge badge-neutral">Returns: {gvng}</span>
        <span class="badge {badge_cls}">Verdict: {roi_verdict}</span>
    </div>
    """, unsafe_allow_html=True)

    summary = data.get("policy_summary", {})
    simple  = summary.get("simple_summary") if isinstance(summary, dict) else str(summary)
    if simple:
        st.markdown(f"<div style='background:#f1f5f9; padding:1rem; border-radius:8px; color:#334155; margin-bottom:2rem;'><strong>Summary:</strong> {simple}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Core Financials</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    total_investment = data.get("total_investment") or 0
    maturity_value   = data.get("maturity_value")   or 0
    net_profit       = data.get("net_profit")        or 0
    roi              = data.get("roi") or data.get("roi_percent")

    delta_str = f"+{fmt_inr(net_profit)}" if net_profit >= 0 else f"-{fmt_inr(abs(net_profit))}"

    with c1: draw_card("Total Investment", fmt_inr(total_investment), "Premiums over term", tooltip="Total money you pay to the insurance company over the years.")
    with c2: draw_card("Maturity Value", fmt_inr(maturity_value), "Expected corpus", tooltip="The total money you get back at the end of the policy.")
    with c3: draw_card("Net Profit", delta_str, "Maturity minus investment", tooltip="Your overall earnings (Money you get back minus money you paid).")
    with c4: draw_card("Annualized ROI", fmt_pct(roi), "After-tax return", highlight=True, tooltip="Your yearly return after factoring in the income tax you saved.")

    st.markdown("<br><div class='section-title'>Rate Metrics & Premium</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    cagr = data.get("cagr") or data.get("cagr_percent")
    irr  = data.get("irr")  or data.get("irr_percent")
    be   = data.get("break_even_year")
    
    prem_details = data.get("premium_details", {})
    prem_amt = fmt_inr(prem_details.get("amount"))
    prem_freq = (prem_details.get("frequency") or "yearly").title()
    
    with c1: draw_card("CAGR", fmt_pct(cagr), "Pure growth rate", tooltip="Your yearly growth rate as if your money was growing in a standard bank savings account.")
    with c2: draw_card("IRR", fmt_pct(irr), "Cashflow return rate", tooltip="Your true yearly return considering exactly when you make your payments each year.")
    with c3: draw_card("Break-Even", f"{float(be):.1f} yrs" if be is not None else "N/A", "Value > Premiums", tooltip="The year when your policy's value finally becomes bigger than the total money you put in.")
    with c4: draw_card("Premium", prem_amt, f"{prem_freq} payment", tooltip="Your regular payment amount.")

    st.markdown("---")
    st.markdown("<div class='section-title'>Advanced Insights</div>", unsafe_allow_html=True)
    
    adv = data.get("advanced_metrics", {})
    c1, c2, c3 = st.columns(3)
    with c1:
        tax_ben = data.get("tax_benefit_80c") or adv.get("tax_saved_estimated") or 0
        draw_card("80C Tax Benefit", fmt_inr(tax_ben), "Estimated tax saved", tooltip="The total income tax you save because of buying this policy.")
    with c2:
        infl_adj = data.get("inflation_adj_net_profit") or adv.get("inflation_adj_net_profit") or 0
        draw_card("Inflation-Adj Profit", fmt_inr(infl_adj), "Today's purchasing power", tooltip="Your actual profit after removing the effect of rising prices (inflation).")
    with c3:
        adj_cagr = adv.get("inflation_adjusted_cagr")
        draw_card("Real CAGR", fmt_pct(adj_cagr), "Stripping 6% inflation", tooltip="Your yearly growth rate considering that things get more expensive every year. (Negative means you lose buying power).")

    st.markdown("---")
    st.markdown("<div class='section-title'>Qualitative Analysis</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("<b>✅ Key Benefits</b>", unsafe_allow_html=True)
        benefits = data.get("key_benefits", [])
        if benefits:
            pills = "".join(f"<div class='pill pill-green'>✓ {b}</div>" for b in benefits)
            st.markdown(f"<div>{pills}</div><br>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='text-muted'>No benefits extracted.</span><br><br>", unsafe_allow_html=True)

        st.markdown("<b>🔍 Hidden Clauses</b>", unsafe_allow_html=True)
        clauses = data.get("hidden_clauses", [])
        if clauses:
            pills = "".join(f"<div class='pill pill-yellow'>• {c}</div>" for c in clauses)
            st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='text-muted'>No hidden clauses identified.</span>", unsafe_allow_html=True)

    with c2:
        st.markdown("<b>❌ Exclusions</b>", unsafe_allow_html=True)
        exclusions = data.get("exclusions", [])
        if exclusions:
            pills = "".join(f"<div class='pill pill-red'>✕ {e}</div>" for e in exclusions)
            st.markdown(f"<div>{pills}</div><br>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='text-muted'>No exclusions extracted.</span><br><br>", unsafe_allow_html=True)

        risk_score = data.get("risk_score", 5)
        risk_level = data.get("risk_level", "Medium")
        ml_risk    = data.get("ml_risk_prediction", "N/A")
        r_badge = "badge-good" if risk_score <= 3 else ("badge-warning" if risk_score <= 6 else "badge-danger")
        
        st.markdown("<b>⚠️ Risk Analysis</b>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:1rem; margin-top:0.5rem;">
            <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                <span class="text-sm">Risk Score:</span>
                <span class="badge {r_badge}">{risk_score}/10 ({risk_level})</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span class="text-sm">ML Prediction:</span>
                <span class="text-sm font-weight-bold">{str(ml_risk).title()}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    risky = data.get("risky_clauses", [])
    if risky:
        st.error("🚨 Risky Clauses Detected")
        for r in risky:
            st.markdown(f"- **{r.get('keyword', '')}:** {r.get('snippet', '')[:200]}…")

    st.markdown("---")
    st.markdown("<div class='section-title'>Investment Comparison</div>", unsafe_allow_html=True)
    
    comp = data.get("comparison", {})
    policy_roi = data.get("roi") or data.get("roi_percent") or 0
    fd_val = comp.get("fd_7pct_maturity") or 0
    mf_val = comp.get("mf_sip_12pct_projection") or 0

    c1, c2, c3 = st.columns(3)
    roi_color = "#16a34a" if policy_roi >= 7 else "#dc2626"
    with c1:
        st.markdown(f"<div class='fin-card' style='border-top:4px solid {roi_color}'><b>Your Policy Returns</b><br><span style='font-size:1.5rem; font-weight:700; color:{roi_color}'>{fmt_pct(policy_roi)}</span></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='fin-card' style='border-top:4px solid #64748b'><b>Fixed Deposit (7%)</b><br><span style='font-size:1.5rem; font-weight:700; color:#475569'>{fmt_inr(fd_val)}</span></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='fin-card' style='border-top:4px solid #2563eb'><b>Mutual Fund (12%)</b><br><span style='font-size:1.5rem; font-weight:700; color:#2563eb'>{fmt_inr(mf_val)}</span></div>", unsafe_allow_html=True)

    rec = data.get("recommendation", "")
    if rec:
        st.markdown(f"<div style='margin-top:1.5rem; padding:1rem; border-left:4px solid #2563eb; background:#eff6ff; color:#1e3a8a; border-radius:4px;'><b>Recommendation:</b> {rec}</div>", unsafe_allow_html=True)

    warnings = data.get("warnings", [])
    if warnings:
        with st.expander("ℹ️ Analysis Notes", expanded=False):
            for w in warnings:
                st.info(w)

def main() -> None:
    st.markdown("""
    <div class="top-header">
        <div class="header-icon">🛡️</div>
        <div class="header-titles">
            <h1>BimaBuddy AI</h1>
            <p>Intelligent Insurance Policy Analyzer</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload your Insurance Policy PDF",
        type=["pdf"],
        help="Max 16 MB — text-selectable PDFs work best",
    )

    if st.button("🔍 Analyze Policy", use_container_width=True):
        if not uploaded:
            st.warning("Please upload a PDF file first.")
            return

        with st.spinner("Analyzing your policy with Gemini AI… this may take 30–60 seconds."):
            result = call_analyze_api(uploaded)

        if result is None:
            return  

        if "error" in result:
            st.error(result["error"])
            return

        render_result(result)

if __name__ == "__main__":
    main()
