"""
Plain-Language Narrative Summary Generator -- US-8.2

Translates statistical test outputs and ML metrics into human-readable narratives for business stakeholders.
"""
from typing import Dict, Any, Optional


def generate_ab_narrative(
    experiment_name: str,
    variant_col: str,
    metric_col: str,
    p_value: float,
    is_significant: bool,
    effect_size: float,
    test_type: str,
    summary_stats: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate plain-language narrative for an A/B experiment.

    Returns:
        Formatted English text string summarizing results.
    """
    summary_stats = summary_stats or {}
    mean_diff = summary_stats.get("mean_difference")

    if is_significant:
        status_text = "STATISTICALLY SIGNIFICANT"
        verdict = "We are confident (p < 0.05) that the observed difference between variants is real and not due to random chance."
    else:
        status_text = "NOT STATISTICALLY SIGNIFICANT"
        verdict = "The observed difference between variants is small enough that it could likely be due to random variation (p >= 0.05)."

    diff_str = ""
    if mean_diff is not None:
        direction = "increase" if mean_diff > 0 else "decrease"
        diff_str = f" Mean difference observed: {abs(mean_diff):.2f} ({direction})."

    narrative = (
        f"**Experiment Summary for '{experiment_name}'**\n\n"
        f"Result: **{status_text}** (p-value = `{p_value:.4f}`).\n\n"
        f"{verdict}{diff_str}\n\n"
        f"- **Test Type Executed:** `{test_type}`\n"
        f"- **Effect Size:** `{effect_size:.3f}`\n"
        f"- **Variants Evaluated:** `{variant_col}` column against `{metric_col}` metric."
    )
    return narrative


def generate_ml_narrative(
    target_col: str,
    model_type: str,
    metrics: Dict[str, float],
) -> str:
    """
    Generate plain-language narrative for an ML model evaluation.

    Returns:
        Formatted English text string summarizing model quality.
    """
    if model_type == "regression":
        rmse = metrics.get("rmse", 0.0)
        r2 = metrics.get("r2", 0.0)
        quality = "high" if r2 > 0.7 else "moderate" if r2 > 0.4 else "low"
        narrative = (
            f"**Machine Learning Regression Model (`{target_col}`)**\n\n"
            f"Model Predictive Power: **{quality.upper()}** (R2 Score = `{r2:.2f}`).\n\n"
            f"- **Root Mean Squared Error (RMSE):** `{rmse:.2f}` (average prediction deviation in target units)\n"
            f"- **R-squared (R2):** `{r2:.2%}` of variance in target column `{target_col}` is explained by model features."
        )
    else:
        acc = metrics.get("accuracy", 0.0)
        f1 = metrics.get("f1_score", 0.0)
        quality = "high" if acc > 0.8 else "moderate" if acc > 0.6 else "low"
        narrative = (
            f"**Machine Learning Classification Model (`{target_col}`)**\n\n"
            f"Model Accuracy: **{quality.upper()}** (`{acc:.1%}` correct predictions).\n\n"
            f"- **Accuracy:** `{acc:.2%}`\n"
            f"- **Macro F1-Score:** `{f1:.3f}` (balanced precision & recall across target classes)."
        )

    return narrative
