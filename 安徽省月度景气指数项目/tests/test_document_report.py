import pytest

pytest.importorskip("docx")
pytest.importorskip("reportlab")

import numpy as np
import pandas as pd
from docx import Document

from anhui_index.document_report import generate_document_reports
from anhui_index.forecast import forecast_index
from anhui_index.index import fit_prosperity_index
from anhui_index.report import generate_report


def test_generate_document_reports_creates_word_and_pdf(tmp_path):
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
    index_result = fit_prosperity_index(table)
    forecast_result = forecast_index(index_result.index, horizon=3)
    validation = pd.DataFrame(
        {
            "model": ["sarima"],
            "horizon": [1],
            "mae": [1.0],
            "rmse": [1.2],
            "n_predictions": [5],
        }
    )
    generate_report(table, index_result, forecast_result, validation, tmp_path)

    word_path, pdf_path = generate_document_reports(
        table, index_result, forecast_result, validation, tmp_path
    )

    assert word_path.exists()
    assert pdf_path.exists()
    assert word_path.stat().st_size > 1000
    assert pdf_path.stat().st_size > 1000
    document = Document(word_path)
    body = next(paragraph for paragraph in document.paragraphs if paragraph.text.startswith("样本期"))
    assert body.runs[0].font.name == "Microsoft YaHei"
    assert body.runs[0].bold is False
