import yaml
from dataclasses import dataclass, asdict, field


@dataclass
class MonteCarloParam:
    profit: float = 0.05
    risk: float = 0.23
    year: int = 20
    start: int = 0
    month: int = 30000
    size: int = 10_000

    # 3σっぽくしてみる,
    # ±1σで68.4: 50を中心として16と84
    # ±2σで95.4: 50を中心として3と97
    # ±3σで99.7: 50を中心として1と99
    percentiles: list[int] = field(default_factory=lambda: [99, 97, 84, 50, 16, 3, 1])

    @classmethod
    def load_param(cls, fname: str):
        """Yamlファイルから設定を読み込む関数

        Args:
            fname (str): yamlファイル名

        Returns:
            MonteCarloParam: _description_
        """
        with open(fname, encoding="utf-8", mode="r") as f:
            data = yaml.safe_load(f)
            param = MonteCarloParam(**data)
            return param

    def save_param(self, fname: str):
        """Yamlファイルへ設定を保存する関数

        Args:
            fname (str): yamlファイル名
        """
        with open(fname, encoding="utf-8", mode="w") as f:
            yaml.safe_dump(asdict(self), f, allow_unicode=True, default_flow_style=None)

    def check_types(self):
        """パラメータの型が正常化確認する。

        Raises:
            ValueError: _description_
        """
        if isinstance(self.profit, float) is False:
            raise ValueError("profit must be float")
        if isinstance(self.risk, float) is False:
            raise ValueError("risk must be float")
        if isinstance(self.year, int) is False:
            raise ValueError("year must be int")
        if isinstance(self.start, int) is False:
            raise ValueError("start asset must be float")
        if isinstance(self.month, int) is False:
            raise ValueError("month must be int")
        if isinstance(self.size, int) is False:
            raise ValueError("size must be int")
        if isinstance(self.percentiles, list) is False:
            raise ValueError("percentile must be list")
        if any([isinstance(p, int) is False for p in self.percentiles]):
            raise ValueError("percentile must be list of int")
        return
