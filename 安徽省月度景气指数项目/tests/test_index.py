import numpy as np
import pandas as pd

from anhui_index.index import fit_prosperity_index


def _synthetic_table() -> pd.DataFrame:
    dates = pd.date_range("2023-01-01", periods=24, freq="MS")
    base = np.arange(24, dtype=float)
    table = pd.DataFrame(
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
    table.loc[2, "quality_flag"] = "missing_core_indicator"
    return table


def test_index_uses_only_complete_months_and_scales_first_complete_year_to_100():
    result = fit_prosperity_index(_synthetic_table())

    assert pd.Timestamp("2023-03-01") not in result.index.index
    assert result.index.index.is_monotonic_increasing
    assert np.isclose(result.index[result.index.index.year == 2024].mean(), 100.0)
    assert result.loadings.index.tolist() == [
        "industrial_yoy",
        "investment_cum_yoy",
        "profit_cum_yoy",
        "power_yoy",
        "ppi_yoy",
    ]
    assert result.explained_variance_ratio > 0.99


def test_index_fits_scaler_only_on_training_period():
    result = fit_prosperity_index(_synthetic_table(), train_end="2023-12-01")

    assert result.training_end == pd.Timestamp("2023-12-01")
    assert result.scaler.n_samples_seen_ == 11
    assert result.index.index.max() == pd.Timestamp("2024-12-01")


def test_index_uses_a_transparent_nearly_complete_baseline_when_no_year_is_complete():
    table = _synthetic_table()
    table.loc[
        table["date"].isin(pd.to_datetime(["2024-01-01", "2024-02-01"])),
        "quality_flag",
    ] = "missing_core_indicator"

    result = fit_prosperity_index(table)

    assert result.baseline_year == 2023
    assert result.baseline_observations == 11
    assert result.baseline_is_complete is False


def test_index_does_not_divide_by_a_near_zero_pca_baseline_mean():
    dates = pd.date_range("2023-01-01", periods=24, freq="MS")
    base = np.sin(np.arange(24) * 2 * np.pi / 12)
    table = pd.DataFrame(
        {
            "date": dates,
            "industrial_yoy": base,
            "investment_cum_yoy": base * 2,
            "profit_cum_yoy": base * 3,
            "power_yoy": base * 4,
            "ppi_yoy": base * 5,
            "quality_flag": "ok",
        }
    )

    result = fit_prosperity_index(table)

    assert np.isclose(result.index[result.index.index.year == 2023].mean(), 100.0)
    assert result.index.abs().max() < 200
