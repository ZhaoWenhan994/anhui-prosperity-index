# 安徽省月度生产与投资景气指数

这是一个用于应用统计复试展示的 Python 项目：使用国家统计局公开数据构建安徽省月度生产与投资景气指数，并完成短期预测和可视化报告。

## 查看成果

先看 `outputs/安徽省月度景气指数分析报告.pdf`；想检查数值，再看 `outputs/安徽省月度景气指数分析结果.xlsx`。报告、Excel 和图表均由下方命令生成。

项目包含数据导入、清洗、主成分分析（PCA）景气指数、季节性 ARIMA 模型（SARIMA）/季节朴素预测、滚动验证，以及中文 HTML、Word 和 PDF 报告模块。

已生成中文指标字典：`data/metadata/data_dictionary.xlsx`。

## 从新环境复现

需要 Python 3.12 或更新版本。以下命令在 Windows PowerShell 中运行，先进入本目录：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe scripts\build_processed_data.py
.\.venv\Scripts\python.exe scripts\create_statistics_report.py
.\.venv\Scripts\python.exe scripts\run_pipeline.py
```

如果计算机没有 `py` 命令，可以用已安装的 Python 3.12+ 可执行文件代替第一行。在 macOS/Linux 上使用 `python3.12 -m venv .venv`，后续将 `.\.venv\Scripts\python.exe` 改为 `./.venv/bin/python`。中文图表和 PDF 依赖可用的中文字体；正式交付文件已在 Windows 环境中生成。

仓库中的原始 Excel 位于 `data/raw/`；`data/metadata/raw_file_manifest.csv` 记录建模指标对应的文件名和官方指标名。若替换原始数据，需同步更新该清单。上述命令会生成：

- `data/processed/anhui_monthly_indicators.csv`：建模月度表；
- `outputs/景气指数结果.csv`：中文景气指数结果；
- `outputs/预测结果.csv`：两种预测方法的未来三个月结果；
- `outputs/滚动验证.csv`：滚动验证误差；
- `outputs/安徽省月度景气指数分析结果.xlsx`：建模数据、指数、预测、验证、载荷和数据说明；
- `outputs/安徽省月度景气指数分析报告.docx`：可编辑的 Word 正式报告；
- `outputs/安徽省月度景气指数分析报告.pdf`：适合提交和打印的 PDF 正式报告；
- `outputs/report.html` 和 `outputs/figures/`：网页预览和四张图。

其中 `data/processed/安徽省月度景气指数统计报表.xlsx` 的首个工作表为“核心变量宽表”：每行一个月份，列为变量 1—5；原始的“月份-指标-数值”长表保留在隐藏工作表中，便于追溯。

## 数据口径与限制

- 原始样本为 2023 年 8 月至 2026 年 7 月，共 36 个月；五项核心指标齐全的月份为 29 个。官方缺失月份不插值。
- 样本中没有 12 个完整月份的自然年，因此按代码中的备用规则，以 2024 年 10 个有效月份的 PCA 得分均值作为指数基准 100。这与“完整年度基期”不同，已在结果中标明。
- 固定资产投资和利润保留国家统计局累计增速口径，不能直接解释为当月增速。当前下载表没有 CPI 和季度社零，因此报告只标记数据不可用。
- 样本较短；预测用于方法展示和短期参考，不应视为确定性经济判断。运行结果反映本仓库保存的数据版本，不代表实时更新。
