"""
A/B Testing Statistical Engine -- US-4.2 (ADR-002)

Responsibilities:
  1. Select and run appropriate statistical test:
     - Numeric metrics: Welch's t-test (scipy.stats.ttest_ind with equal_var=False), Cohen's d, 95% CI.
     - Categorical metrics: Chi-square test (scipy.stats.chi2_contingency), Cram?r's V.
  2. Compute statistical significance flag (p < 0.05).
  3. Store results in the `experiments` database table.

References: ADR-002, prompt.md US-4.2
"""
import json
from dataclasses import dataclass
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ab_testing.config import ExperimentConfig, validate_config
from ingestion.logger import get_logger

log = get_logger(__name__)


@dataclass
class ExperimentResult:
    """Container for complete A/B experiment evaluation results."""
    config: ExperimentConfig
    test_type: str                  # "t-test" | "chi-square"
    stat_value: float               # t-statistic or chi2 statistic
    p_value: float
    is_significant: bool            # True if p_value < 0.05
    effect_size: float              # Cohen's d or Cram?r's V
    confidence_interval: Tuple[float, float] | None
    summary_stats: Dict[str, Any]


def _cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    """Calculate Cohen's d for two independent samples."""
    nx, ny = len(x), len(y)
    dof = nx + ny - 2
    if dof <= 0:
        return 0.0
    s_pooled = np.sqrt(((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / dof)
    if s_pooled == 0:
        return 0.0
    return float((np.mean(y) - np.mean(x)) / s_pooled)


def _cramers_v(contingency_table: np.ndarray) -> float:
    """Calculate Cram?r's V for a contingency table."""
    chi2 = stats.chi2_contingency(contingency_table)[0]
    n = contingency_table.sum()
    if n == 0:
        return 0.0
    r, k = contingency_table.shape
    min_dim = min(r - 1, k - 1)
    if min_dim <= 0:
        return 0.0
    return float(np.sqrt((chi2 / n) / min_dim))


def evaluate_experiment(config: ExperimentConfig, df: pd.DataFrame) -> ExperimentResult:
    """
    Execute statistical analysis for an A/B experiment.

    Args:
        config: Validated ExperimentConfig.
        df:     Cleaned DataFrame containing experiment data.

    Returns:
        ExperimentResult instance.
    """
    validate_config(config, df)
    log.info("evaluate_experiment started", extra={"experiment_name": config.name, "type": config.metric_type})

    groups = df[config.variant_column].dropna().unique()
    g1_label, g2_label = str(groups[0]), str(groups[1])

    g1_data = df[df[config.variant_column] == groups[0]][config.metric_column].dropna()
    g2_data = df[df[config.variant_column] == groups[1]][config.metric_column].dropna()

    if config.metric_type == "numeric":
        # Welch's t-test
        t_stat, p_val = stats.ttest_ind(g2_data, g1_data, equal_var=False)
        t_stat = float(t_stat)
        p_val = float(p_val)

        effect = _cohens_d(g1_data.to_numpy(), g2_data.to_numpy())

        # 95% Confidence Interval for mean difference (g2 - g1)
        mean_diff = float(np.mean(g2_data) - np.mean(g1_data))
        se_diff = float(np.sqrt(np.var(g1_data, ddof=1)/len(g1_data) + np.var(g2_data, ddof=1)/len(g2_data)))
        ci_lower = mean_diff - 1.96 * se_diff
        ci_upper = mean_diff + 1.96 * se_diff
        ci = (float(ci_lower), float(ci_upper))

        test_type = "t-test"
        summary = {
            f"{g1_label}_mean": float(np.mean(g1_data)),
            f"{g2_label}_mean": float(np.mean(g2_data)),
            f"{g1_label}_std": float(np.std(g1_data)),
            f"{g2_label}_std": float(np.std(g2_data)),
            "mean_difference": mean_diff,
        }
    else:
        # Chi-square test
        contingency = pd.crosstab(df[config.variant_column], df[config.metric_column])
        chi2_stat, p_val, dof, _ex = stats.chi2_contingency(contingency)
        t_stat = float(chi2_stat)
        p_val = float(p_val)
        effect = _cramers_v(contingency.to_numpy())
        ci = None
        test_type = "chi-square"
        summary = {"contingency_matrix": contingency.to_dict()}

    is_sig = bool(p_val < 0.05)

    res = ExperimentResult(
        config=config,
        test_type=test_type,
        stat_value=t_stat,
        p_value=p_val,
        is_significant=is_sig,
        effect_size=float(effect),
        confidence_interval=ci,
        summary_stats=summary,
    )

    log.info(
        "evaluate_experiment complete",
        extra={"p_value": p_val, "is_significant": is_sig, "effect_size": effect},
    )
    return res


def save_experiment_result(conn: Connection, result: ExperimentResult) -> None:
    """
    Persist an ExperimentResult into the experiments table.

    Args:
        conn:   Active SQLAlchemy Connection.
        result: ExperimentResult to save.
    """
    insert_sql = text(
        """
        INSERT INTO experiments (
            dataset_id, name, variant_column, metric_column, metric_type,
            p_value, effect_size, is_significant, summary
        ) VALUES (
            :dataset_id, :name, :variant_column, :metric_column, :metric_type,
            :p_value, :effect_size, :is_significant, :summary
        )
        """
    )

    summary_payload = {
        "test_type": result.test_type,
        "stat_value": result.stat_value,
        "confidence_interval": result.confidence_interval,
        "summary_stats": result.summary_stats,
    }

    conn.execute(
        insert_sql,
        {
            "dataset_id": result.config.dataset_id,
            "name": result.config.name,
            "variant_column": result.config.variant_column,
            "metric_column": result.config.metric_column,
            "metric_type": result.config.metric_type,
            "p_value": result.p_value,
            "effect_size": result.effect_size,
            "is_significant": result.is_significant,
            "summary": json.dumps(summary_payload),
        },
    )
    log.info("save_experiment_result written to DB", extra={"exp_name": result.config.name})
