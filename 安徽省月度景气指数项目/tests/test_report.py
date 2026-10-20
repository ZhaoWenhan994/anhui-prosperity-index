import numpy as np
import pandas as pd

from anhui_index.forecast import forecast_index
from anhui_index.index import fit_prosperity_index
from anhui_index.report import generate_report


def _synthetic_table() -> pd.DataFrame:
    dates = pd.date_range("2023-01-01", periods=24, freq="MS")
    base = np.arange(24, dtype=float)
    return pd.DataFrame(
        {
            "date": dates,
            "industrial_yoy": base,
            "investment_cum_yoy": base * 0.8 + 2,
            "profit_cum_yoy": base * 1.2 - 1,
            "power_yoy": base * 0.5 + 4,
            "ppi_yoy": base * 0.3 - 2,
            "quality_flag": "ok",
        }
    )


def test_generate_report_creates_html_and_four_figures(tmp_path):
    table = _synthetic_table()
    index_result = fit_prosperity_index(table)
    forecast_result = forecast_index(index_result.index, horizon=3)
    validation = pd.DataFrame(
        {
            "model": ["sarima", "seasonal_naive"],
            "horizon": [1, 1],
            "mae": [1.0, 2.0],
            "rmse": [1.2, 2.4],
            "n_predictions": [5, 5],
        }
    )

    output = generate_report(table, index_result, forecast_result, validation, tmp_path)

    assert output == tmp_path / "report.html"
    assert output.exists()
    assert "安徽省月度生产与投资景气指数" in output.read_text(encoding="utf-8")
    assert "固定资产投资和利润使用累计增速" in output.read_text(encoding="utf-8")
    assert "工业生产者出厂价格指数（PPI）" in output.read_text(encoding="utf-8")
    assert "平均绝对误差（MAE）" in output.read_text(encoding="utf-8")
    assert "季节性 ARIMA 模型（SARIMA）" in output.read_text(encoding="utf-8")
    for name in (
        "indicator_trends.png",
        "pca_loadings.png",
        "index_forecast.png",
        "context.png",
    ):
        assert (tmp_path / "figures" / name).exists()
