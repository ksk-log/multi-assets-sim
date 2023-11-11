import yaml
import numpy as np
import pandas as pd
from dataclasses import dataclass, field, asdict


@dataclass
class MultiMonteCarloParam:
    """エクセルで指定する相関を持つ複数アセットのモンテカルロシミュレーション用パラメータ

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """

    profits: np.ndarray = field(
        default_factory=lambda: np.array([-0.016, 0.003, 0.033, 0.049])
    )  # リターン
    stds: np.ndarray = None
    cov: np.ndarray = field(
        default_factory=lambda: np.array(
            [
                [0.00065536, 0.00088123, -0.00093597, 0.00066797],
                [0.00088123, 0.01408969, 0.00164803, 0.01725572],
                [-0.00093597, 0.00164803, 0.05354596, 0.03697436],
                [0.00066797, 0.01725572, 0.03697436, 0.06175225],
            ]
        )
    )  # 共分散行列
    cor: np.ndarray = field(
        default_factory=lambda: np.array(
            [
                [1.0, 0.29, -0.158, 0.105],
                [0.29, 1.0, 0.06, 0.585],
                [-0.158, 0.06, 1.0, 0.643],
                [0.105, 0.585, 0.643, 1.0],
            ]
        )
    )  # 相関係数
    year: int = 20
    start: int = 0
    month: int = 30000
    size: int = 10_000
    rebalance: bool = True

    # 3σっぽくしてみる,
    # ±1σで68.4: 50を中心として16と84
    # ±2σで95.4: 50を中心として3と97
    # ±3σで99.7: 50を中心として1と99
    percentiles: list[int] = field(default_factory=lambda: [99, 97, 84, 50, 16, 3, 1])

    # 資産ラベル
    labels: list[str] = field(default_factory=lambda: ["国内債券", "外国債券", "国内株式", "外国株式"])

    # 構成比率
    ratios: np.ndarray = field(
        default_factory=lambda: np.array([0.25, 0.25, 0.25, 0.25])
    )

    def __post_init__(self):
        if self.stds is None:
            self.stds = self.get_stds()

    def get_stds(self) -> np.ndarray:
        """標準偏差を計算して返す関数

        Returns:
            np.ndarray: _description_
        """
        stds = np.sqrt(np.diagonal(self.cov))  # 標準偏差を抽出
        return stds

    @staticmethod
    def get_covs(cor: np.ndarray, stds: np.ndarray) -> np.ndarray:
        """相関行列から共分散行列を計算して返す関数

        Args:
            cor (np.ndarray): 相関行列
            stds (np.ndarray): 標準偏差

        Returns:
            np.ndarray: _description_
        """

        cov = np.zeros_like(cor)

        for i in range(cor.shape[0]):
            for j in range(cor.shape[1]):
                cov[i, j] = cor[i, j] * stds[i] * stds[j]
        return cov

    def calc_cor_from_tril(self):
        """相関行列の下三角行列から、対称行列として相関行列を再構成する"""
        tril = np.tril(self.cor)  # 下三角行列の抽出
        self.cor = (
            tril + tril.T - np.diag(np.diagonal(tril))
        )  # 下三角行列 + その転置 - 対角成分で対称行列にできる

    def calc_cov_from_cor(self):
        """相関行列と標準偏差から、共分散行列を再構成する"""
        self.cov = MultiMonteCarloParam.get_covs(self.cor, self.stds)

    def add_items(self):
        """要素数を1つ追加する"""
        prev_dim = self.cor.shape[0]

        self.labels.append("")
        self.profits = np.append(self.profits, 0.0)
        self.stds = np.append(self.stds, 0.01)
        self.ratios = np.append(self.ratios, 0.0)

        # 1行1列ずつ拡張する
        self.cor = np.append(self.cor, np.zeros((prev_dim, 1)), axis=1)
        self.cor = np.append(self.cor, np.zeros((1, prev_dim + 1)), axis=0)
        self.cor[prev_dim, prev_dim] = 1.0

        self.cov = np.append(self.cov, np.zeros((prev_dim, 1)), axis=1)
        self.cov = np.append(self.cov, np.zeros((1, prev_dim + 1)), axis=0)

    def remove_items(self):
        """要素数を1つ削除する"""

        self.labels.pop()

        self.profits = self.profits[:-1]
        self.stds = self.stds[:-1]
        self.ratios = self.ratios[:-1]

        # 1行1列ずつ削除する
        self.cor = self.cor[:-1, :-1]
        self.cov = self.cov[:-1, :-1]

    @classmethod
    def load_excel(cls, fpath: str):
        """エクセルからパラメータ情報を読み込む関数

        Args:
            fpath (str): ファイル名

        Returns:
            MultiMonteCarloParam: _description_
        """
        # 基本パラメータ
        df_param = pd.read_excel(fpath, sheet_name="sim_param", index_col=None)
        year = int(df_param["year"][0])
        start = int(df_param["start"][0])
        month = int(df_param["month"][0])
        size = int(df_param["size"][0])
        rebalance = bool(df_param["rebalance"][0])

        # アセット情報
        df_info = pd.read_excel(fpath, sheet_name="asset_info", index_col=0)
        labels = df_info.index.values.tolist()  # ndarray
        profits = df_info["リターン"].values
        stds = df_info["標準偏差"].values
        ratios = df_info["構成比率"].values

        # パーセンタイル
        df_pers = pd.read_excel(fpath, sheet_name="percentiles", index_col=None)
        percentiles = df_pers["パーセンタイル"].values.tolist()

        # 相関係数を読込
        df_cor = pd.read_excel(fpath, sheet_name="correlation", index_col=None)
        np_cor = df_cor.values

        # 相関係数の対称行列に変換
        tril = np.tril(np_cor)  # 下三角行列の抽出
        cor = tril + tril.T - np.diag(np.diagonal(tril))  # 下三角行列 + その転置 - 対角成分で対称行列にできる

        # 共分散行列に変換
        cov = MultiMonteCarloParam.get_covs(cor, stds)

        param = MultiMonteCarloParam(
            profits=profits,
            stds=stds,
            cov=cov,
            cor=cor,
            year=year,
            start=start,
            month=month,
            size=size,
            rebalance=rebalance,
            labels=labels,
            ratios=ratios,
            percentiles=percentiles,
        )
        param.check_types()

        return param

    def save_excel(self, fname: str):
        """シート名でパラメータを分けて1つのエクセルファイルに保存するクラス

        Args:
            fname (str): _description_
        """
        self.check_types()

        df_param = pd.DataFrame(
            {
                "year": [self.year],
                "start": [self.start],
                "month": self.month,
                "size": self.size,
                "rebalance": self.rebalance,
            }
        )
        df_pers = pd.DataFrame({"パーセンタイル": self.percentiles})

        df_info = pd.DataFrame(
            {"リターン": self.profits, "標準偏差": self.stds, "構成比率": self.ratios},
            index=self.labels,
        )
        df_cor = pd.DataFrame(self.cor, columns=self.labels)
        with pd.ExcelWriter(fname) as writer:
            df_param.to_excel(writer, sheet_name="sim_param", index=False)
            df_info.to_excel(writer, sheet_name="asset_info")
            df_pers.to_excel(writer, sheet_name="percentiles", index=False)
            df_cor.to_excel(writer, sheet_name="correlation", index=False)

    @classmethod
    def load_yaml(cls, fname: str):
        """Yamlファイルから設定を読み込む関数

        Args:
            fname (str): yamlファイル名

        Returns:
            MonteCarloParam: _description_
        """
        with open(fname, encoding="utf-8", mode="r") as f:
            data = yaml.safe_load(f)
            stds = np.array(data["stds"])
            profits = np.array(data["profits"])
            ratios = np.array(data["ratios"])
            np_cor = np.array(data["cor"])

            # 相関係数の対称行列に変換
            tril = np.tril(np_cor)  # 下三角行列の抽出
            cor = (
                tril + tril.T - np.diag(np.diagonal(tril))
            )  # 下三角行列 + その転置 - 対角成分で対称行列にできる

            # 共分散行列に変換
            cov = MultiMonteCarloParam.get_covs(cor, stds)

            param = MultiMonteCarloParam(
                profits=profits,
                stds=stds,
                cov=cov,
                cor=cor,
                year=data["year"],
                start=data["start"],
                month=data["month"],
                size=data["size"],
                rebalance=data["rebalance"],
                labels=data["labels"],
                ratios=ratios,
                percentiles=data["percentiles"],
            )
            param.check_types()
            return param

    def save_yaml(self, fname: str):
        """Yamlファイルへ設定を保存する関数

        Args:
            fname (str): yamlファイル名
        """
        with open(fname, encoding="utf-8", mode="w") as f:
            d = asdict(self)
            del d["cov"]  # corから計算するので除外
            d["stds"] = self.stds.tolist()
            d["profits"] = self.profits.tolist()
            d["cor"] = self.cor.tolist()
            d["ratios"] = self.ratios.tolist()
            yaml.safe_dump(d, f, allow_unicode=True, default_flow_style=None)

    def check_types(self):
        """型チェックを行う関数

        Raises:
            ValueError: _description_
        """
        dim = len(self.labels)
        if isinstance(self.year, int) is False:
            raise ValueError("year must be int")
        if isinstance(self.start, int) is False:
            raise ValueError("start asset must be float")
        if isinstance(self.month, int) is False:
            raise ValueError("month must be int")
        if isinstance(self.size, int) is False:
            raise ValueError("size must be int")
        if isinstance(self.rebalance, bool) is False:
            raise ValueError("rebalance must be bool")
        if isinstance(self.percentiles, list) is False:
            raise ValueError("percentile must be list")
        if any([isinstance(p, int) is False for p in self.percentiles]):
            raise ValueError("percentile must be list of int")
        # 行列チェック
        if self.cov.shape != (dim, dim):
            raise ValueError(f"cov matrix shape must be ({dim},{dim})")
        if self.cor.shape != (dim, dim):
            raise ValueError(f"cor matrix shape must be ({dim},{dim})")
        if len(self.labels) != dim:
            raise ValueError(f"assets label length must be {dim}")
        if len(self.ratios) != dim:
            raise ValueError(f"assets ratios length must be {dim}")
        if len(self.profits) != dim:
            raise ValueError(f"assets profits length must be {dim}")
        if len(self.stds) != dim:
            raise ValueError(f"assets stds length must be {dim}")
        return
