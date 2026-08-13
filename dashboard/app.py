"""
EaaS Platform Streamlit Dashboard -- US-6.1, US-6.2

Launch with: streamlit run dashboard/app.py
"""
import json
import os
import pandas as pd
import streamlit as st
from sqlalchemy import text

from db.connection import get_connection
from dashboard.stats import compute_summary_stats
from dashboard.results import (
    load_experiments_summary,
    load_predictions_summary,
    load_benchmarks_summary,
    create_ab_pvalue_chart,
    create_benchmark_chart,
)

st.set_page_config(page_title="EaaS Analytics Platform", layout="wide", page_icon="??")

st.title("?? EaaS (Experiment-as-a-Service) Analytics Platform")
st.markdown("### Self-Service Data Ingestion, A/B Testing & Machine Learning Dashboard")

st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select View",
    ["?? Descriptive Statistics", "?? A/B Testing Results", "?? ML Model Predictions", "? DB Query Benchmarks"]
)

# ---------------------------------------------------------------------------
# Page 1: Descriptive Statistics (US-6.1)
# ---------------------------------------------------------------------------
if page == "?? Descriptive Statistics":
    st.header("?? Dataset Descriptive Statistics (US-6.1)")

    try:
        with get_connection() as conn:
            query = text("SELECT DISTINCT dataset_id FROM clean_records")
            dataset_ids = [r[0] for r in conn.execute(query).fetchall()]

        if not dataset_ids:
            st.info("No records found in clean_records. Upload a CSV/Excel file or run a connector first.")
        else:
            selected_dataset = st.selectbox("Select Dataset ID", dataset_ids)
            with get_connection() as conn:
                res = conn.execute(text("SELECT fields FROM clean_records WHERE dataset_id = :ds"), {"ds": selected_dataset})
                rows = [json.loads(r[0]) for r in res.fetchall()]

            df_clean = pd.DataFrame(rows)
            st.subheader(f"Summary Metrics for Dataset: `{selected_dataset}` ({len(df_clean)} rows)")

            stats_df = compute_summary_stats(df_clean)
            st.dataframe(stats_df, use_container_width=True)

            st.subheader("Raw Data Sample")
            st.dataframe(df_clean.head(50), use_container_width=True)
    except Exception as exc:
        st.warning(f"Database connection error or no data: {exc}")

# ---------------------------------------------------------------------------
# Page 2: A/B Testing Results (US-6.2)
# ---------------------------------------------------------------------------
elif page == "?? A/B Testing Results":
    st.header("?? A/B Experiment Results (US-6.2)")

    try:
        with get_connection() as conn:
            exp_df = load_experiments_summary(conn)

        if exp_df.empty:
            st.info("No A/B experiments recorded yet.")
        else:
            fig = create_ab_pvalue_chart(exp_df)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Completed Experiments Table")
            st.dataframe(exp_df, use_container_width=True)
    except Exception as exc:
        st.warning(f"Error loading experiment results: {exc}")

# ---------------------------------------------------------------------------
# Page 3: ML Model Predictions (US-6.2)
# ---------------------------------------------------------------------------
elif page == "?? ML Model Predictions":
    st.header("?? ML Model Prediction Registry (US-6.2)")

    try:
        with get_connection() as conn:
            pred_df = load_predictions_summary(conn)

        if pred_df.empty:
            st.info("No trained models recorded in predictions table yet.")
        else:
            st.subheader("Trained Model Artifacts & Performance Metrics")
            st.dataframe(pred_df, use_container_width=True)
    except Exception as exc:
        st.warning(f"Error loading predictions: {exc}")

# ---------------------------------------------------------------------------
# Page 4: DB Query Benchmarks (US-3.1)
# ---------------------------------------------------------------------------
elif page == "? DB Query Benchmarks":
    st.header("? Database Query Performance Benchmarks (US-3.1)")

    try:
        with get_connection() as conn:
            bench_df = load_benchmarks_summary(conn)

        if bench_df.empty:
            st.info("No query benchmarks recorded yet. Run `python scripts/seed_and_benchmark.py` to populate.")
        else:
            fig = create_benchmark_chart(bench_df)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("EXPLAIN ANALYZE Benchmark Records")
            st.dataframe(bench_df, use_container_width=True)
    except Exception as exc:
        st.warning(f"Error loading benchmarks: {exc}")
