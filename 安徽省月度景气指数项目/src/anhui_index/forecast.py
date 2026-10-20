from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX


@dataclass
class ForecastResult:
    forecasts: pd.DataFrame
    selected_model: str
    selected_order: tuple[tuple[int, int, int], tuple[int, int, int, int]] | None
    candidates: pd.DataFrame


_SARIMA_CANDIDATES = (
    ((0, 1, 1), (0, 0, 0, 12)),
    ((1, 1, 0), (0, 0, 0, 12)),
    ((1, 0, 0), (0, 0, 0, 12)),
    ((0, 1, 0), (0, 0, 0, 12)),
)


def _prepare_index(index: pd.Series) -> pd.Series:
    series = pd.Series(index, copy=True, dtype=float)
    series.index = pd.to_datetime(series.index)
    if series.index.has_duplicates:
        raise ValueError("景气指数中存在重复日期")
    series = series.sort_index().dropna()
    if len(series) < 13:
        raise ValueError("预测至少需要 13 个月的景气指数")
    return series


def _future_dates(last_date: pd.Timestamp, horizon: int) -> pd.DatetimeIndex:
    return pd.date_range(
        start=last_date + pd.offsets.MonthBegin(1), periods=horizon, freq="MS"
    )


def _seasonal_naive(series: pd.Series, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    values = series.to_numpy()
    forecast = np.array([values[-12 + i % 12] for i in range(horizon)], dtype=float)
    residuals = values[12:] - values[:-12]
    spread = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0
    margin = 1.96 * spread
    return forecast, np.column_stack((forecast - margin, forecast + margin))


def _fit_sarima(
    series: pd.Series, horizon: int
) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int], tuple[int, int, int, int], float, float] | None:
    fitted: list[tuple[float, float, tuple[int, int, int], tuple[int, int, int, int], object]] = []
    for order, seasonal_order in _SARIMA_CANDIDATES:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = SARIMAX(
                    series.to_numpy(),
                    order=order,
                    seasonal_order=seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                result = model.fit(disp=False, maxiter=200)
            if np.isfinite(result.aic) and np.isfinite(result.bic):
                fitted.append((float(result.aic), float(result.bic), order, seasonal_order, result))
        except (ValueError, np.linalg.LinAlgError, RuntimeError):
            continue

    if not fitted:
        return None
    fitted.sort(key=lambda item: (item[0], item[1]))
    aic, bic, order, seasonal_order, result = fitted[0]
    prediction = result.get_forecast(steps=horizon)
    confidence = np.asarray(prediction.conf_int(alpha=0.05), dtype=float)
    return (
        np.asarray(prediction.predicted_mean, dtype=float),
        confidence,
        order,
        seasonal_order,
        aic,
        bic,
    )


def forecast_index(index: pd.Series, horizon: int = 3) -> ForecastResult:
    """Forecast a monthly index with SARIMA and a 12-month seasonal baseline."""
    if horizon < 1:
        raise ValueError("预测期限必须至少为 1 个月")
    series = _prepare_index(index)
    dates = _future_dates(series.index[-1], horizon)
    rows: list[dict[str, object]] = []

    seasonal_forecast, seasonal_interval = _seasonal_naive(series, horizon)
    for date, value, interval in zip(dates, seasonal_forecast, seasonal_interval):
        rows.append(
            {
                "model": "seasonal_naive",
                "date": date,
                "forecast": value,
                "lower_95": interval[0],
                "upper_95": interval[1],
                "aic": np.nan,
                "bic": np.nan,
                "model_detail": "t-12",
            }
        )

    sarima = _fit_sarima(series, horizon)
    candidates = pd.DataFrame(columns=["order", "seasonal_order", "aic", "bic"])
    selected_order = None
    if sarima is not None:
        forecast, interval, order, seasonal_order, aic, bic = sarima
        selected_order = (order, seasonal_order)
        for date, value, bounds in zip(dates, forecast, interval):
            rows.append(
                {
                    "model": "sarima",
                    "date": date,
                    "forecast": value,
                    "lower_95": bounds[0],
                    "upper_95": bounds[1],
                    "aic": aic,
                    "bic": bic,
                    "model_detail": f"order={order}, seasonal_order={seasonal_order}",
                }
            )
        candidates = pd.DataFrame(
            [{"order": order, "seasonal_order": seasonal_order, "aic": aic, "bic": bic}]
        )

    return ForecastResult(
        forecasts=pd.DataFrame(rows),
        selected_model="sarima" if sarima is not None else "seasonal_naive",
        selected_order=selected_order,
        candidates=candidates,
    )


def rolling_validate(
    index: pd.Series, horizons: tuple[int, ...] = (1, 2, 3)
) -> pd.DataFrame:
    """Evaluate both forecasting approaches over expanding rolling windows."""
    series = _prepare_index(index)
    if not horizons or any(horizon < 1 for horizon in horizons):
        raise ValueError("horizons 必须是正整数元组")

    errors: dict[tuple[str, int], list[float]] = {}
    for horizon in horizons:
        for origin in range(13, len(series) - horizon + 1):
            train = series.iloc[:origin]
            actual = series.iloc[origin : origin + horizon].to_numpy()
            result = forecast_index(train, horizon=horizon)
            for model in ("seasonal_naive", "sarima"):
                prediction = result.forecasts.loc[
                    result.forecasts["model"].eq(model), "forecast"
                ].to_numpy()
                if len(prediction) != horizon:
                    continue
                errors.setdefault((model, horizon), []).extend((prediction - actual).tolist())

    rows = []
    for (model, horizon), values in sorted(errors.items()):
        error = np.asarray(values, dtype=float)
        rows.append(
            {
                "model": model,
                "horizon": horizon,
                "mae": float(np.mean(np.abs(error))),
                "rmse": float(np.sqrt(np.mean(error**2))),
                "n_predictions": int(len(error)),
            }
        )
    return pd.DataFrame(rows, columns=["model", "horizon", "mae", "rmse", "n_predictions"])
