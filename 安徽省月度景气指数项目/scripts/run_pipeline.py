from __future__ import annotations

from pathlib import Path

import pandas as pd

from anhui_index.forecast import forecast_index, rolling_validate
from anhui_index.document_report import generate_document_reports
from anhui_index.excel_report import (
    localize_forecast_table,
    localize_index_series,
    localize_validation_table,
    write_excel_report,
)
from anhui_index.index import fit_prosperity_index
from anhui_index.report import generate_report


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "anhui_monthly_indicators.csv"
OUTPUTS = ROOT / "outputs"


def main() -> None:
    if not PROCESSED.exists():
        raise FileNotFoundError(
            f"缺少处理后的数据：{PROCESSED}。请先运行 scripts/build_processed_data.py"
        )
    table = pd.read_csv(PROCESSED, parse_dates=["date"])
    index_result = fit_prosperity_index(table)
    forecast_result = forecast_index(index_result.index, horizon=3)
    validation = rolling_validate(index_result.index, horizons=(1, 2, 3))

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    localize_index_series(index_result.index).to_csv(
        OUTPUTS / "景气指数结果.csv", index=False, encoding="utf-8-sig"
    )
    localize_forecast_table(forecast_result.forecasts).to_csv(
        OUTPUTS / "预测结果.csv", index=False, encoding="utf-8-sig"
    )
    localize_validation_table(validation).to_csv(
        OUTPUTS / "滚动验证.csv", index=False, encoding="utf-8-sig"
    )
    excel_report = write_excel_report(
        table,
        index_result,
        forecast_result,
        validation,
        OUTPUTS / "安徽省月度景气指数分析结果.xlsx",
    )
    report = generate_report(table, index_result, forecast_result, validation, OUTPUTS)
    word_report, pdf_report = generate_document_reports(
        table, index_result, forecast_result, validation, OUTPUTS
    )

    print(f"index_months={len(index_result.index)}")
    print(f"baseline_year={index_result.baseline_year}")
    print(f"explained_variance_ratio={index_result.explained_variance_ratio:.4f}")
    print(f"selected_model={forecast_result.selected_model}")
    print(f"excel_report={excel_report}")
    print(f"report={report}")
    print(f"word_report={word_report}")
    print(f"pdf_report={pdf_report}")


if __name__ == "__main__":
    main()
