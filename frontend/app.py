import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from backend.pipeline import process_policy

st.set_page_config(
    page_title="BimaBuddy AI — Intelligent Insurance Analyzer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for Premium SaaS UI
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif; 
    color: #1e293b;
    background-color: #f8fafc;
}

/* Base background */
.stApp {
    background-color: #f8fafc !important;
}

[data-testid="stAppViewContainer"] {
    background-color: #f8fafc !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Hero Section */
.hero-container {
    background: linear-gradient(135deg, #e0e7ff 0%, #f1f5f9 100%);
    padding: 3.5rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 2.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    border: 1px solid #e2e8f0;
}
.hero-logo {
    font-size: 3.5rem;
    margin-bottom: 0.5rem;
}
.hero-title {
    font-size: 2.75rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 0.5rem 0;
}
.hero-subtitle {
    font-size: 1.15rem;
    color: #64748b;
    margin: 0;
    font-weight: 400;
}

/* Feature Strip Cards */
.feature-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    height: 100%;
}
.feature-icon {
    font-size: 1.75rem;
    margin-bottom: 0.75rem;
}
.feature-title {
    font-weight: 600;
    color: #334155;
    font-size: 1.05rem;
    margin-bottom: 0.25rem;
}
.feature-desc {
    font-size: 0.85rem;
    color: #64748b;
}

/* Data Cards */
.data-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.75rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    height: 100%;
    transition: transform 0.2s, box-shadow 0.2s;
}
.data-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
}
.data-card-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.data-card-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
}
.data-card-sub {
    font-size: 0.85rem;
    color: #94a3b8;
}

/* Highlight Card (Blue) */
.data-card.highlight {
    background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
    border: 1px solid #bfdbfe;
}
.data-card.highlight .data-card-value {
    color: #1d4ed8;
}

/* Invest Comparison Cards */
.invest-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 1.5rem;
    border-top: 4px solid #e2e8f0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    text-align: center;
}
.invest-card-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 0.75rem;
}
.invest-card-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
}

/* Status Badges */
.badge {
    display: inline-block;
    padding: 0.35rem 1rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 600;
}
.badge-good { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
.badge-warning { background: #fef08a; color: #854d0e; border: 1px solid #fde047; }
.badge-danger { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
.badge-neutral { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }

/* Pills for text items */
.pill {
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    font-size: 0.9rem;
    margin: 0.3rem;
    font-weight: 500;
}
.pill-green { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.pill-yellow { background: #fefce8; color: #854d0e; border: 1px solid #fef08a; }
.pill-red { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }

/* Sections */
.section-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #1e293b;
    margin: 2.5rem 0 1.25rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e2e8f0;
}

/* Success Banner */
.success-banner {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #15803d;
    padding: 1.25rem 1.5rem;
    border-radius: 12px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    font-size: 1.1rem;
}

/* Risk Analysis Box */
.risk-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02) inset;
}

/* Recommendation Box */
.rec-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 4px solid #3b82f6;
    padding: 1.5rem;
    border-radius: 8px;
    color: #1e3a8a;
    font-size: 1.1rem;
    margin: 2rem 0;
}

/* Custom File Uploader */
[data-testid="stFileUploader"] {
    background-color: #ffffff !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    border: 2px dashed #cbd5e1 !important;
}

/* Primary Button */
.stButton>button {
    background: #2563eb;
    color: #ffffff;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    border: none;
    width: 100%;
    transition: all 0.2s;
    font-size: 1.05rem;
}
.stButton>button:hover {
    background: #1d4ed8;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    color: #ffffff;
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 5rem;
    padding-top: 2rem;
    border-top: 1px solid #e2e8f0;
    color: #94a3b8;
    font-size: 0.95rem;
    line-height: 1.6;
}

</style>
""", unsafe_allow_html=True)

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
    icon = f'<span style="font-size:1rem; cursor:help; color:#94a3b8;" title="{tooltip}">ⓘ</span>' if tooltip else ""
    
    st.markdown(f"""
    <div class="data-card{hl_class}">
        <div class="data-card-title">
            <span>{title}</span>
            {icon}
        </div>
        <div class="data-card-value">{value}</div>
        <div class="data-card-sub">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

def draw_invest_card(title, value, color_hex):
    st.markdown(f"""
    <div class="invest-card" style="border-top-color: {color_hex};">
        <div class="invest-card-title">{title}</div>
        <div class="invest-card-value" style="color: {color_hex};">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_result(data: dict) -> None:
    if data.get("degraded_analysis"):
        st.warning("⚠️ Partial analysis: AI could not fully parse the document.")

    # 3. RESULT HEADER
    st.markdown("""
    <div class="success-banner">
        <span>✅</span>
        <span>Analysis Completed Successfully</span>
    </div>
    """, unsafe_allow_html=True)

    policy_type = data.get("policy_type_detected", "N/A").upper()
    gvng        = data.get("guaranteed_vs_non_guaranteed", "N/A")
    roi_verdict = data.get("roi_verdict", "Unknown")
    
    badge_cls = "badge-neutral"
    if "Good" in roi_verdict: badge_cls = "badge-good"
    elif "Average" in roi_verdict: badge_cls = "badge-warning"
    elif "Poor" in roi_verdict: badge_cls = "badge-danger"

    st.markdown(f"""
    <div style="display:flex; gap:1rem; margin-bottom:2rem; align-items:center; flex-wrap:wrap;">
        <span class="badge badge-neutral">📋 Policy Type: {policy_type}</span>
        <span class="badge badge-neutral">💰 Returns Type: {gvng}</span>
        <span class="badge {badge_cls}">🎯 Verdict: {roi_verdict}</span>
    </div>
    """, unsafe_allow_html=True)

    summary = data.get("policy_summary", {})
    simple  = summary.get("simple_summary") if isinstance(summary, dict) else str(summary)
    if simple:
        st.markdown(f"<div style='background:#ffffff; border:1px solid #e2e8f0; padding:1.25rem; border-radius:12px; color:#334155; margin-bottom:2.5rem; font-size:1.05rem; line-height:1.6; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'><strong>Summary:</strong> {simple}</div>", unsafe_allow_html=True)

    # 4. CORE FINANCIALS (4 BIG CARDS)
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

    # 5. METRICS SECTION
    st.markdown("<div class='section-title'>Rate Metrics & Premium</div>", unsafe_allow_html=True)
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

    # 6. ADVANCED INSIGHTS
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

    # 8. RISKY CLAUSES
    risky = data.get("risky_clauses", [])
    if risky:
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        st.error("🚨 Risky Clauses Detected", icon="🚨")
        for r in risky:
            st.markdown(f"- **{r.get('keyword', '')}:** {r.get('snippet', '')[:250]}…")

    # 7. QUALITATIVE ANALYSIS
    st.markdown("<div class='section-title'>Qualitative Analysis</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("<b style='color:#1e293b; font-size:1.05rem;'>✅ Key Benefits</b><br>", unsafe_allow_html=True)
        benefits = data.get("key_benefits", [])
        if benefits:
            pills = "".join(f"<div class='pill pill-green'>✓ {b}</div>" for b in benefits)
            st.markdown(f"<div>{pills}</div><br>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#94a3b8;'>No benefits extracted.</span><br><br>", unsafe_allow_html=True)

        st.markdown("<b style='color:#1e293b; font-size:1.05rem;'>🔍 Hidden Clauses</b><br>", unsafe_allow_html=True)
        clauses = data.get("hidden_clauses", [])
        if clauses:
            pills = "".join(f"<div class='pill pill-yellow'>⚠️ {c}</div>" for c in clauses)
            st.markdown(f"<div>{pills}</div><br>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#94a3b8;'>No hidden clauses identified.</span><br><br>", unsafe_allow_html=True)

    with c2:
        st.markdown("<b style='color:#1e293b; font-size:1.05rem;'>❌ Exclusions</b><br>", unsafe_allow_html=True)
        exclusions = data.get("exclusions", [])
        if exclusions:
            pills = "".join(f"<div class='pill pill-red'>✕ {e}</div>" for e in exclusions)
            st.markdown(f"<div>{pills}</div><br>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#94a3b8;'>No exclusions extracted.</span><br><br>", unsafe_allow_html=True)

        risk_score = data.get("risk_score", 5)
        risk_level = data.get("risk_level", "Medium")
        ml_risk    = data.get("ml_risk_prediction", "N/A")
        r_badge = "badge-good" if risk_score <= 3 else ("badge-warning" if risk_score <= 6 else "badge-danger")
        
        st.markdown("<b style='color:#1e293b; font-size:1.05rem;'>🛡️ Risk Analysis</b><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="risk-box" style="margin-top: 0.25rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <span style="color:#475569; font-weight:500;">Risk Score:</span>
                <span class="badge {r_badge}">{risk_score}/10 ({risk_level})</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#475569; font-weight:500;">ML Prediction:</span>
                <span style="font-weight:600; color:#0f172a;">{str(ml_risk).title()}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


    # 9. INVESTMENT COMPARISON
    st.markdown("<div class='section-title'>Investment Comparison</div>", unsafe_allow_html=True)
    
    comp = data.get("comparison", {})
    policy_roi = data.get("roi") or data.get("roi_percent") or 0
    fd_val = comp.get("fd_7pct_maturity") or 0
    mf_val = comp.get("mf_sip_12pct_projection") or 0

    c1, c2, c3 = st.columns(3)
    r_color = "#16a34a" if policy_roi >= 7 else "#dc2626"
    with c1:
        draw_invest_card("Your Policy Returns", fmt_pct(policy_roi), r_color)
    with c2:
        draw_invest_card("Fixed Deposit (7%)", fmt_inr(fd_val), "#64748b")
    with c3:
        draw_invest_card("Mutual Fund (12%)", fmt_inr(mf_val), "#2563eb")

    # 10. RECOMMENDATION BOX
    rec = data.get("recommendation", "")
    if rec:
        st.markdown(f"""
        <div class="rec-box">
            <strong>💡 Recommendation:</strong><br/>
            {rec}
        </div>
        """, unsafe_allow_html=True)

    warnings = data.get("warnings", [])
    if warnings:
        with st.expander("ℹ️ Analysis Notes"):
            for w in warnings:
                st.info(w)

def main() -> None:
    # 1. HERO SECTION (Top)
    st.markdown("""
    <div class="hero-container">
        <div class="hero-logo">🛡️</div>
        <h1 class="hero-title">BimaBuddy AI</h1>
        <p class="hero-subtitle">Intelligent Insurance Policy Analyzer</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. FEATURE STRIP (3 CARDS)
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-title">Smart Analysis</div>
            <div class="feature-desc">AI-powered extraction of key benefits and terms</div>
        </div>
        """, unsafe_allow_html=True)
    with f2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">👀</div>
            <div class="feature-title">Risk Detection</div>
            <div class="feature-desc">Uncovers hidden clauses and exclusions</div>
        </div>
        """, unsafe_allow_html=True)
    with f3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Comparison</div>
            <div class="feature-desc">Benchmarks against FDs and Mutual Funds</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)

    # UPLOAD SECTION
    col_up1, col_up2, col_up3 = st.columns([1,2,1])
    with col_up2:
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
                try:
                    result = process_policy(uploaded)
                    
                    if result is None:
                        st.error("Analysis failed to return result.")
                        return

                    if "error" in result:
                        st.error(result["error"])
                        return

                    st.session_state['analysis_result'] = result
                    
                except Exception as e:
                    import traceback
                    st.error(f"Unexpected error: {str(e)}")
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

    if 'analysis_result' in st.session_state:
        st.markdown("<hr style='border:1px solid #e2e8f0; margin: 3rem 0;'>", unsafe_allow_html=True)
        render_result(st.session_state['analysis_result'])

    # 11. FOOTER
    st.markdown("""
    <div class="footer">
        <p>Made with ❤️ by <strong>BimaBuddy AI</strong></p>
        <p>Contact: support@bimabuddy.ai</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
