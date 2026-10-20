from pathlib import Path

from openpyxl import Workbook

from anhui_index.metadata import INDICATORS, SOURCE_URL


def write_dictionary(path: Path) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "指标字典"
    sheet.append(["字段名", "官方指标", "频率", "口径", "方向", "纳入 PCA", "转换规则", "数据来源"])

    for spec in INDICATORS:
        sheet.append([
            spec.key,
            spec.official_name,
            spec.frequency,
            spec.definition,
            spec.direction,
            "是" if spec.included_in_pca else "否",
            spec.transform,
            SOURCE_URL,
        ])

    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    return path
