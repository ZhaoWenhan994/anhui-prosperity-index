import pandas as pd

from anhui_index.excel_report import (
    localize_forecast_table,
    localize_index_series,
    localize_validation_table,
)


def test_output_tables_use_chinese_column_labels():
    index = pd.Series([100.0], index=pd.to_datetime(["2024-01-01"]), name="index_value")
    forecast = pd.DataFrame(
        {
            "model": ["sarima"],
            "date": pd.to_datetime(["2024-02-01"]),
            "forecast": [101.0],
            "lower_95": [99.0],
            "upper_95": [103.0],
            "aic": [10.0],
            "bic": [11.0],
            "model_detail": ["order=(1, 1, 1)"],
        }
    )
    validation = pd.DataFrame(
        {
            "model": ["sarima"],
            "horizon": [1],
            "mae": [1.0],
            "rmse": [1.2],
            "n_predictions": [5],
        }
    )

    assert list(localize_index_series(index).columns) == ["日期", "景气指数"]
    assert list(localize_forecast_table(forecast).columns) == [
        "模型",
        "日期",
        "预测值",
        "下限（95%）",
        "上限（95%）",
        "赤池信息准则（AIC）",
        "贝叶斯信息准则（BIC）",
        "模型参数",
    ]
    assert list(localize_validation_table(validation).columns) == [
        "模型",
        "预测期限（月）",
        "平均绝对误差（MAE）",
        "均方根误差（RMSE）",
        "预测点数",
    ]
