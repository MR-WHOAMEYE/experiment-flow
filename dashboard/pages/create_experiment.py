"""
Create Experiment Wizard — US-9.2

4-step multi-step form:
  Step 1  Choose Data Source
  Step 2  Choose Analysis Type
  Step 3  Configure (conditional — skipped for EDA-only)
  Step 4  Review & Create → execute backend → show narrative
"""
from __future__ import annotations

import io
import json
import uuid

import pandas as pd
import streamlit as st
from sqlalchemy import text as sqla_text

from db.connection import get_connection
from cleaning.cleaner import clean
from ab_testing.config import ExperimentConfig
from ab_testing.engine import evaluate_experiment, save_experiment_result
from ml.trainer import train_model, save_prediction_metadata
from dashboard.narrative import generate_ab_narrative, generate_ml_narrative


# ─────────────────────────────────────────────────────────────────────────────
# Session-state helpers
# ─────────────────────────────────────────────────────────────────────────────

_WIZARD_DEFAULTS: dict = {
    "step": 1,
    "source_type": None,
    "uploaded_bytes": None,
    "uploaded_name": "",
    "db_config": {},
    "api_url": "",
    "firecrawl_url": "",
    "firecrawl_crawl": False,
    "firecrawl_limit": 10,
    "existing_dataset_id": None,
    "analysis_type": None,
    "dataset_id": None,
    "df": None,
    "columns": [],
    "variant_col": None,
    "metric_col": None,
    "metric_type": None,
    "target_col": None,
    "task_type": None,
    "exp_name": "",
    "result": None,
    "ml_result": None,
    "executed": False,
    "error": None,
}


def _init():
    if "wizard" not in st.session_state:
        st.session_state.wizard = dict(_WIZARD_DEFAULTS)
    # Ensure all keys exist (forward-compat for cloned wizards from History)
    for k, v in _WIZARD_DEFAULTS.items():
        st.session_state.wizard.setdefault(k, v)


def _reset():
    st.session_state.wizard = dict(_WIZARD_DEFAULTS)
    st.session_state.wizard["exp_name"] = f"Experiment-{pd.Timestamp.now().strftime('%Y%m%d-%H%M')}"


# ─────────────────────────────────────────────────────────────────────────────
# Progress bar
# ─────────────────────────────────────────────────────────────────────────────

def _progress_bar(step: int) -> None:
    steps = ["Data Source", "Analysis Type", "Configure", "Review & Create"]
    cols = st.columns(len(steps) * 2 - 1)

    for i, label in enumerate(steps):
        ci = i * 2
        if i + 1 < step:
            dot_bg, dot_text, label_color = "#10b981", "✓", "#10b981"
        elif i + 1 == step:
            dot_bg, dot_text, label_color = "#6366f1", str(i + 1), "#e2e8f0"
        else:
            dot_bg, dot_text, label_color = "#1e293b", str(i + 1), "#475569"

        cols[ci].markdown(
            f"<div style='text-align:center'>"
            f"<div style='width:32px;height:32px;border-radius:50%;background:{dot_bg};"
            f"display:flex;align-items:center;justify-content:center;color:white;font-weight:600;"
            f"font-size:0.82rem;margin:0 auto 6px'>{dot_text}</div>"
            f"<div style='font-size:0.72rem;color:{label_color};white-space:nowrap'>{label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if i < len(steps) - 1:
            line_color = "#10b981" if step > i + 1 else "#1e293b"
            cols[ci + 1].markdown(
                f"<div style='height:2px;background:{line_color};margin-top:15px'></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Data Source
# ─────────────────────────────────────────────────────────────────────────────

_SOURCE_LABELS = {
    "csv": "📁 Upload CSV file",
    "excel": "📊 Upload Excel file",
    "existing": "🗄️ Use existing dataset from database",
    "postgres": "🐘 Connect to PostgreSQL",
    "mysql": "🐬 Connect to MySQL",
    "api": "🌐 Enter API endpoint",
    "firecrawl": "🕷️ Scrape a URL (via Firecrawl)",
}


def _step1(w: dict) -> None:
    st.markdown("#### Where is your data?")

    options = list(_SOURCE_LABELS.values())
    codes = list(_SOURCE_LABELS.keys())
    current_idx = codes.index(w["source_type"]) if w["source_type"] in codes else 0

    selected_label = st.radio(
        "source",
        options,
        index=current_idx,
        label_visibility="collapsed",
        key="s1_radio",
    )
    src = codes[options.index(selected_label)]

    uploaded_file = None

    # ── CSV / Excel upload ────────────────────────────────────────────────
    if src in ("csv", "excel"):
        ext = "csv" if src == "csv" else "xlsx"
        uploaded_file = st.file_uploader(
            f"Drop or click to select a .{ext.upper()} file",
            type=[ext],
            key=f"s1_upload_{src}",
        )
        if uploaded_file:
            st.success(f"✓ **{uploaded_file.name}** ready  ({uploaded_file.size:,} bytes)")

    # ── Existing dataset ──────────────────────────────────────────────────
    elif src == "existing":
        try:
            with get_connection() as conn:
                ids = [r[0] for r in conn.execute(sqla_text(
                    "SELECT DISTINCT dataset_id FROM clean_records")).fetchall()]
            if ids:
                sel = st.selectbox("Choose existing dataset", ids, key="s1_existing_sel",
                                   index=ids.index(w["existing_dataset_id"]) if w["existing_dataset_id"] in ids else 0)
                w["existing_dataset_id"] = sel
                st.success(f"✓ Dataset `{sel}` selected.")
            else:
                st.warning("No datasets in the database yet. Upload a CSV instead.")
                src = "csv"
        except Exception as exc:
            st.error(f"Database unavailable: {exc}")

    # ── PostgreSQL ────────────────────────────────────────────────────────
    elif src == "postgres":
        st.markdown("**PostgreSQL connection**")
        c1, c2 = st.columns(2)
        host = c1.text_input("Host", value=w["db_config"].get("host", "localhost"), key="s1_pg_host")
        port = c2.text_input("Port", value=str(w["db_config"].get("port", 5432)), key="s1_pg_port")
        c3, c4 = st.columns(2)
        user = c3.text_input("Username", value=w["db_config"].get("user", ""), key="s1_pg_user")
        pwd = c4.text_input("Password", type="password", key="s1_pg_pwd")
        dbname = st.text_input("Database", value=w["db_config"].get("dbname", ""), key="s1_pg_db")
        query_sql = st.text_area("SQL Query", value=w["db_config"].get("query", "SELECT * FROM your_table LIMIT 1000"), key="s1_pg_q")
        if st.button("🔌 Test Connection", key="s1_pg_test"):
            with st.spinner("Connecting…"):
                try:
                    from ingestion.connectors.postgres_connector import PostgresConnector
                    ok = PostgresConnector(host=host, port=int(port), user=user,
                                          password=pwd, dbname=dbname).test_connection()
                    (st.success if ok else st.error)(
                        "✓ Connection successful!" if ok else "✗ Connection failed. Check credentials."
                    )
                except Exception as e:
                    st.error(f"✗ {e}")
        w["db_config"] = {"host": host, "port": port, "user": user, "password": pwd, "dbname": dbname, "query": query_sql}

    # ── MySQL ─────────────────────────────────────────────────────────────
    elif src == "mysql":
        st.markdown("**MySQL connection**")
        c1, c2 = st.columns(2)
        host = c1.text_input("Host", value=w["db_config"].get("host", "localhost"), key="s1_my_host")
        port = c2.text_input("Port", value=str(w["db_config"].get("port", 3306)), key="s1_my_port")
        c3, c4 = st.columns(2)
        user = c3.text_input("Username", key="s1_my_user")
        pwd = c4.text_input("Password", type="password", key="s1_my_pwd")
        dbname = st.text_input("Database", key="s1_my_db")
        if st.button("🔌 Test Connection", key="s1_my_test"):
            st.info("MySQL connection test will use credentials from .env or the fields above.")
        w["db_config"] = {"host": host, "port": port, "user": user, "password": pwd, "dbname": dbname}

    # ── REST API ──────────────────────────────────────────────────────────
    elif src == "api":
        w["api_url"] = st.text_input(
            "API Endpoint URL",
            value=w.get("api_url", ""),
            placeholder="https://api.example.com/data.json",
            key="s1_api_url",
        )
        st.caption("The endpoint must return a JSON array of objects (records).")

    # ── Firecrawl ─────────────────────────────────────────────────────────
    elif src == "firecrawl":
        w["firecrawl_url"] = st.text_input(
            "Website URL to scrape",
            value=w.get("firecrawl_url", ""),
            placeholder="https://example.com",
            key="s1_fc_url",
        )
        crawl = st.checkbox("Crawl entire site (not just this page)", value=w.get("firecrawl_crawl", False), key="s1_fc_crawl")
        limit = st.slider("Max pages to crawl", 1, 50, w.get("firecrawl_limit", 10), key="s1_fc_limit") if crawl else 1
        w["firecrawl_crawl"] = crawl
        w["firecrawl_limit"] = limit
        st.caption("Requires `FIRECRAWL_API_KEY` set in `.env`.")

    # ── Nav ───────────────────────────────────────────────────────────────
    st.markdown("")
    c_cancel, _, c_next = st.columns([1, 5, 1])
    with c_cancel:
        if st.button("Cancel", key="s1_cancel"):
            _reset()
            st.switch_page(st.session_state.pages["home"])
    with c_next:
        if st.button("Next →", type="primary", key="s1_next"):
            # Validation
            if src in ("csv", "excel") and uploaded_file is None:
                st.error("Please upload a file before proceeding.")
                return
            if src == "api" and not w.get("api_url", "").strip():
                st.error("Please enter an API URL.")
                return
            if src == "firecrawl" and not w.get("firecrawl_url", "").strip():
                st.error("Please enter a URL to scrape.")
                return
            if src == "existing" and not w.get("existing_dataset_id"):
                st.error("Please select a dataset.")
                return

            w["source_type"] = src
            if uploaded_file is not None:
                w["uploaded_bytes"] = uploaded_file.getvalue()
                w["uploaded_name"] = uploaded_file.name
            w["columns"] = []   # reset columns so step 3 reloads them
            w["step"] = 2
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Analysis Type
# ─────────────────────────────────────────────────────────────────────────────

_ANALYSIS_OPTS = {
    "🔍 Data Cleaning & EDA only": ("eda",
        "Clean your data and explore descriptive statistics. No experiment configuration needed."),
    "🧪 A/B Testing": ("ab",
        "Compare two or more variants with statistical tests (t-test or chi-square). We'll tell you if the difference is real."),
    "🤖 ML Prediction": ("ml",
        "Train a machine learning model to predict a target column — works for numeric and categorical targets."),
    "⚡ All of the above": ("all",
        "Clean data, run an A/B test, AND train an ML model — all in one go."),
}


def _step2(w: dict) -> None:
    st.markdown("#### What do you want to analyze?")

    current = next((label for label, (code, _) in _ANALYSIS_OPTS.items() if code == w["analysis_type"]), None)

    selected = st.radio(
        "analysis",
        list(_ANALYSIS_OPTS.keys()),
        index=list(_ANALYSIS_OPTS.keys()).index(current) if current else 1,
        label_visibility="collapsed",
        key="s2_radio",
    )
    code, description = _ANALYSIS_OPTS[selected]
    st.info(f"ℹ️  {description}")

    st.markdown("")
    c_back, _, c_next = st.columns([1, 5, 1])
    with c_back:
        if st.button("← Back", key="s2_back"):
            w["step"] = 1
            st.rerun()
    with c_next:
        if st.button("Next →", type="primary", key="s2_next"):
            w["analysis_type"] = code
            w["step"] = 3 if code != "eda" else 4
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Configure
# ─────────────────────────────────────────────────────────────────────────────

def _load_columns(w: dict) -> list[str]:
    """Derive column list from whatever data source was chosen."""
    src = w.get("source_type", "")

    if src in ("csv", "excel") and w.get("uploaded_bytes"):
        buf = io.BytesIO(w["uploaded_bytes"])
        df = pd.read_csv(buf) if src == "csv" else pd.read_excel(buf)
        w["df"] = df
        return list(df.columns)

    if src == "existing" and w.get("existing_dataset_id"):
        try:
            with get_connection() as conn:
                rows = [
                    json.loads(r[0])
                    for r in conn.execute(
                        sqla_text("SELECT fields FROM clean_records WHERE dataset_id = :ds LIMIT 10"),
                        {"ds": w["existing_dataset_id"]},
                    ).fetchall()
                ]
            if rows:
                df = pd.DataFrame(rows)
                w["df"] = df
                w["dataset_id"] = w["existing_dataset_id"]
                return list(df.columns)
        except Exception:
            pass

    if src == "api" and w.get("api_url", "").strip():
        try:
            import requests as _req
            resp = _req.get(w["api_url"], timeout=15)
            data = resp.json()
            if isinstance(data, list) and data:
                df = pd.DataFrame(data)
                w["df"] = df
                return list(df.columns)
        except Exception:
            pass

    return []


def _infer_type(w: dict, col: str) -> str | None:
    """Return 'numeric' | 'categorical' | None based on the loaded df."""
    df = w.get("df")
    if df is None or col not in df.columns:
        return None
    return "numeric" if pd.api.types.is_numeric_dtype(df[col]) else "categorical"


def _step3(w: dict) -> None:
    analysis = w["analysis_type"]

    # Lazy-load columns
    if not w.get("columns"):
        with st.spinner("Reading your data…"):
            w["columns"] = _load_columns(w)

    cols = w["columns"]
    if not cols:
        st.error(
            "Could not read column names from your data source. "
            "Go back and verify your file / connection."
        )
        if st.button("← Back", key="s3_err_back"):
            w["step"] = 2
            st.rerun()
        return

    # ── A/B config ────────────────────────────────────────────────────────
    if analysis in ("ab", "all"):
        st.markdown("#### Configure Your A/B Test")

        v_idx = cols.index(w["variant_col"]) if w.get("variant_col") in cols else 0
        m_idx = cols.index(w["metric_col"]) if w.get("metric_col") in cols else min(1, len(cols) - 1)

        variant_col = st.selectbox(
            "Which column contains your **variants** (the group labels)?",
            cols, index=v_idx, key="s3_variant",
        )
        metric_col = st.selectbox(
            "Which column is your **success metric** (what you're measuring)?",
            cols, index=m_idx, key="s3_metric",
        )

        inferred = _infer_type(w, metric_col)
        if inferred == "numeric":
            metric_type = "numeric"
            st.markdown("""
            <div class="verdict-win" style="padding:14px 18px">
                📐 <strong>We'll use a t-test</strong> — because <em>{col}</em> is a <strong>numeric</strong> column.
                We'll compare average values between your variants.
            </div>""".replace("{col}", metric_col), unsafe_allow_html=True)
        elif inferred == "categorical":
            metric_type = "categorical"
            st.markdown("""
            <div class="verdict-lose" style="padding:14px 18px">
                📊 <strong>We'll use a chi-square test</strong> — because <em>{col}</em> is a <strong>categorical</strong> column.
                We'll compare the distribution of outcomes between your variants.
            </div>""".replace("{col}", metric_col), unsafe_allow_html=True)
        else:
            choice = st.radio(
                "Metric type (couldn't auto-detect — please choose):",
                ["Numeric  →  t-test will be used", "Categorical  →  chi-square will be used"],
                key="s3_mt_manual",
            )
            metric_type = "numeric" if "Numeric" in choice else "categorical"

        w["variant_col"] = variant_col
        w["metric_col"] = metric_col
        w["metric_type"] = metric_type

    # ── ML config ─────────────────────────────────────────────────────────
    if analysis in ("ml", "all"):
        if analysis == "all":
            st.markdown("---")
        st.markdown("#### Configure Your ML Model")

        t_idx = cols.index(w["target_col"]) if w.get("target_col") in cols else 0
        target_col = st.selectbox(
            "Which column do you want to **predict**?",
            cols, index=t_idx, key="s3_target",
        )

        t_type = _infer_type(w, target_col)
        if t_type == "numeric":
            task_type = "regression"
            st.markdown("""
            <div class="verdict-win" style="padding:14px 18px">
                📈 <strong>Regression model</strong> — we'll predict numeric values
                and report RMSE &amp; R² score.
            </div>""", unsafe_allow_html=True)
        elif t_type == "categorical":
            task_type = "classification"
            st.markdown("""
            <div class="verdict-lose" style="padding:14px 18px">
                🏷️ <strong>Classification model</strong> — we'll predict categories
                and report Accuracy &amp; F1 score.
            </div>""", unsafe_allow_html=True)
        else:
            tc = st.radio(
                "Task type:",
                ["Regression  (numeric target)", "Classification  (category target)"],
                key="s3_task_manual",
            )
            task_type = "regression" if "Regression" in tc else "classification"

        w["target_col"] = target_col
        w["task_type"] = task_type

    # ── Experiment name ───────────────────────────────────────────────────
    st.markdown("---")
    default_name = w.get("exp_name") or f"Experiment-{pd.Timestamp.now().strftime('%Y%m%d-%H%M')}"
    w["exp_name"] = st.text_input("Experiment name (for your records)", value=default_name, key="s3_name")

    st.markdown("")
    c_back, _, c_next = st.columns([1, 5, 1])
    with c_back:
        if st.button("← Back", key="s3_back"):
            w["step"] = 2
            st.rerun()
    with c_next:
        if st.button("Next →", type="primary", key="s3_next"):
            w["step"] = 4
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Review & Create
# ─────────────────────────────────────────────────────────────────────────────

def _load_full_df(w: dict) -> pd.DataFrame | None:
    """Return the full DataFrame to run the experiment on."""
    src = w.get("source_type", "")

    if src in ("csv", "excel") and w.get("uploaded_bytes"):
        buf = io.BytesIO(w["uploaded_bytes"])
        return pd.read_csv(buf) if src == "csv" else pd.read_excel(buf)

    if src == "existing" and w.get("existing_dataset_id"):
        with get_connection() as conn:
            rows = [
                json.loads(r[0])
                for r in conn.execute(
                    sqla_text("SELECT fields FROM clean_records WHERE dataset_id = :ds"),
                    {"ds": w["existing_dataset_id"]},
                ).fetchall()
            ]
        return pd.DataFrame(rows) if rows else None

    if w.get("df") is not None:
        return w["df"]

    return None


def _execute(w: dict) -> None:
    """Run the full pipeline and store results in wizard state."""
    w["error"] = None
    with st.spinner("⚙️  Running experiment…"):
        try:
            df = _load_full_df(w)
            if df is None or df.empty:
                w["error"] = "Could not load data. Go back and check your data source."
                return

            # Clean
            cleaned_df, report = clean(df)
            st.toast(f"✓ Data cleaned ({report.rows_in}→{report.rows_out} rows)", icon="🧹")

            analysis = w.get("analysis_type", "ab")
            dataset_id = w.get("dataset_id") or w.get("existing_dataset_id") or str(uuid.uuid4())
            exp_name = w.get("exp_name") or f"Experiment-{pd.Timestamp.now().strftime('%H%M%S')}"
            w["dataset_id"] = dataset_id

            # A/B Test
            if analysis in ("ab", "all"):
                cfg = ExperimentConfig(
                    dataset_id=dataset_id,
                    name=exp_name,
                    variant_column=w["variant_col"],
                    metric_column=w["metric_col"],
                    metric_type=w["metric_type"],
                )
                result = evaluate_experiment(cfg, cleaned_df)
                with get_connection() as conn:
                    save_experiment_result(conn, result)
                w["result"] = result
                st.toast(f"✓ A/B experiment '{exp_name}' saved!", icon="🧪")

            # ML
            if analysis in ("ml", "all"):
                ml_res = train_model(
                    df=cleaned_df,
                    target_column=w["target_col"],
                    task_type=w.get("task_type", "regression"),
                    dataset_id=dataset_id,
                )
                with get_connection() as conn:
                    save_prediction_metadata(conn, ml_res)
                w["ml_result"] = ml_res
                st.toast("✓ ML model trained!", icon="🤖")

            # EDA only — just clean and return
            if analysis == "eda":
                st.success(f"✓ Data profiled! {report.rows_out} clean rows ready for analysis.")
                w["executed"] = True
                st.rerun()
                return

            w["executed"] = True
            st.rerun()

        except Exception as exc:
            w["error"] = str(exc)


def _step4(w: dict) -> None:
    st.markdown("#### Experiment Summary")
    st.caption("Review your configuration before running the experiment.")

    src_label = _SOURCE_LABELS.get(w.get("source_type", ""), "—")
    analysis_label = {
        "eda": "Data Cleaning & EDA",
        "ab": "A/B Testing",
        "ml": "ML Prediction",
        "all": "A/B Testing + ML Prediction",
    }.get(w.get("analysis_type", ""), "—")

    summary_rows = [("Data Source", src_label)]
    if w.get("uploaded_name"):
        summary_rows.append(("File", w["uploaded_name"]))
    if w.get("existing_dataset_id"):
        summary_rows.append(("Dataset ID", f"`{w['existing_dataset_id']}`"))
    summary_rows.append(("Analysis Type", analysis_label))
    if w.get("variant_col"):
        summary_rows.append(("Variant Column", f"`{w['variant_col']}`"))
    if w.get("metric_col"):
        test_map = {"numeric": "t-test (numeric)", "categorical": "chi-square (categorical)"}
        summary_rows.append(("Success Metric", f"`{w['metric_col']}`"))
        summary_rows.append(("Statistical Test", test_map.get(w.get("metric_type", ""), "—")))
    if w.get("target_col"):
        summary_rows.append(("Prediction Target", f"`{w['target_col']}`"))
        summary_rows.append(("ML Task", (w.get("task_type") or "—").title()))
    if w.get("exp_name"):
        summary_rows.append(("Experiment Name", f"**{w['exp_name']}**"))

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    for label, value in summary_rows:
        c1, c2 = st.columns([2, 3])
        c1.markdown(f"**{label}**")
        c2.markdown(value)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Error display ─────────────────────────────────────────────────────
    if w.get("error"):
        st.error(f"✗ {w['error']}")
        w["error"] = None

    # ── Post-execution result display ─────────────────────────────────────
    if w.get("executed"):
        st.markdown("---")
        result = w.get("result")
        ml_res = w.get("ml_result")

        if result is not None:
            is_sig = result.is_significant
            verdict_cls = "verdict-win" if is_sig else "verdict-lose"
            verdict_icon = "✅" if is_sig else "❌"
            verdict_text = "Statistically Significant!" if is_sig else "Not Statistically Significant"

            st.markdown(
                f'<div class="{verdict_cls}">'
                f'<span style="font-size:1.6rem">{verdict_icon}</span>'
                f'<strong style="font-size:1.2rem; margin-left:14px">{verdict_text}</strong><br>'
                f'<span style="color:#94a3b8; margin-left:46px; font-size:0.9rem">'
                f"p-value: {result.p_value:.4f}  |  Effect size: {result.effect_size:.3f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            narrative = generate_ab_narrative(
                experiment_name=w["exp_name"],
                variant_col=w.get("variant_col", ""),
                metric_col=w.get("metric_col", ""),
                p_value=result.p_value,
                is_significant=result.is_significant,
                effect_size=result.effect_size,
                test_type=result.test_type,
                summary_stats=result.summary_stats,
            )
            st.markdown(narrative)

        if ml_res is not None:
            ml_narrative = generate_ml_narrative(
                target_col=w.get("target_col", ""),
                model_type=ml_res.model_type,
                metrics=ml_res.metrics,
            )
            st.markdown(ml_narrative)

        if w.get("analysis_type") == "eda":
            st.success("Data profiling complete. Navigate to the Results tab or History for more detail.")

        col_view, col_new = st.columns(2)
        with col_view:
            if result is not None and st.button(
                "📊 View Full Results Dashboard", type="primary", use_container_width=True, key="s4_view"
            ):
                st.session_state["view_experiment"] = w["exp_name"]
                _reset()
                st.switch_page(st.session_state.pages["results"])
        with col_new:
            if st.button("🔄 Start Another Experiment", use_container_width=True, key="s4_new"):
                _reset()
                st.rerun()
        return

    # ── Create button ─────────────────────────────────────────────────────
    st.markdown("")
    c_back, _, c_create = st.columns([1, 2, 2])
    with c_back:
        back_step = 2 if w.get("analysis_type") == "eda" else 3
        if st.button("← Back", key="s4_back"):
            w["step"] = back_step
            st.rerun()
    with c_create:
        if st.button(
            "✓  Create Experiment",
            type="primary",
            use_container_width=True,
            key="s4_create",
        ):
            _execute(w)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def show() -> None:
    st.markdown("## 🧪 Create New Experiment")
    _init()
    w = st.session_state.wizard

    _progress_bar(w["step"])

    st.markdown(f"**Step {w['step']} of 4**")
    st.markdown("")

    if w["step"] == 1:
        _step1(w)
    elif w["step"] == 2:
        _step2(w)
    elif w["step"] == 3:
        _step3(w)
    elif w["step"] == 4:
        _step4(w)
