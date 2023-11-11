import numpy as np
import pandas as pd
from .monte_carlo_param import MonteCarloParam
from multi_assets_sim.table_keys import DataFrameKey


class MonteCarloSim:
    """モンテカルロシミュレーションを行うクラス"""

    def __init__(self):
        self.param = MonteCarloParam()
        self.result = None
        self.org = None  # 元本計算用

    def set_param(self, param: MonteCarloParam):
        """Dataclassを用いてパラメータのセットを行う関数

        Args:
            param (MonteCarloParam): _description_
        """
        self.param = param

    def simulate(self):
        """積立資産のモンテカルロシミュレーションを行う関数。途中経過も残すためメモリ量に注意"""
        rng = np.random.default_rng()

        year = self.param.year
        size = self.param.size
        profit = self.param.profit
        risk = self.param.risk
        month = self.param.month
        start = self.param.start

        # 元本
        org = np.arange(1, year + 1) * 12 * month + start
        # シミュレーションパターン
        pattern = np.zeros((year, size))

        for i in range(year):
            c = rng.normal(loc=1 + profit, scale=risk, size=size)
            if i == 0:
                pattern[i, :] = (start + 12.0 * month) * c
            else:
                pattern[i, :] = (pattern[i - 1, :] + 12.0 * month) * c  # 要素積
        # print(pattern)

        self.result = pattern
        self.org = org

    def has_result(self) -> bool:
        """シミュレーション結果を保持しているかどうか

        Returns:
            bool: _description_
        """
        if self.result is None:
            return False
        else:
            return True

    def get_result(self) -> np.ndarray:
        """シミュレーション結果のndarrayを返す関数

        Raises:
            ValueError: _description_

        Returns:
            np.ndarray: _description_
        """
        if self.result is None:
            raise ValueError("Simulation result is not Calculated")
        return self.result

    def _get_percentile_label(self, i: int) -> str:
        """パーセンタイルの値を表示用に整形する。
        50を中央値、1~49を下位1~49%, 51~99を上位49~1%とする

        Args:
            i (int): Percentilの値。0~100のint想定

        Returns:
            str: 表示用に整形した文字列
        """
        if i > 50:
            return f"上位{100-i}%"
        elif i == 50:
            return "中央値"
        else:
            return f"下位{i}%"

    def get_percentile_describe(self) -> pd.DataFrame:
        """パーセンタイルと分析値を作成してDataFrameとして返す

        Raises:
            ValueError: _description_

        Returns:
            pd.DataFrame: _description_
        """
        if self.result is None or self.org is None:
            raise ValueError("Simulation result is not Calculated")
        idxs = self.param.percentiles
        labels = [self._get_percentile_label(i) for i in idxs]
        pers = np.percentile(self.result[-1, :], idxs, method="nearest").astype(int)
        diff = pers - self.org[-1]
        plus_ratio = diff / self.org[-1]
        df = pd.DataFrame(
            {
                DataFrameKey.percentile.value: idxs,
                DataFrameKey.labels.value: labels,
                DataFrameKey.result.value: pers,
                DataFrameKey.profit.value: diff,
                DataFrameKey.profit_ratio.value: plus_ratio,
            }
        )
        df.sort_values(DataFrameKey.result.value, inplace=True, ascending=False)
        df.reset_index(inplace=True, drop=True)
        # print(df)
        return df

    def get_percentile_history(self):
        """パーセンタイルを計算し、その利益率の推移をDataFrameとして返す。
        なお、パーセンタイルは最終結果から計算し、それに対応する過去の履歴を使っている。
        その時点時点でのパーセンタイルを使う場合は別の関数を利用する。

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        if self.result is None and self.org is None:
            raise ValueError("Simulation result is not Calculated")
        idxs = self.param.percentiles
        last = self.result[-1, :]
        pers = np.percentile(last, idxs, method="nearest")
        data = {}
        for i, p in zip(idxs, pers):
            i_p = np.where(last == p)[0][0]  # 一致するidxを探す(2次元タプルを外してる)
            # 利益率に変換
            data[self._get_percentile_label(i)] = (
                self.result[:, i_p] - self.org
            ) / self.org
        data[DataFrameKey.passing_year.value] = np.arange(1, self.param.year + 1)
        df = pd.DataFrame(data)
        return df

    def get_percentile_eachtime(self):
        """パーセンタイルを計算し、その利益率の推移をDataFrameとして返す。
        なお、パーセンタイルはその時刻ごとに計算している。

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        if self.result is None and self.org is None:
            raise ValueError("Simulation result is not Calculated")
        idxs = self.param.percentiles
        src = np.zeros((self.param.year, len(idxs)))
        for i in range(self.param.year):
            src[i, :] = np.percentile(self.result[i, :], idxs, method="nearest")
            # 利益率に変換
            src[i, :] = (src[i, :] - self.org[i]) / self.org[i]

        cols = [self._get_percentile_label(p) for p in idxs]
        df = pd.DataFrame(data=src, columns=cols)
        df[DataFrameKey.passing_year.value] = np.arange(1, self.param.year + 1)
        # print(df)
        return df

    def get_hist(self) -> (np.ndarray, np.ndarray):
        if self.result is None:
            raise ValueError("Simulation result is not Calculated")
        h, b = np.histogram(self.result[-1, :], bins="sturges", density=True)
        return h, b


def monte_carlo_sim_by_param(param: MonteCarloParam) -> np.ndarray:
    """積立資産のモンテカルロシミュレーションを行う関数

    Args:
        param (MonteCarloParam): シミュレーション用パラメータ

    Returns:
        np.ndarray: _description_
    """
    return monte_carlo_sim(
        param.profit, param.risk, param.year, param.start, param.month, param.size
    )


def monte_carlo_sim(
    profit: float = 0.05,
    risk: float = 0.23,
    year: int = 20,
    start: int = 0,
    month: int = 30000,
    size: int = 10_000,
) -> np.ndarray:
    """積立資産のモンテカルロシミュレーションを行う関数

    Args:
        profit (float, optional): 資産の平均リターン. Defaults to 0.05.
        risk (float, optional): 資産のリスク(標準偏差). Defaults to 0.23.
        year (int, optional): 投資年数. Defaults to 20.
        start (int, optional): 初期投資額. Defaults to 0.
        month (int, optional): 毎月の積立額. Defaults to 30000.
        size (int, optional): シミュレーションを行う要素数. Defaults to 10_000.

    Returns:
        np.ndarray: _description_
    """
    # 平均(loc)=5.6%, 標準偏差(scale)=23%
    rng = np.random.default_rng()

    # 元本
    org = start
    # シミュレーションパターン
    pattern = None

    for _ in range(year):
        c = rng.normal(loc=1 + profit, scale=risk, size=size)
        if pattern is None:
            pattern = (start + 12.0 * month) * c
        else:
            pattern = (pattern + 12.0 * month) * c  # 要素積
        org += 12 * month
    # print(pattern)

    return pattern


def monte_carlo_sim_matrix(
    profit: float = 0.05,
    risk: float = 0.23,
    year: int = 20,
    start: int = 0,
    month: int = 30000,
    size: int = 10_000,
) -> np.ndarray:
    """積立資産のモンテカルロシミュレーションを行う関数。途中経過も残すためメモリ量に注意

    Args:
        profit (float, optional): 資産の平均リターン. Defaults to 0.05.
        risk (float, optional): 資産のリスク(標準偏差). Defaults to 0.23.
        year (int, optional): 投資年数. Defaults to 20.
        start (int, optional): 初期投資額. Defaults to 0.
        month (int, optional): 毎月の積立額. Defaults to 30000.
        size (int, optional): シミュレーションを行う要素数. Defaults to 10_000.

    Returns:
        np.ndarray: _description_
    """
    # 平均(loc)=5.6%, 標準偏差(scale)=23%
    rng = np.random.default_rng()

    # 元本
    org = start
    # シミュレーションパターン
    pattern = np.zeros((year, size))

    for i in range(year):
        c = rng.normal(loc=1 + profit, scale=risk, size=size)
        if i == 0:
            pattern[i, :] = (start + 12.0 * month) * c
        else:
            pattern[i, :] = (pattern[i - 1, :] + 12.0 * month) * c  # 要素積
        org += 12 * month
    # print(pattern)

    return pattern
