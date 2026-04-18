import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from backend.pipeline import process_policy

st.set_page_config(
    page_title="BimaBuddy AI",
    page_icon="🛡️",
    layout="wide"
)

# ---------------- PREMIUM CSS ----------------
st.markdown("""
<style>
body {
    background-color: #f8fafc;
}

.main {
    background: #f8fafc;
}

/* HERO */
.hero {
    text-align: center;
    padding: 3rem 1rem;
}

.hero h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #0f172a;
}

.hero p {
    color: #64748b;
    font-size: 1.1rem;
}

/* CARDS */
.card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    transition: 0.2s;
}
.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.1);
}

/* FEATURE */
.feature-title {
    font-weight: 600;
    font-size: 1.1rem;
}

.footer {
    text-align: center;
    padding: 2rem;
    color: #64748b;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HERO ----------------
st.markdown("""
<div class="hero">
    <h1>🛡️ BimaBuddy AI</h1>
    <p>Understand your Insurance Policy Instantly</p>
</div>
""", unsafe_allow_html=True)

# ---------------- UPLOAD ----------------
uploaded = st.file_uploader("Upload your policy PDF", type=["pdf"])

analyze_btn = st.button("🔍 Analyze Policy", use_container_width=True)

# ---------------- TRUST SECTION ----------------
st.markdown("### Trusted by users")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown('<div class="card">10,000+ Policies Analyzed</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="card">AI Powered Insights</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="card">Secure & Private</div>', unsafe_allow_html=True)

# ---------------- FEATURES ----------------
st.markdown("### Why Choose Us")
f1, f2, f3 = st.columns(3)

with f1:
    st.markdown('<div class="card"><div class="feature-title">📊 Smart Analysis</div><p>Understand returns, risk, and benefits instantly.</p></div>', unsafe_allow_html=True)

with f2:
    st.markdown('<div class="card"><div class="feature-title">⚠️ Risk Detection</div><p>Find hidden clauses and risks in seconds.</p></div>', unsafe_allow_html=True)

with f3:
    st.markdown('<div class="card"><div class="feature-title">📈 Comparison</div><p>Compare with FD & Mutual Funds easily.</p></div>', unsafe_allow_html=True)

# ---------------- RESULT ----------------
def render_result(data):
    st.success("Analysis Completed")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Investment", f"₹{data.get('total_investment',0):,.0f}")
    col2.metric("Maturity", f"₹{data.get('maturity_value',0):,.0f}")
    col3.metric("Profit", f"₹{data.get('net_profit',0):,.0f}")
    col4.metric("ROI", f"{data.get('roi',0)}%")

    st.markdown("### Recommendation")
    st.info(data.get("recommendation","N/A"))

# ---------------- LOGIC ----------------
if analyze_btn:
    if not uploaded:
        st.warning("Upload a file first")
    else:
        with st.spinner("Analyzing..."):
            try:
                result = process_policy(uploaded)
                render_result(result)
            except Exception as e:
                st.error(str(e))

# ---------------- FOOTER ----------------
st.markdown("""
<div class="footer">
    Made with ❤️ by BimaBuddy AI | Contact: support@bimabuddy.ai
</div>
""", unsafe_allow_html=True)
