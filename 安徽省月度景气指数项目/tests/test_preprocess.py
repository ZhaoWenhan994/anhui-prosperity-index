import pandas as pd
import pytest

from anhui_index.preprocess import build_monthly_table


def test_build_monthly_table_converts_ppi_and_marks_missing_core_indicator():
    records = pd.DataFrame(
        [
            {"date": "2025-01-01", "indicator": "industrial_yoy", "value": 4.0},
            {"date": "2025-01-01", "indicator": "investment_cum_yoy", "value": 5.0},
            {"date": "2025-01-01", "indicator": "profit_cum_yoy", "value": 6.0},
            {"date": "2025-01-01", "indicator": "power_yoy", "value": 7.0},
            {"date": "2025-01-01", "indicator": "ppi_yoy", "value": 102.5},
            {"date": "2025-02-01", "indicator": "ppi_yoy", "value": 99.5},
        ]
    )

    table = build_monthly_table(records)

    assert table["date"].astype(str).tolist() == ["2025-01-01", "2025-02-01"]
    assert table.loc[0, "ppi_yoy"] == 2.5
    assert table.loc[0, "quality_flag"] == "ok"
    assert table.loc[1, "ppi_yoy"] == -0.5
    assert table.loc[1, "quality_flag"] == "missing_core_indicator"


def test_build_monthly_table_rejects_duplicate_date_indicator_records():
    records = pd.DataFrame(
        [
            {"date": "2025-01-01", "indicator": "ppi_yoy", "value": 100.0},
            {"date": "2025-01-01", "indicator": "ppi_yoy", "value": 101.0},
        ]
    )

    with pytest.raises(ValueError, match="重复"):
        build_monthly_table(records)
