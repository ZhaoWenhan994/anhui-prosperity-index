# 安徽省月度生产与投资景气指数：实施计划

**目标：** 建立一个可复现的 Python 项目，导入安徽省官方月度统计数据，构建 PCA 景气指数，预测未来三个月，并生成中文图表报告。

**架构：** 原始 Excel 仅作为不可修改的输入文件。导入模块将其统一为长表，清洗模块再生成建模月度表；指数、预测和报告模块只依赖处理后的数据表。Excel 指标字典用于说明数据口径，不作为手工维护的建模数据源。

**技术栈：** Python 3.12、pandas、numpy、scikit-learn、statsmodels、matplotlib、openpyxl、pytest。

**设计依据：** `docs/superpowers/specs/2026-08-14-anhui-prosperity-index-design.md`

## 全局约束

- 地区为安徽省，核心输入均为月度数据。
- 原始官方文件保存在 `data/raw/`，不得由程序修改。
- PCA 核心字段是 `industrial_yoy`、`investment_cum_yoy`、`profit_cum_yoy`、`power_yoy` 和 `ppi_yoy`。
- `cpi_yoy` 与季度社零仅用于报告展示，绝不进入 PCA。
- 不对缺失月份插值，只生成质量标记。
- 标准化器只在训练样本拟合；滚动验证报告 1、2、3 个月预测的 MAE 与 RMSE。

## 文件结构

```text
data/
  raw/                         # 国家统计局下载的原始 Excel
  processed/                   # 清洗后的 CSV
  metadata/                    # 指标字典与原始文件清单
src/anhui_index/
  metadata.py                  # 指标元数据
  dictionary.py                # 生成 Excel 指标字典
  importer.py                  # 解析原始 Excel
  preprocess.py                # 清洗和质量检查
  index.py                     # PCA 指数
  forecast.py                  # 预测与滚动验证
  report.py                    # 图表与 HTML 报告
tests/                         # 对应模块测试
outputs/                       # 图表、预测结果与报告
```

## 任务一：项目骨架与 Excel 指标字典

**新增文件：** `pyproject.toml`、`README.md`、`src/anhui_index/__init__.py`、`src/anhui_index/metadata.py`、`src/anhui_index/dictionary.py`、`tests/test_dictionary.py`。

**产出接口：**

```python
@dataclass(frozen=True)
class IndicatorSpec:
    key: str
    official_name: str
    unit: str
    frequency: str
    direction: str
    included_in_pca: bool
    transform: str
    source_url: str

def write_dictionary(path: Path) -> Path: ...
```

**执行顺序：**

1. 编写测试：生成的 `data_dictionary.xlsx` 必须包含五个 PCA 字段。
2. 运行 `python -m pytest tests/test_dictionary.py -v`，确认模块不存在时测试失败。
3. 实现不可变指标元数据和 `write_dictionary`，Excel 首行必须是中文字段名。
4. 再次运行测试，并执行 `python -m anhui_index.dictionary --output data/metadata/data_dictionary.xlsx`。
5. 提交：`git commit -m "feat: 添加指标字典"`。

## 任务二：原始 Excel 导入与数据契约

**新增文件：** `src/anhui_index/importer.py`、`tests/test_importer.py`、`data/metadata/raw_file_manifest.csv`。

**输入：** 国家统计局导出的 Excel。首列含官方指标名，月份列为 `YYYY年M月`。清单列为 `indicator,filename,official_name`，核心文件名固定为 `industrial.xlsx`、`investment.xlsx`、`profit.xlsx`、`power.xlsx`、`ppi.xlsx`。

**产出接口：**

```python
CANONICAL_COLUMNS = ["date", "indicator", "value", "source_file", "official_name"]

def import_workbook(path: Path, indicator_key: str) -> pd.DataFrame: ...

def import_manifest(manifest_path: Path, raw_directory: Path) -> pd.DataFrame: ...
```

**执行顺序：**

1. 用一个最小测试 Excel 验证 `2025年11月` 会被解析成 `2025-11-01`。
2. 先运行测试，确认没有 `import_workbook` 时失败。
3. 实现月份表头与官方指标行的严格解析。
4. 指标行或月份表头不存在时，抛出包含文件名和预期官方指标名的 `ValueError`；不猜测近似名称。
5. 运行 `python -m pytest tests/test_importer.py -v`，通过后提交。

## 任务三：清洗、转换与建模月度表

**新增文件：** `src/anhui_index/preprocess.py`、`tests/test_preprocess.py`。

**产出接口：**

```python
def build_monthly_table(records: pd.DataFrame) -> pd.DataFrame: ...

def write_processed_table(table: pd.DataFrame, path: Path) -> Path: ...
```

**规则：**

- 日期按升序排列；重复的“日期-指标”组合直接报错。
- PPI 从“上年同月=100”转换为 `ppi_yoy = value - 100`。
- 任何 PCA 核心字段缺失时，该月 `quality_flag` 为 `missing_core_indicator`。
- 不前向填充，不插值，不删除官方异常值；只保留异常和缺失标记。

**执行顺序：**

1. 测试 PPI 转换和缺失核心字段标记。
2. 运行 `python -m pytest tests/test_preprocess.py -v`，确认实现前失败。
3. 实现透视成长表、日期排序、重复检查、PPI 转换与质量标记。
4. 测试通过后，执行导入命令。没有原始 Excel 时必须明确报出缺失文件名，而不是生成虚构数据。
5. 提交：`git commit -m "feat: 添加月度数据清洗"`。

## 任务四：PCA 景气指数、预测和滚动验证

**新增文件：** `src/anhui_index/index.py`、`src/anhui_index/forecast.py`、`tests/test_index.py`、`tests/test_forecast.py`。

**产出接口：**

```python
def fit_prosperity_index(
    table: pd.DataFrame, train_end: str | None = None
) -> IndexResult: ...

def forecast_index(index: pd.Series, horizon: int = 3) -> ForecastResult: ...

def rolling_validate(
    index: pd.Series, horizons: tuple[int, ...] = (1, 2, 3)
) -> pd.DataFrame: ...
```

**规则：**

1. 只使用 `quality_flag == "ok"` 的月份和五个核心字段。
2. `StandardScaler` 只在训练段拟合，PCA 提取第一主成分。
3. 当主成分与多数正向经济指标方向相反时，整体乘以 `-1`。
4. 以共同样本首个完整年份的平均值缩放为 100。
5. 在小范围候选 SARIMA 中依 AIC/BIC 选择模型；同时和 12 月季节性朴素预测比较。
6. 每个滚动起点记录模型、预测期限、MAE 和 RMSE。

**执行顺序：**

1. 先写测试：指数只使用完整月份，首年均值约为 100；验证结果同时含 `sarima` 和 `seasonal_naive`。
2. 运行两份测试，确认模块不存在时失败。
3. 实现泄漏安全的 PCA、三个月预测和滚动验证。
4. 用合成数据运行测试与命令行端到端检查。
5. 提交：`git commit -m "feat: 添加景气指数与预测"`。

## 任务五：中文图表与 HTML 报告

**新增文件：** `src/anhui_index/report.py`、`tests/test_report.py`。

**修改文件：** `README.md`。

**产出：** `outputs/report.html` 和以下图表：

- `indicator_trends.png`：五个核心指标走势。
- `pca_loadings.png`：主成分载荷。
- `index_forecast.png`：景气指数、预测值与 95% 区间。
- `context.png`：CPI 与季度社零观察。

**报告必须写明：** 样本覆盖期、最新观测月、五个 PCA 输入、模型与季节性朴素基线的误差对比，以及“固定资产投资和利润使用累计增速”的解释限制。

**执行顺序：**

1. 编写测试，验证一个 HTML 文件和四张图均会生成。
2. 运行 `python -m pytest tests/test_report.py -v`，确认实现前失败。
3. 实现中文标题、中文坐标标签和中文文字结论。
4. 运行全部测试：`python -m pytest -v`。
5. 在有真实原始 Excel 后执行完整流水线；没有真实数据时只验证错误信息，绝不伪造报告结论。
6. 提交：`git commit -m "feat: 添加中文分析报告"`。

## 完成条件

- `data/metadata/data_dictionary.xlsx` 已生成，内容为中文。
- 从 `data/raw/` 的官方 Excel 出发，可自动生成 `data/processed/anhui_monthly_indicators.csv`。
- 所有测试通过。
- 报告中的每个指标、图表与数值可追溯到官方名称和处理规则。
- 没有真实数据时，程序清楚说明缺少什么文件，而不杜撰结果。
