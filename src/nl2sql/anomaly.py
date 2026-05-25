"""Anomaly detection for query results."""
import logging
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result of anomaly detection analysis."""

    is_anomaly: bool = False
    score: float = 0.0
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""


def detect_anomaly(
    query_result: Dict[str, Any],
    sensitivity: float = 1.5,
    method: str = "auto",
) -> Dict[str, Any]:
    """Detect anomalies in query results.

    Supports two detection methods:
    - z_score: Statistical z-score based detection (for normally distributed data)
    - iqr: Interquartile range based detection (for skewed data)

    Args:
        query_result: Query result dict with 'columns' and 'rows'
        sensitivity: Sensitivity threshold (lower = more sensitive, default 1.5)
        method: Detection method - 'z_score', 'iqr', or 'auto' (default)

    Returns:
        Dictionary with anomaly detection results:
        - is_anomaly: bool indicating if anomalies were found
        - score: anomaly score (higher = more anomalous)
        - anomalies: list of anomalous rows with context
        - summary: human-readable summary string
    """
    if not query_result or query_result.get("error"):
        return {
            "is_anomaly": False,
            "score": 0.0,
            "anomalies": [],
            "summary": "No data available for anomaly detection",
        }

    columns = query_result.get("columns", [])
    rows = query_result.get("rows", [])

    if not rows or len(rows) < 3:
        return {
            "is_anomaly": False,
            "score": 0.0,
            "anomalies": [],
            "summary": "Insufficient data for anomaly detection (need at least 3 rows)",
        }

    # Find numeric columns for analysis
    numeric_cols = _identify_numeric_columns(columns, rows)
    if not numeric_cols:
        return {
            "is_anomaly": False,
            "score": 0.0,
            "anomalies": [],
            "summary": "No numeric columns found for anomaly detection",
        }

    # Auto-select method based on data distribution
    if method == "auto":
        method = _select_method(rows, numeric_cols)

    # Run selected detection method
    if method == "z_score":
        return z_score_detection(rows, numeric_cols, sensitivity)
    elif method == "iqr":
        return iqr_detection(rows, numeric_cols, sensitivity)
    else:
        logger.warning(f"Unknown method '{method}', falling back to z_score")
        return z_score_detection(rows, numeric_cols, sensitivity)


def _identify_numeric_columns(
    columns: List[str],
    rows: List[Dict[str, Any]],
) -> List[str]:
    """Identify numeric columns from the data.

    Args:
        columns: List of column names
        rows: List of row dictionaries

    Returns:
        List of column names that contain numeric data
    """
    numeric_cols = []

    for col in columns:
        try:
            values = [row.get(col) for row in rows if row.get(col) is not None]
            if values:
                # Check if values are numeric (int or float)
                numeric_count = sum(
                    1 for v in values if isinstance(v, (int, float))
                )
                if numeric_count / len(values) >= 0.8:  # 80% threshold
                    numeric_cols.append(col)
        except Exception as e:
            logger.debug(f"Column {col} analysis failed: {e}")
            continue

    return numeric_cols


def _select_method(
    rows: List[Dict[str, Any]],
    numeric_cols: List[str],
) -> str:
    """Select appropriate detection method based on data characteristics.

    Args:
        rows: List of row dictionaries
        numeric_cols: List of numeric column names

    Returns:
        'z_score' or 'iqr'
    """
    if not numeric_cols:
        return "z_score"

    # Use IQR for skewed distributions, z-score for normal
    try:
        values = [row[numeric_cols[0]] for row in rows if row.get(numeric_cols[0]) is not None]
        if len(values) < 3:
            return "z_score"

        mean = statistics.mean(values)
        median = statistics.median(values)
        std = statistics.stdev(values) if len(values) > 1 else 0

        # If mean differs significantly from median, data is skewed
        if std > 0:
            skew_measure = abs(mean - median) / std
            return "iqr" if skew_measure > 0.5 else "z_score"
        return "z_score"

    except Exception:
        return "z_score"


def z_score_detection(
    rows: List[Dict[str, Any]],
    numeric_cols: List[str],
    sensitivity: float = 1.5,
) -> Dict[str, Any]:
    """Detect anomalies using z-score method.

    A value is flagged as anomalous if its z-score exceeds the sensitivity threshold.

    Args:
        rows: List of row dictionaries
        numeric_cols: List of numeric column names
        sensitivity: Z-score threshold (default 1.5)

    Returns:
        Anomaly detection results dictionary
    """
    anomalies = []
    max_score = 0.0

    for col in numeric_cols:
        values = [(i, row[col]) for i, row in enumerate(rows) if row.get(col) is not None]

        if len(values) < 3:
            continue

        numeric_values = [v for _, v in values]
        mean = statistics.mean(numeric_values)
        std = statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0

        if std == 0:
            continue

        for idx, val in values:
            z_score = abs((val - mean) / std)
            if z_score > sensitivity:
                anomalies.append({
                    "row_index": idx,
                    "row_data": rows[idx],
                    "column": col,
                    "value": val,
                    "z_score": round(z_score, 3),
                    "expected_range": f"[{round(mean - sensitivity * std, 2)}, {round(mean + sensitivity * std, 2)}]",
                })
                max_score = max(max_score, z_score)

    is_anomaly = len(anomalies) > 0
    summary = _generate_summary(
        is_anomaly,
        max_score,
        len(anomalies),
        len(rows),
        "z-score",
        sensitivity,
    )

    return {
        "is_anomaly": is_anomaly,
        "score": round(max_score, 3),
        "anomalies": anomalies,
        "summary": summary,
    }


def iqr_detection(
    rows: List[Dict[str, Any]],
    numeric_cols: List[str],
    sensitivity: float = 1.5,
) -> Dict[str, Any]:
    """Detect anomalies using Interquartile Range (IQR) method.

    A value is flagged as anomalous if it falls outside
    [Q1 - sensitivity * IQR, Q3 + sensitivity * IQR].

    Args:
        rows: List of row dictionaries
        numeric_cols: List of numeric column names
        sensitivity: IQR multiplier threshold (default 1.5)

    Returns:
        Anomaly detection results dictionary
    """
    anomalies = []
    max_score = 0.0

    for col in numeric_cols:
        values = [(i, row[col]) for i, row in enumerate(rows) if row.get(col) is not None]

        if len(values) < 3:
            continue

        numeric_values = sorted([v for _, v in values])
        n = len(numeric_values)

        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        q1 = numeric_values[q1_idx]
        q3 = numeric_values[q3_idx]
        iqr = q3 - q1

        if iqr == 0:
            # Fall back to z-score if IQR is zero (no spread)
            for idx, val in values:
                mean = statistics.mean(numeric_values)
                std = statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
                if std > 0:
                    z_score = abs((val - mean) / std)
                    if z_score > sensitivity:
                        anomalies.append({
                            "row_index": idx,
                            "row_data": rows[idx],
                            "column": col,
                            "value": val,
                            "z_score": round(z_score, 3),
                            "expected_range": f"[{round(mean - sensitivity * std, 2)}, {round(mean + sensitivity * std, 2)}]",
                        })
                        max_score = max(max_score, z_score)
            continue

        lower_bound = q1 - sensitivity * iqr
        upper_bound = q3 + sensitivity * iqr

        for idx, val in values:
            if val < lower_bound or val > upper_bound:
                # Calculate how far outside the bounds
                if val < lower_bound:
                    distance = lower_bound - val
                else:
                    distance = val - upper_bound
                score = distance / iqr if iqr > 0 else 0

                anomalies.append({
                    "row_index": idx,
                    "row_data": rows[idx],
                    "column": col,
                    "value": val,
                    "score": round(score, 3),
                    "expected_range": f"[{round(lower_bound, 2)}, {round(upper_bound, 2)}]",
                    "quartiles": {"q1": q1, "q3": q3, "iqr": iqr},
                })
                max_score = max(max_score, score)

    is_anomaly = len(anomalies) > 0
    summary = _generate_summary(
        is_anomaly,
        max_score,
        len(anomalies),
        len(rows),
        "IQR",
        sensitivity,
    )

    return {
        "is_anomaly": is_anomaly,
        "score": round(max_score, 3),
        "anomalies": anomalies,
        "summary": summary,
    }


def _generate_summary(
    is_anomaly: bool,
    score: float,
    num_anomalies: int,
    total_rows: int,
    method: str,
    sensitivity: float,
) -> str:
    """Generate human-readable summary of anomaly detection results.

    Args:
        is_anomaly: Whether anomalies were detected
        score: Anomaly score
        num_anomalies: Number of anomalous rows
        total_rows: Total number of rows analyzed
        method: Detection method used
        sensitivity: Sensitivity threshold used

    Returns:
        Human-readable summary string
    """
    if not is_anomaly:
        return (
            f"No anomalies detected using {method} method "
            f"(sensitivity={sensitivity}). All {total_rows} values are within expected ranges."
        )

    pct = (num_anomalies / total_rows * 100) if total_rows > 0 else 0
    return (
        f"Anomaly detected: {num_anomalies} of {total_rows} rows ({pct:.1f}%) "
        f"flagged as anomalous using {method} method (score={score:.3f}, "
        f"sensitivity={sensitivity}). These values deviate significantly from the expected distribution."
    )