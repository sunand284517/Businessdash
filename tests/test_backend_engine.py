import pandas as pd
from backend.main import AnalysisEngine


def make_demo_df():
    return pd.DataFrame({
        "Region": ["North", "South", "East", "West"],
        "Sales": [100, 200, 150, 175],
        "Category": ["A", "B", "A", "B"]
    })


def test_get_data_stats():
    df = make_demo_df()
    engine = AnalysisEngine(df)
    stats = engine.get_data_stats()
    assert stats["rows"] == 4
    assert stats["columns"] == 3
    assert "numeric_columns" in stats


def test_execute_analysis_simple_query():
    df = make_demo_df()
    engine = AnalysisEngine(df)
    plan = {"sql": "SELECT Region, Sales FROM data ORDER BY Sales DESC LIMIT 2"}
    result = engine.execute_analysis(plan)
    assert len(result) == 2
    assert list(result.columns) == ["Region", "Sales"]
