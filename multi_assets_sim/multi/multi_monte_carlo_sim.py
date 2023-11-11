import numpy as np
import pandas as pd
from .multi_monte_carlo_param import MultiMonteCarloParam
from multi_assets_sim.table_keys import DataFrameKey


class MultiMonteCarloSim:
    """相関を持つ複数アセットでモンテカルロシミュレーションを行うクラス"""

    def __init__(self):
        self.param = None
        self.all_pattern = None
        self.result = None
        self.org = None  # 元本計算用

    def set_param(self, param: MultiMonteCarloParam):
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
        means = self.param.profits
        cov = self.param.cov
        ratio = self.param.ratios
        rebalance = self.param.rebalance
        month = self.param.month
        start = self.param.start
        assets_len = len(self.param.labels)

        # 元本
        org = np.arange(1, year + 1) * 12 * month + start

        # シミュレーションパターン
        pattern = np.zeros((year, size, assets_len))

        for i in range(year):
            vals = rng.multivariate_normal(
                1 + means, cov, size=size
            )  # (size,asset_len)
            if i == 0:
                prev = (
                    np.ones((size, assets_len)) * (start + 12.0 * month) * ratio
                )  # (size, asset_len)
            else:
                if rebalance is False:
                    prev = pattern[i - 1, :] + (12.0 * month) * ratio
                else:
                    sums = pattern[i - 1, :].sum(axis=1)  # シミュレーションパターンごとに資産額を合計(size)
                    reb = (
                        sums[:, np.newaxis] * ratio
                    )  # sums(size,)->(size,1)と列ベクトルに拡張し、行ベクトルratio(asset_len,)と乗算してリバランス後の値を計算(size, asset_len)
                    prev = reb + (12.0 * month) * ratio

            pattern[i, :] = prev * vals  # 要素積

        # 全パターンを記録
        self.all_pattern = pattern
        # 各年,各パターンごとに資産合計を取って利益計算(year, size)。これでsingle互換の結果
        self.result = pattern.sum(axis=2)
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
