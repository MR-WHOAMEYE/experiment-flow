"""
Dashboard Summary Statistics Module -- US-6.1
"""
import pandas as pd


def compute_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute descriptive statistics for all columns in a DataFrame.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with columns: column, dtype, count, missing_count, missing_pct, mean, std, min, median, max, unique_values.
    """
    records = []
    n = len(df)

    for col in df.columns:
        s = df[col]
        missing_count = int(s.isna().sum())
        missing_pct = round((missing_count / n) * 100, 2) if n > 0 else 0.0
        dtype_str = str(s.dtype)
        unique_vals = int(s.nunique(dropna=True))

        if pd.api.types.is_numeric_dtype(s):
            mean_val = float(s.mean()) if not s.dropna().empty else None
            std_val = float(s.std()) if len(s.dropna()) > 1 else None
            min_val = float(s.min()) if not s.dropna().empty else None
            med_val = float(s.median()) if not s.dropna().empty else None
            max_val = float(s.max()) if not s.dropna().empty else None
        else:
            mean_val = std_val = min_val = med_val = max_val = None

        records.append({
            "column": col,
            "dtype": dtype_str,
            "count": int(s.count()),
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "mean": mean_val,
            "std": std_val,
            "min": min_val,
            "median": med_val,
            "max": max_val,
            "unique_values": unique_vals,
        })

    return pd.DataFrame(records)
