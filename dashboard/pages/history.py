"""
Experiment History Page — US-9.4

Searchable, paginated table of all past experiments.
Each row has View (→ Results Dashboard) and Clone (→ Create Experiment wizard) actions.
"""
import json

import pandas as pd
import streamlit as st

from db.connection import get_connection
from dashboard.results import load_experiments_summary

_PAGE_SIZE = 10


def _load_all() -> pd.DataFrame:
    with get_connection() as conn:
        return load_experiments_summary(conn)


def show() -> None:
    st.markdown("## 📋 Experiment History")
    st.markdown("Browse, search, and manage all past experiments.")
    st.markdown("---")

    # ── Load data ─────────────────────────────────────────────────────────
    try:
        df = _load_all()
    except Exception as exc:
        st.error(f"Could not load experiments: {exc}")
        return

    if df.empty:
        st.info("No experiments recorded yet.", icon="🧪")
        if st.button("🚀 Create Your First Experiment", type="primary"):
            st.switch_page(st.session_state.pages["create"])
        return

    # ── Search ────────────────────────────────────────────────────────────
    search_col, _, count_col = st.columns([3, 2, 2])
    with search_col:
        query = st.text_input(
            "🔍 Search",
            placeholder="Filter by experiment name…",
            label_visibility="collapsed",
            key="history_search",
        )
    with count_col:
        st.markdown(
            f"<div style='text-align:right; padding-top:8px; color:#64748b'>"
            f"<strong>{len(df)}</strong> total experiments</div>",
            unsafe_allow_html=True,
        )

    # ── Filter ────────────────────────────────────────────────────────────
    if query:
        mask = df["name"].str.contains(query, case=False, na=False)
        df = df[mask].reset_index(drop=True)

    total_rows = len(df)
    if total_rows == 0:
        st.info(f"No experiments match **'{query}'**.")
        return

    # ── Pagination ────────────────────────────────────────────────────────
    if "history_page" not in st.session_state:
        st.session_state.history_page = 0

    total_pages = max(1, (total_rows + _PAGE_SIZE - 1) // _PAGE_SIZE)
    # Reset to page 0 if search changed
    if st.session_state.history_page >= total_pages:
        st.session_state.history_page = 0

    start = st.session_state.history_page * _PAGE_SIZE
    end = start + _PAGE_SIZE
    page_df = df.iloc[start:end].copy()

    # ── Table + row actions ───────────────────────────────────────────────
    st.markdown("---")

    # Column header row
    hdr = st.columns([3, 2, 2, 2, 2, 2, 2])
    for col, label in zip(hdr, ["Experiment", "Type", "Variant Col", "Metric Col", "Result", "p-value", "Actions"]):
        col.markdown(f"**{label}**")

    st.markdown('<hr style="margin:4px 0; border-color:#1e293b">', unsafe_allow_html=True)

    for _, row in page_df.iterrows():
        is_sig = bool(row["is_significant"])
        result_badge = (
            '<span style="color:#10b981;font-weight:600">✅ Significant</span>'
            if is_sig
            else '<span style="color:#f43f5e;font-weight:600">❌ Not Significant</span>'
        )
        p_fmt = f"{float(row['p_value']):.4f}"

        r_cols = st.columns([3, 2, 2, 2, 2, 2, 2])
        r_cols[0].markdown(f"**{row['name']}**")
        r_cols[1].markdown(row["metric_type"].title())
        r_cols[2].markdown(f"`{row['variant_column']}`")
        r_cols[3].markdown(f"`{row['metric_column']}`")
        r_cols[4].markdown(result_badge, unsafe_allow_html=True)
        r_cols[5].markdown(p_fmt)

        with r_cols[6]:
            view_key = f"view_{row['name']}_{_}"
            clone_key = f"clone_{row['name']}_{_}"
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("View", key=view_key, help="View full results dashboard"):
                    st.session_state["view_experiment"] = row["name"]
                    st.switch_page(st.session_state.pages["results"])
            with btn_col2:
                if st.button("Clone", key=clone_key, help="Copy this config into a new experiment"):
                    # Pre-populate wizard with this experiment's config
                    raw_summary = row.get("summary", "{}")
                    summary = json.loads(raw_summary) if isinstance(raw_summary, str) else {}
                    st.session_state["wizard"] = {
                        "step": 2,                          # skip to analysis type
                        "source_type": "existing",
                        "existing_dataset_id": row["dataset_id"],
                        "uploaded_bytes": None,
                        "uploaded_name": "",
                        "db_config": {},
                        "api_url": "",
                        "firecrawl_url": "",
                        "analysis_type": "ab",
                        "dataset_id": row["dataset_id"],
                        "df": None,
                        "columns": [],
                        "variant_col": row["variant_column"],
                        "metric_col": row["metric_column"],
                        "metric_type": row["metric_type"],
                        "target_col": None,
                        "task_type": None,
                        "exp_name": f"{row['name']} (copy)",
                        "result": None,
                        "executed": False,
                    }
                    st.switch_page(st.session_state.pages["create"])

        st.markdown('<hr style="margin:4px 0; border-color:#0f172a">', unsafe_allow_html=True)

    # ── Pagination controls ───────────────────────────────────────────────
    st.markdown("")
    pg_left, pg_mid, pg_right = st.columns([2, 3, 2])

    with pg_left:
        if st.button("← Previous", disabled=st.session_state.history_page == 0, key="hist_prev"):
            st.session_state.history_page -= 1
            st.rerun()

    with pg_mid:
        st.markdown(
            f"<div style='text-align:center; color:#64748b; padding-top:8px'>"
            f"Page <strong>{st.session_state.history_page + 1}</strong> of <strong>{total_pages}</strong> "
            f"({total_rows} results)</div>",
            unsafe_allow_html=True,
        )

    with pg_right:
        if st.button(
            "Next →",
            disabled=st.session_state.history_page >= total_pages - 1,
            key="hist_next",
        ):
            st.session_state.history_page += 1
            st.rerun()

    # ── New experiment CTA ────────────────────────────────────────────────
    st.markdown("---")
    _, cta_col, _ = st.columns([2, 3, 2])
    with cta_col:
        if st.button("🧪 Create New Experiment", type="primary", use_container_width=True, key="hist_cta"):
            st.switch_page(st.session_state.pages["create"])
