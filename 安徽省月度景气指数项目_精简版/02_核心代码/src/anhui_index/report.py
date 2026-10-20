from __future__ import annotations

from html import escape
import os
from pathlib import Path
import tempfile

_MPL_CONFIG_DIR = Path(tempfile.gettempdir()) / "anhui-prosperity-index-matplotlib"
_MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from anhui_index.forecast import ForecastResult
from anhui_index.excel_report import (
    INDICATOR_LABELS,
    MODEL_LABELS,
    localize_validation_table,
)
from anhui_index.index import IndexResult
from anhui_index.preprocess import CORE_INDICATORS


def _configure_chinese_font() -> None:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def _save_indicator_trends(table: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    dates = pd.to_datetime(table["date"])
    for indicator in CORE_INDICATORS:
        ax.plot(dates, table[indicator], marker="o", markersize=2.5, label=INDICATOR_LABELS[indicator])
    ax.axhline(0, color="#777777", linewidth=0.8)
    ax.set_title("安徽省核心景气指标走势")
    ax.set_xlabel("月份")
    ax.set_ylabel("同比或同比偏离值")
    ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _save_loadings(index_result: IndexResult, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    labels = [INDICATOR_LABELS[name] for name in index_result.loadings.index]
    colors = ["#176b87" if value >= 0 else "#c84b31" for value in index_result.loadings]
    ax.bar(labels, index_result.loadings.values, color=colors)
    ax.axhline(0, color="#444444", linewidth=0.8)
    ax.set_title(
        f"PCA第一主成分载荷（解释方差比 {index_result.explained_variance_ratio:.1%}）"
    )
    ax.set_ylabel("载荷")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _save_index_forecast(
    index_result: IndexResult, forecast_result: ForecastResult, path: Path
) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    observed = index_result.index.sort_index()
    ax.plot(observed.index, observed.values, color="#176b87", label="历史景气指数")
    selected = forecast_result.forecasts.loc[
        forecast_result.forecasts["model"].eq(forecast_result.selected_model)
    ]
    if selected.empty:
        selected = forecast_result.forecasts.loc[
            forecast_result.forecasts["model"].eq("seasonal_naive")
        ]
    selected_dates = pd.to_datetime(selected["date"])
    ax.plot(selected_dates, selected["forecast"], "o--", color="#c84b31", label="预测值")
    ax.fill_between(
        selected_dates,
        selected["lower_95"].to_numpy(),
        selected["upper_95"].to_numpy(),
        color="#c84b31",
        alpha=0.16,
        label="95%区间",
    )
    ax.axhline(100, color="#777777", linewidth=0.8, linestyle=":", label="基准线 100")
    ax.set_title(f"安徽省景气指数与未来{len(selected)}个月预测")
    ax.set_xlabel("月份")
    ax.set_ylabel("指数")
    ax.legend(loc="best")
    ax.grid(alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _save_context(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.axis("off")
    ax.text(
        0.5,
        0.63,
        "辅助指标数据可用性说明",
        ha="center",
        va="center",
        fontsize=17,
        fontweight="bold",
    )
    ax.text(
        0.5,
        0.42,
        "本次国家统计局合并月度表未提供居民消费价格指数（CPI）和季度社会消费品零售总额。\n"
        "因此本项目不插值、不补造辅助指标，仅在报告中保留数据缺口说明。",
        ha="center",
        va="center",
        fontsize=12,
        linespacing=1.8,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def generate_report(
    table: pd.DataFrame,
    index_result: IndexResult,
    forecast_result: ForecastResult,
    validation: pd.DataFrame,
    output_dir: Path,
) -> Path:
    """Generate Chinese figures and a traceable HTML report."""
    _configure_chinese_font()
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    _save_indicator_trends(table, figures / "indicator_trends.png")
    _save_loadings(index_result, figures / "pca_loadings.png")
    _save_index_forecast(index_result, forecast_result, figures / "index_forecast.png")
    _save_context(figures / "context.png")

    dates = pd.to_datetime(table["date"])
    observed = index_result.index
    validation_display = localize_validation_table(validation)
    validation_html = validation_display.to_html(index=False, border=0, classes="metrics")
    loading_display = (
        index_result.loadings.rename("主成分分析载荷（PCA）")
        .rename(index=INDICATOR_LABELS)
        .rename_axis("指标")
        .reset_index()
    )
    loading_html = loading_display.to_html(index=False, border=0)
    selected_model_label = MODEL_LABELS.get(
        forecast_result.selected_model, forecast_result.selected_model
    )
    report = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>安徽省月度生产与投资景气指数</title>
<style>
body {{ max-width: 1100px; margin: 32px auto; padding: 0 24px; color: #23313a; font-family: "Microsoft YaHei", "Noto Sans CJK SC", sans-serif; line-height: 1.65; }}
h1 {{ color: #176b87; }}
h2 {{ border-bottom: 2px solid #d8e4e8; padding-bottom: 6px; }}
img {{ max-width: 100%; border: 1px solid #d8e4e8; margin: 8px 0 20px; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0 20px; }}
th, td {{ border: 1px solid #d8e4e8; padding: 6px 9px; text-align: right; }}
th {{ background: #eef5f7; }}
.note {{ background: #fff5e6; border-left: 4px solid #c84b31; padding: 10px 14px; }}
</style>
</head>
<body>
<h1>安徽省月度生产与投资景气指数</h1>
<p>本报告基于国家统计局分省月度数据，使用主成分分析（PCA）构建综合景气指数，并对未来三个月进行短期预测。</p>

<h2>样本与方法</h2>
<ul>
<li>原始样本期：{escape(str(dates.min().date()))} 至 {escape(str(dates.max().date()))}，共 {len(table)} 个月。</li>
<li>最新景气指数观测月：{escape(str(observed.index.max().date()))}。</li>
<li>主成分分析（PCA）输入：工业增加值同比、固定资产投资完成额累计增长、利润总额累计增长、发电量同比、工业生产者出厂价格指数（PPI）同比偏离值。</li>
<li>指数基准：{index_result.baseline_year}年平均值缩放为 100（使用 {index_result.baseline_observations} 个月观测，{'完整年度' if index_result.baseline_is_complete else '该年度存在官方缺失'}）。</li>
<li>指数幅度：将 PCA 得分的总体标准差映射为 10 个指数点，避免 PCA 得分均值接近 0 时产生失真的巨大指数。</li>
<li>预测模型：{escape(selected_model_label)}；同时保留 12 个月季节朴素基线。</li>
</ul>

<h2>核心指标走势</h2>
<img src="figures/indicator_trends.png" alt="核心指标走势">

<h2>主成分分析载荷（PCA）</h2>
<img src="figures/pca_loadings.png" alt="PCA载荷">
{loading_html}

<h2>景气指数与预测</h2>
<img src="figures/index_forecast.png" alt="景气指数预测">

<h2>滚动验证</h2>
<p>以下是模型与季节性朴素基线的误差对比。平均绝对误差（MAE）和均方根误差（RMSE）越小，表示预测误差越小。</p>
{validation_html}

<h2>辅助指标</h2>
<img src="figures/context.png" alt="辅助指标可用性说明">

<div class="note"><strong>解释限制：</strong>固定资产投资和利润使用累计增速（官方口径），不能直接解释为当月增速；样本长度较短，预测结果只适合作为方法展示和短期参考，不应视为确定性判断。</div>
</body>
</html>
"""
    report_path = output_dir / "report.html"
    report_path.write_text(report, encoding="utf-8")
    return report_path
