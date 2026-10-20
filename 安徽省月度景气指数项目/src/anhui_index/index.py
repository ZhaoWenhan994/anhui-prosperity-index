from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from anhui_index.preprocess import CORE_INDICATORS


@dataclass
class IndexResult:
    index: pd.Series
    loadings: pd.Series
    explained_variance_ratio: float
    scaler: StandardScaler
    pca: PCA
    training_end: pd.Timestamp | None
    baseline_year: int
    baseline_mean: float
    baseline_observations: int
    baseline_is_complete: bool


def _select_baseline_year(index: pd.Series) -> tuple[int, bool]:
    counts = index.groupby(index.index.year).size()
    complete_years = counts[counts >= 12]
    if not complete_years.empty:
        return int(complete_years.index.min()), True

    nearly_complete_years = counts[counts >= 10]
    if not nearly_complete_years.empty:
        return int(nearly_complete_years.index.min()), False

    raise ValueError("无法确定景气指数基准年：样本中没有至少 10 个月观测的年份")


def fit_prosperity_index(
    table: pd.DataFrame, train_end: str | None = None
) -> IndexResult:
    """Fit a leakage-safe first-principal-component prosperity index."""
    required = {"date", *CORE_INDICATORS, "quality_flag"}
    missing = required - set(table.columns)
    if missing:
        raise ValueError(f"建模表缺少字段：{', '.join(sorted(missing))}")

    valid = table.loc[table["quality_flag"].eq("ok"), ["date", *CORE_INDICATORS]].copy()
    valid["date"] = pd.to_datetime(valid["date"])
    valid = valid.sort_values("date").set_index("date")
    valid = valid.apply(pd.to_numeric, errors="raise")
    if valid.empty:
        raise ValueError("没有质量标记为 ok 的完整月份，无法拟合景气指数")

    end = pd.Timestamp(train_end) if train_end is not None else None
    training = valid if end is None else valid.loc[valid.index <= end]
    if len(training) < 2:
        raise ValueError("训练期完整月份少于 2 个，无法拟合 PCA")

    scaler = StandardScaler()
    scaled_training = scaler.fit_transform(training[CORE_INDICATORS])
    pca = PCA(n_components=1)
    pca.fit(scaled_training)

    loadings = pd.Series(pca.components_[0], index=CORE_INDICATORS, dtype=float)
    direction = 1.0 if loadings.sum() >= 0 else -1.0
    loadings = loadings * direction
    scores = pca.transform(scaler.transform(valid[CORE_INDICATORS]))[:, 0] * direction
    raw_index = pd.Series(scores, index=valid.index, name="prosperity_index")

    baseline_year, baseline_is_complete = _select_baseline_year(raw_index)
    baseline_values = raw_index[raw_index.index.year == baseline_year]
    baseline_mean = float(baseline_values.mean())
    score_std = float(raw_index.std(ddof=0))
    if np.isclose(score_std, 0.0):
        raise ValueError("PCA 得分没有时间波动，无法构建景气指数")
    scaled_index = 100 + (raw_index - baseline_mean) / score_std * 10

    return IndexResult(
        index=scaled_index,
        loadings=loadings,
        explained_variance_ratio=float(pca.explained_variance_ratio_[0]),
        scaler=scaler,
        pca=pca,
        training_end=end,
        baseline_year=baseline_year,
        baseline_mean=baseline_mean,
        baseline_observations=int(len(baseline_values)),
        baseline_is_complete=baseline_is_complete,
    )
