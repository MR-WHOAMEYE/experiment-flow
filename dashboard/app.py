"""
EaaS Platform Streamlit Dashboard -- US-6.1, US-6.2, US-8.1, US-8.2

Launch with: streamlit run dashboard/app.py
"""
import json
import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import text

# Ensure repository root is on sys.path when running via `streamlit run dashboard/app.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.connection import get_connection
from dashboard.stats import compute_summary_stats
from dashboard.results import (
    load_experiments_summary,
    load_predictions_summary,
    load_benchmarks_summary,
    create_ab_pvalue_chart,
    create_benchmark_chart,
)
from dashboard.narrative import generate_ab_narrative, generate_ml_narrative
from ab_testing.config import ExperimentConfig
from ab_testing.engine import evaluate_experiment, save_experiment_result
from ml.trainer import train_model, save_prediction_metadata

st.set_page_config(page_title="EaaS Analytics Platform", layout="wide", page_icon="??")

st.title("?? EaaS (Experiment-as-a-Service) Analytics Platform")
st.markdown("### Self-Service Data Ingestion, A/B Testing & Machine Learning Dashboard")

st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select View",
    [
        "?? Descriptive Statistics",
        "?? A/B Testing Results",
        "? Create A/B Experiment",
        "?? ML Model Predictions",
        "? DB Query Benchmarks"
    ]
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
# Page 2: A/B Testing Results & Plain Language Summaries (US-6.2, US-8.2)
# ---------------------------------------------------------------------------
elif page == "?? A/B Testing Results":
    st.header("?? A/B Experiment Results & Plain-Language Summaries (US-6.2, US-8.2)")

    try:
        with get_connection() as conn:
            exp_df = load_experiments_summary(conn)

        if exp_df.empty:
            st.info("No A/B experiments recorded yet. Use 'Create A/B Experiment' tab to launch one.")
        else:
            fig = create_ab_pvalue_chart(exp_df)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Plain-Language Results Summaries (US-8.2)")
            for _idx, row in exp_df.iterrows():
                with st.expander(f"Experiment: {row['name']} (p = {row['p_value']:.4f})"):
                    summary_dict = json.loads(row["summary"]) if isinstance(row["summary"], str) else (row["summary"] or {})
                    narrative_text = generate_ab_narrative(
                        experiment_name=row["name"],
                        variant_col=row["variant_column"],
                        metric_col=row["metric_column"],
                        p_value=float(row["p_value"]),
                        is_significant=bool(row["is_significant"]),
                        effect_size=float(row["effect_size"]),
                        test_type=summary_dict.get("test_type", "t-test"),
                        summary_stats=summary_dict.get("summary_stats"),
                    )
                    st.markdown(narrative_text)

            st.subheader("Completed Experiments Table")
            st.dataframe(exp_df, use_container_width=True)
    except Exception as exc:
        st.warning(f"Error loading experiment results: {exc}")

# ---------------------------------------------------------------------------
# Page 3: Interactive A/B Experiment Creation (US-8.1)
# ---------------------------------------------------------------------------
elif page == "? Create A/B Experiment":
    st.header("? Form-Driven A/B Experiment Creation (US-8.1)")
    st.markdown("Configure and execute an A/B experiment without writing code.")

    try:
        with get_connection() as conn:
            query = text("SELECT DISTINCT dataset_id FROM clean_records")
            dataset_ids = [r[0] for r in conn.execute(query).fetchall()]

        if not dataset_ids:
            st.info("No datasets available. Please upload a dataset first.")
        else:
            with st.form("ab_create_form"):
                selected_ds = st.selectbox("Select Dataset", dataset_ids)
                exp_name = st.text_input("Experiment Name", value="New A/B Test")

                # Fetch columns
                with get_connection() as conn:
                    res = conn.execute(text("SELECT fields FROM clean_records WHERE dataset_id = :ds LIMIT 10"), {"ds": selected_ds})
                    rows = [json.loads(r[0]) for r in res.fetchall()]
                df_sample = pd.DataFrame(rows)
                all_cols = list(df_sample.columns)

                variant_col = st.selectbox("Variant Column (Group Labels)", all_cols)
                metric_col = st.selectbox("Metric Column (To Measure)", all_cols)
                metric_type = st.selectbox("Metric Type", ["numeric", "categorical"])

                submitted = st.form_submit_button("?? Run Experiment")

                if submitted:
                    with get_connection() as conn:
                        res = conn.execute(text("SELECT fields FROM clean_records WHERE dataset_id = :ds"), {"ds": selected_ds})
                        df_full = pd.DataFrame([json.loads(r[0]) for r in res.fetchall()])

                        cfg = ExperimentConfig(
                            dataset_id=selected_ds,
                            name=exp_name,
                            variant_column=variant_col,
                            metric_column=metric_col,
                            metric_type=metric_type,
                        )
                        eval_res = evaluate_experiment(cfg, df_full)
                        save_experiment_result(conn, eval_res)

                        st.success(f"Experiment '{exp_name}' executed and saved successfully!")
                        st.subheader("Instant Plain-Language Summary")
                        st.markdown(
                            generate_ab_narrative(
                                experiment_name=exp_name,
                                variant_col=variant_col,
                                metric_col=metric_col,
                                p_value=eval_res.p_value,
                                is_significant=eval_res.is_significant,
                                effect_size=eval_res.effect_size,
                                test_type=eval_res.test_type,
                                summary_stats=eval_res.summary_stats,
                            )
                        )
    except Exception as exc:
        st.error(f"Error executing experiment form: {exc}")

# ---------------------------------------------------------------------------
# Page 4: ML Model Predictions & Summaries (US-6.2, US-8.2)
# ---------------------------------------------------------------------------
elif page == "?? ML Model Predictions":
    st.header("?? ML Model Prediction Registry & Narratives (US-6.2, US-8.2)")

    try:
        with get_connection() as conn:
            pred_df = load_predictions_summary(conn)

        if pred_df.empty:
            st.info("No trained models recorded in predictions table yet.")
        else:
            st.subheader("Model Plain-Language Quality Summaries (US-8.2)")
            for _idx, row in pred_df.iterrows():
                metrics_dict = json.loads(row["metrics"]) if isinstance(row["metrics"], str) else (row["metrics"] or {})
                with st.expander(f"Model: {row['target_column']} ({row['model_type'].upper()})"):
                    st.markdown(
                        generate_ml_narrative(
                            target_col=row["target_column"],
                            model_type=row["model_type"],
                            metrics=metrics_dict,
                        )
                    )

            st.subheader("Trained Model Artifacts Table")
            st.dataframe(pred_df, use_container_width=True)
    except Exception as exc:
        st.warning(f"Error loading predictions: {exc}")

# ---------------------------------------------------------------------------
# Page 5: DB Query Benchmarks (US-3.1)
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
