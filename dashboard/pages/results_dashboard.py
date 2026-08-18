"""
Results Dashboard — US-9.3

Loads a completed experiment by name (from st.session_state["view_experiment"])
and renders: plain-language verdict, metric cards, Plotly charts, and diagnostics.
"""
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text as sqla_text

from db.connection import get_connection
from dashboard.results import load_experiments_summary, load_predictions_summary
from dashboard.narrative import generate_ab_narrative, generate_ml_narrative


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_experiment(name: str) -> dict | None:
    """Return a single experiment row as a dict, or None if not found."""
    try:
        with get_connection() as conn:
            df = load_experiments_summary(conn)
        if df.empty:
            return None
        row = df[df["name"] == name]
        return row.iloc[0].to_dict() if not row.empty else None
    except Exception:
        return None


def _parse_summary(raw) -> dict:
    """Safely parse the JSON summary field."""
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    if isinstance(raw, dict):
        return raw
    return {}


def _variant_bar_chart(summary: dict, variant_col: str, metric_col: str) -> go.Figure | None:
    """Build a bar chart of per-variant means from summary_stats."""
    ss = summary.get("summary_stats", {})
    keys = [k for k in ss if k.endswith("_mean")]
    if len(keys) < 2:
        return None

    labels = [k.replace("_mean", "") for k in keys]
    values = [ss[k] for k in keys]

    colors = ["#6366f1", "#10b981", "#f59e0b", "#f43f5e"]
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors[: len(labels)],
            text=[f"{v:.3f}" for v in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=f"Mean {metric_col} by {variant_col}",
        xaxis_title=variant_col,
        yaxis_title=f"Mean {metric_col}",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        showlegend=False,
        margin=dict(t=60, b=40),
    )
    return fig


def _ci_chart(summary: dict, metric_col: str) -> go.Figure | None:
    """Build a 95% confidence interval visualisation for the mean difference."""
    ci = summary.get("confidence_interval")
    mean_diff = summary.get("summary_stats", {}).get("mean_difference")
    if ci is None or mean_diff is None:
        return None

    lo, hi = ci
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[lo, hi],
            y=["95% CI", "95% CI"],
            mode="lines",
            line=dict(color="#6366f1", width=4),
            name="95% CI",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[mean_diff],
            y=["95% CI"],
            mode="markers",
            marker=dict(size=14, color="#10b981"),
            name=f"Mean diff = {mean_diff:.3f}",
        )
    )
    fig.add_vline(x=0, line_dash="dash", line_color="#f43f5e", annotation_text="No effect (0)")
    fig.update_layout(
        title=f"95% Confidence Interval for Mean Difference in {metric_col}",
        xaxis_title="Mean Difference (Variant B − Variant A)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        margin=dict(t=60, b=40),
        height=200,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def show() -> None:
    experiment_name: str | None = st.session_state.get("view_experiment")

    # ── No experiment selected ─────────────────────────────────────────────
    if not experiment_name:
        st.markdown("## 📊 Results Dashboard")
        st.markdown("---")
        st.info(
            "No experiment selected. Run a new experiment or pick one from History.",
            icon="📋",
        )
        col_l, col_r = st.columns(2)
        with col_l:
            if st.button("🧪 Create New Experiment", type="primary", use_container_width=True):
                st.switch_page(st.session_state.pages["create"])
        with col_r:
            if st.button("📋 View History", use_container_width=True):
                st.switch_page(st.session_state.pages["history"])
        return

    # ── Load ──────────────────────────────────────────────────────────────
    with st.spinner("Loading results…"):
        exp = _load_experiment(experiment_name)

    if exp is None:
        st.error(f"Experiment **'{experiment_name}'** not found in the database.")
        if st.button("← Back to History"):
            st.switch_page(st.session_state.pages["history"])
        return

    summary = _parse_summary(exp.get("summary"))

    p_val = float(exp["p_value"])
    effect = float(exp["effect_size"])
    is_sig = bool(exp["is_significant"])
    test_type = summary.get("test_type", "t-test")

    # ── Header ────────────────────────────────────────────────────────────
    hdr_col, btn_col = st.columns([5, 1])
    with hdr_col:
        st.markdown(f"## 📊 {experiment_name}")
        st.caption(
            f"A/B Test · Variant: `{exp['variant_column']}` → Metric: `{exp['metric_column']}` "
            f"· Created: {str(exp.get('created_at', ''))[:10]}"
        )
    with btn_col:
        if st.button("↩ History", key="res_back"):
            st.switch_page(st.session_state.pages["history"])

    # ── Verdict ───────────────────────────────────────────────────────────
    verdict_cls = "verdict-win" if is_sig else "verdict-lose"
    verdict_icon = "✅" if is_sig else "❌"
    verdict_text = "Statistically Significant!" if is_sig else "Not Statistically Significant"
    threshold_note = "p < 0.05 — we are confident this difference is real." if is_sig else "p ≥ 0.05 — the difference could be due to chance."

    st.markdown(
        f'<div class="{verdict_cls}">'
        f'<span style="font-size:2rem">{verdict_icon}</span>'
        f'<strong style="font-size:1.35rem; margin-left:16px">{verdict_text}</strong><br>'
        f'<span style="color:#94a3b8; font-size:0.92rem; margin-left:56px">{threshold_note}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # Plain-language narrative
    narrative = generate_ab_narrative(
        experiment_name=experiment_name,
        variant_col=exp["variant_column"],
        metric_col=exp["metric_column"],
        p_value=p_val,
        is_significant=is_sig,
        effect_size=effect,
        test_type=test_type,
        summary_stats=summary.get("summary_stats"),
    )
    st.markdown(narrative)

    # ── Metric cards ──────────────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    sig_color = "#10b981" if is_sig else "#f43f5e"
    cards = [
        (c1, f"{p_val:.4f}", "p-value", "#6366f1"),
        (c2, "Yes" if is_sig else "No", "Significant", sig_color),
        (c3, f"{effect:.3f}", "Effect Size", "#818cf8"),
        (c4, test_type.title(), "Statistical Test", "#06b6d4"),
    ]
    for col, val, label, color in cards:
        col.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color:{color}">{val}</div>'
            f'<div class="metric-label">{label}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Charts ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📈 Charts")

    bar_fig = _variant_bar_chart(summary, exp["variant_column"], exp["metric_column"])
    ci_fig = _ci_chart(summary, exp["metric_column"])

    if bar_fig or ci_fig:
        chart_cols = st.columns(2 if (bar_fig and ci_fig) else 1)
        if bar_fig:
            with chart_cols[0]:
                st.plotly_chart(bar_fig, use_container_width=True)
        if ci_fig:
            with chart_cols[-1]:
                st.plotly_chart(ci_fig, use_container_width=True)
    else:
        st.info("Chart data not available for this experiment (summary statistics not stored).")

    # ── Diagnostics ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔬 Diagnostics")

    ss = summary.get("summary_stats", {})
    diag_rows = {
        "Statistical Test": test_type.title(),
        "p-value": f"{p_val:.6f}",
        "Effect Size (Cohen's d / Cramér's V)": f"{effect:.4f}",
        "Significant at 95% confidence": "Yes ✓" if is_sig else "No ✗",
    }
    if summary.get("confidence_interval"):
        lo, hi = summary["confidence_interval"]
        diag_rows["95% Confidence Interval"] = f"[{lo:.3f}, {hi:.3f}]"
    if ss.get("mean_difference") is not None:
        diag_rows["Mean Difference (B − A)"] = f"{ss['mean_difference']:.4f}"

    for k, v in diag_rows.items():
        col_k, col_v = st.columns([2, 3])
        col_k.markdown(f"**{k}**")
        col_v.markdown(v)

    # ── Raw summary data ───────────────────────────────────────────────────
    with st.expander("🗃️ Raw Summary Data (JSON)"):
        st.json(summary)

    st.markdown("---")
    c_hist, c_new = st.columns(2)
    with c_hist:
        if st.button("← Back to All Experiments", use_container_width=True):
            st.switch_page(st.session_state.pages["history"])
    with c_new:
        if st.button("🧪 Run Another Experiment", type="primary", use_container_width=True):
            st.session_state.pop("view_experiment", None)
            st.switch_page(st.session_state.pages["create"])
