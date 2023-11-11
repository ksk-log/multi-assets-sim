from enum import Enum


class CtrlKey(Enum):
    profit = "profit"
    risk = "risk"
    year = "year"
    start = "start"
    month = "month"
    size = "size"
    percentiles = "percentiles"


class DataFrameKey(Enum):
    percentile = "パーセンタイル"
    labels = "運用成績"
    result = "結果[円]"
    profit = "利益[円]"
    profit_ratio = "累積利益率"
    passing_year = "経過年数"
