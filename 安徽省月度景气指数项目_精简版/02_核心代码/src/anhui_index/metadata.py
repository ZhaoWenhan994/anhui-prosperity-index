from dataclasses import dataclass


SOURCE_URL = "https://data.stats.gov.cn/"


@dataclass(frozen=True)
class IndicatorSpec:
    key: str
    official_name: str
    frequency: str
    definition: str
    direction: str
    included_in_pca: bool
    transform: str


INDICATORS = (
    IndicatorSpec("industrial_yoy", "工业增加值同比增长 (%)", "月度", "当月同比（%）", "正向", True, "不转换"),
    IndicatorSpec("investment_cum_yoy", "固定资产投资完成额累计增长 (%)", "月度", "累计同比（%）", "正向", True, "不转换"),
    IndicatorSpec("profit_cum_yoy", "利润总额累计增长 (%)", "月度", "累计同比（%）", "正向", True, "不转换"),
    IndicatorSpec("power_yoy", "发电量同比增长 (%)", "月度", "当月同比（%）", "正向", True, "不转换"),
    IndicatorSpec("ppi_yoy", "工业生产者出厂价格指数 (上年同月=100)", "月度", "上年同月=100", "正向", True, "数值减 100"),
    IndicatorSpec("cpi_yoy", "居民消费价格指数", "月度", "上年同月=100", "辅助", False, "不转换"),
    IndicatorSpec("retail_quarterly_yoy", "社会消费品零售总额累计增长 (%)", "季度", "累计同比（%）", "辅助", False, "不转换"),
)
