import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from backend.pipeline import process_policy   # ✅ NEW (IMPORTANT)

st.set_page_config(
    page_title="BimaBuddy AI — Insurance Policy Analyzer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* (same CSS as before — untouched) */
</style>
""", unsafe_allow_html=True)


# ---------------- UTILS ----------------

def fmt_inr(value):
    if value is None:
        return "N/A"
    try:
        return f"₹{float(value):,.0f}"
    except:
        return "N/A"

def fmt_pct(value, decimals=2):
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}%"
    except:
        return "N/A"

def draw_card(title, value, subtext="", highlight=False, tooltip=""):
    hl_class = " highlight" if highlight else ""
    st.markdown(f"""
    <div class="fin-card{hl_class}">
        <div class="fin-card-title">{title}</div>
        <div class="fin-card-value">{value}</div>
        <div class="fin-card-sub">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------- RESULT UI ----------------

def render_result(data: dict) -> None:
    st.success("✅ Analysis Completed")

    st.write(data)  # (you can later replace with your full UI)


# ---------------- MAIN ----------------

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
    )

    if st.button("🔍 Analyze Policy", use_container_width=True):
        if not uploaded:
            st.warning("Please upload a PDF file first.")
            return

        with st.spinner("Analyzing your policy..."):
            try:
                result = process_policy(uploaded)   # ✅ DIRECT CALL
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
                return

        if result is None:
            st.error("No result returned.")
            return

        render_result(result)


if __name__ == "__main__":
    main()
