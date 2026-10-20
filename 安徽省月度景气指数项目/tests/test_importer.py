from openpyxl import Workbook

from anhui_index.importer import CANONICAL_COLUMNS, import_workbook
from anhui_index.metadata import INDICATORS


def test_import_workbook_converts_statistical_bureau_wide_sheet_to_long_table(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["数据库：分省月度数据"])
    sheet.append(["地区：安徽省"])
    sheet.append(["时间：2025年10月-2025年11月"])
    sheet.append(["指标", "2025年11月", "2025年10月"])
    sheet.append(["工业增加值同比增长 (%)", "5.2", "4.8"])

    path = tmp_path / "industrial.xlsx"
    workbook.save(path)

    records = import_workbook(path, "industrial_yoy")

    assert list(records.columns) == CANONICAL_COLUMNS
    assert records.to_dict("records") == [
        {
            "date": "2025-10-01",
            "indicator": "industrial_yoy",
            "value": 4.8,
            "source_file": "industrial.xlsx",
            "official_name": "工业增加值同比增长 (%)",
        },
        {
            "date": "2025-11-01",
            "indicator": "industrial_yoy",
            "value": 5.2,
            "source_file": "industrial.xlsx",
            "official_name": "工业增加值同比增长 (%)",
        },
    ]


def test_ppi_metadata_uses_the_exact_official_export_name():
    ppi = next(spec for spec in INDICATORS if spec.key == "ppi_yoy")

    assert ppi.official_name == "工业生产者出厂价格指数 (上年同月=100)"
