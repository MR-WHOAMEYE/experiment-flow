"""
Dashboard Results Data Loaders & Plotly Visualization Helpers -- US-6.2
"""
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from sqlalchemy.engine import Connection


def load_experiments_summary(conn: Connection) -> pd.DataFrame:
    """Load all experiment records from the experiments table."""
    query = text("SELECT name, dataset_id, variant_column, metric_column, metric_type, p_value, effect_size, is_significant, summary, created_at FROM experiments ORDER BY created_at DESC")
    res = conn.execute(query)
    rows = res.fetchall()
    cols = list(res.keys())
    return pd.DataFrame(rows, columns=cols)


def load_predictions_summary(conn: Connection) -> pd.DataFrame:
    """Load all prediction model records from the predictions table."""
    query = text("SELECT dataset_id, target_column, model_type, metrics, model_path, trained_at FROM predictions ORDER BY trained_at DESC")
    res = conn.execute(query)
    rows = res.fetchall()
    cols = list(res.keys())
    return pd.DataFrame(rows, columns=cols)


def load_benchmarks_summary(conn: Connection) -> pd.DataFrame:
    """Load all query optimization benchmarks from query_benchmarks table."""
    query = text("SELECT query_label, before_ms, after_ms, before_plan_cost, after_plan_cost, recorded_at FROM query_benchmarks ORDER BY recorded_at DESC")
    res = conn.execute(query)
    rows = res.fetchall()
    cols = list(res.keys())
    return pd.DataFrame(rows, columns=cols)


def create_ab_pvalue_chart(df: pd.DataFrame) -> go.Figure:
    """Create a bar chart showing A/B test p-values and significance threshold."""
    if df.empty:
        return go.Figure()

    fig = px.bar(
        df,
        x="name",
        y="p_value",
        color="is_significant",
        title="A/B Experiment p-values (Red Line = p=0.05 Significance Floor)",
        labels={"name": "Experiment Name", "p_value": "p-value", "is_significant": "Significant (p < 0.05)"},
        color_discrete_map={True: "#2ecc71", False: "#e74c3c"},
    )
    fig.add_hline(y=0.05, line_dash="dash", line_color="red", annotation_text="p = 0.05 Floor")
    return fig


def create_benchmark_chart(df: pd.DataFrame) -> go.Figure:
    """Create a grouped bar chart comparing Before vs After query execution times (ms)."""
    if df.empty:
        return go.Figure()

    fig = go.Figure(data=[
        go.Bar(name="Before Index (ms)", x=df["query_label"], y=df["before_ms"], marker_color="#e74c3c"),
        go.Bar(name="After Index (ms)", x=df["query_label"], y=df["after_ms"], marker_color="#2ecc71"),
    ])
    fig.update_layout(
        barmode="group",
        title="Database Query Performance Improvement (EXPLAIN ANALYZE)",
        xaxis_title="Query Benchmark",
        yaxis_title="Execution Time (ms)",
    )
    return fig
