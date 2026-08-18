"""
Home Page — US-9.1

Landing page: hero section, summary metric cards, and the 5 most recent experiments.
"""
import streamlit as st
import pandas as pd

from db.connection import get_connection
from dashboard.results import load_experiments_summary


def show() -> None:
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-section">
        <div class="hero-eyebrow">🔬 Experiment Flow</div>
        <div class="hero-title">Unified A/B Testing &amp;<br>Prediction Platform</div>
        <div class="hero-sub">
            Run experiments, train ML models, and get results automatically—all in one place.<br>
            No code required. No SQL. No jargon.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA ───────────────────────────────────────────────────────────────────
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if st.button(
            "🚀  Create New Experiment",
            type="primary",
            use_container_width=True,
            key="home_cta",
        ):
            st.switch_page(st.session_state.pages["create"])

    st.markdown(
        "<div style='text-align:center; color:#475569; margin:12px 0 32px; font-size:0.9rem'>"
        "or browse past experiments below ↓</div>",
        unsafe_allow_html=True,
    )

    # ── Stats row ─────────────────────────────────────────────────────────────
    try:
        with get_connection() as conn:
            exp_df = load_experiments_summary(conn)

        total = len(exp_df)
        significant = int(exp_df["is_significant"].sum()) if not exp_df.empty else 0
        avg_effect = float(exp_df["effect_size"].mean()) if not exp_df.empty else 0.0
        ab_count = int((exp_df["metric_type"] == "numeric").sum()) if not exp_df.empty else 0

        c1, c2, c3, c4 = st.columns(4)
        metrics = [
            (c1, "Total Experiments", str(total), "#6366f1"),
            (c2, "Significant Results", str(significant), "#10b981"),
            (c3, "Avg Effect Size", f"{avg_effect:.3f}", "#818cf8"),
            (c4, "Numeric A/B Tests", str(ab_count), "#06b6d4"),
        ]
        for col, label, value, color in metrics:
            col.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-value" style="color:{color}">{value}</div>'
                f'<div class="metric-label">{label}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── Recent Experiments ─────────────────────────────────────────────
        st.markdown("### 🕐 Recent Experiments")

        if exp_df.empty:
            st.info(
                "No experiments yet. Click **Create New Experiment** above to get started!",
                icon="🧪",
            )
        else:
            recent = exp_df.head(5).copy()

            def _result_badge(row):
                if row["is_significant"]:
                    return "✅ Significant"
                return "❌ Not Significant"

            recent["Result"] = recent.apply(_result_badge, axis=1)
            recent["p-value"] = recent["p_value"].round(4)
            recent["Effect"] = recent["effect_size"].round(3)
            recent["Type"] = recent["metric_type"].str.title()

            display = recent[
                ["name", "Type", "variant_column", "metric_column", "Result", "p-value", "Effect", "created_at"]
            ].rename(
                columns={
                    "name": "Experiment",
                    "variant_column": "Variant Col",
                    "metric_column": "Metric Col",
                    "created_at": "Created",
                }
            )
            st.dataframe(display, use_container_width=True, hide_index=True)

            st.markdown("")
            _, col_btn, _ = st.columns([3, 2, 3])
            with col_btn:
                if st.button("📋  View All Experiments →", use_container_width=True, key="home_history"):
                    st.switch_page(st.session_state.pages["history"])

    except Exception as exc:
        st.info(
            "Connect a database to see experiment history. Create your first experiment above!",
            icon="💡",
        )
        with st.expander("Technical details"):
            st.caption(str(exc))
