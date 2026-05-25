"""Rule-based chart type recommendation."""
from typing import Literal


CHART_KEYWORDS = {
    "line": ["trend", "over time", "growth", "变化趋势", "增长", "下降", "时间序列"],
    "column_parallel": ["compare", "ranking", "比较", "排名", "count"],
    "pie": ["proportion", "share", "占比", "比例", "distribution"],
    "measure_card": ["total", "value", "key metric", "数值", "汇总", "总额"],
    "table": ["detail", "明细", "list", "详细"],
    "scatter": ["correlation", "relationship", "相关性", "分布", "影响"],
    "map": ["region", "geography", "区域", "地理", "map"],
    "double_axis": ["dual axis", "对比", "双轴", "two metrics"],
    "combination": ["combination", "complex", "组合", "多维度"],
}

# Data shape heuristics
CHART_BY_ROWS = {
    1: "measure_card",
    2: "column_parallel",
    "default": "table",
}


def recommend_chart(
    query: str,
    num_rows: int = 0,
    has_time_dimension: bool = False,
    has_geography_dimension: bool = False,
) -> str:
    """Recommend chart type based on query text and data shape.

    query: original natural language question
    num_rows: number of result rows
    has_time_dimension: result contains time column
    has_geography_dimension: result contains region column
    """
    q_lower = query.lower()
    for chart_type, keywords in CHART_KEYWORDS.items():
        for kw in keywords:
            if kw in q_lower:
                if chart_type == "map" and has_geography_dimension:
                    return "map"
                if chart_type == "line" and has_time_dimension:
                    return "line"
                return chart_type
    if num_rows == 1:
        return "measure_card"
    if num_rows <= 10:
        return "column_parallel"
    return "table"