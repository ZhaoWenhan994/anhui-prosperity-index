from __future__ import annotations

from pathlib import Path

import pandas as pd


CORE_INDICATORS = [
    "industrial_yoy",
    "investment_cum_yoy",
    "profit_cum_yoy",
    "power_yoy",
    "ppi_yoy",
]


def build_monthly_table(records: pd.DataFrame) -> pd.DataFrame:
    """Convert canonical long records into a monthly modelling table."""
    required = {"date", "indicator", "value"}
    if not required <= set(records.columns):
        raise ValueError("长表必须包含 date、indicator 和 value 三列")
    if records.duplicated(["date", "indicator"]).any():
        raise ValueError("长表中存在重复的 日期-指标 记录")

    table = records.pivot(index="date", columns="indicator", values="value").sort_index()
    table.index = pd.to_datetime(table.index)
    table.index.name = "date"
    for indicator in CORE_INDICATORS:
        if indicator not in table:
            table[indicator] = pd.NA
    table["ppi_yoy"] = table["ppi_yoy"] - 100
    table["quality_flag"] = table[CORE_INDICATORS].notna().all(axis=1).map(
        {True: "ok", False: "missing_core_indicator"}
    )
    return table.reset_index()[["date", *CORE_INDICATORS, "quality_flag"]]


def write_processed_table(table: pd.DataFrame, path: Path) -> Path:
    """Write a UTF-8 BOM CSV so it opens directly in Excel on Windows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False, encoding="utf-8-sig")
    return path
