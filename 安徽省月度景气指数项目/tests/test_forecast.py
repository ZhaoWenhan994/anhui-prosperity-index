import warnings

import numpy as np
import pandas as pd

from anhui_index.forecast import forecast_index, rolling_validate


def _synthetic_index() -> pd.Series:
    dates = pd.date_range("2022-01-01", periods=36, freq="MS")
    values = 100 + np.arange(36, dtype=float) * 0.4 + 2 * np.sin(np.arange(36) / 2)
    return pd.Series(values, index=dates, name="prosperity_index")


def test_forecast_returns_sarima_and_seasonal_naive_predictions():
    result = forecast_index(_synthetic_index(), horizon=3)

    assert {"sarima", "seasonal_naive"} <= set(result.forecasts["model"])
    assert result.forecasts.groupby("model").size().to_dict() == {
        "sarima": 3,
        "seasonal_naive": 3,
    }
    assert result.forecasts["date"].min() == pd.Timestamp("2025-01-01")
    assert result.forecasts["date"].max() == pd.Timestamp("2025-03-01")
    assert result.selected_model in {"sarima", "seasonal_naive"}


def test_rolling_validate_reports_error_metrics_for_both_models():
    result = rolling_validate(_synthetic_index(), horizons=(1, 2, 3))

    assert {"sarima", "seasonal_naive"} <= set(result["model"])
    assert set(result["horizon"]) == {1, 2, 3}
    assert {"mae", "rmse", "n_predictions"} <= set(result.columns)
    assert (result["n_predictions"] > 0).all()
    assert (result["rmse"] >= result["mae"]).all()


def test_forecast_does_not_emit_unsupported_datetime_index_warnings():
    index = _synthetic_index().drop(pd.Timestamp("2022-03-01"))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        forecast_index(index, horizon=3)

    assert not [warning for warning in caught if "No supported index" in str(warning.message)]
