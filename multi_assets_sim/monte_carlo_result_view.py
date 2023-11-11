import pandas as pd
import matplotlib
from matplotlib import rcParams
import matplotlib.pyplot as plt
import flet as ft
from flet.matplotlib_chart import MatplotlibChart
from .table_keys import DataFrameKey

rcParams["font.family"] = "sans-serif"
rcParams["font.sans-serif"] = [
    "Hiragino Maru Gothic Pro",
    "Yu Gothic",
    "Meirio",
    "Takao",
    "IPAexGothic",
    "IPAPGothic",
    "VL PGothic",
    "Noto Sans CJK JP",
]


class MonteCarloResultView(ft.UserControl):
    """モンテカルロシミュレーションの結果表示用View

    Args:
        ft (_type_): _description_
    """

    def __init__(self, is_web: bool):
        matplotlib.use("svg")

        super().__init__()
        self.df_result_desc = None
        self.df_persentile_hisotry = None
        self.df_persentile_eachtime = None

        self.graph_eachtime = True
        self.is_web = is_web

    def build(self):
        self.dtbl = ft.DataTable()  # DataTableは単独ではスクロールできないのでRowなりColumnなりでラッパー作る

        self.graph_type = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="History", label="最終年のみのパーセンタイル"),
                    ft.Radio(value="EachTime", label="毎年のパーセンタイル"),
                ],
                # alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="EachTime",
            on_change=self.onchange_graph_type,
        )

        fig = plt.figure()
        self.chart = MatplotlibChart(figure=fig, expand=True)

        self.row_main = ft.ResponsiveRow(
            [
                ft.Row(
                    [self.dtbl],
                    scroll=ft.ScrollMode.AUTO,
                    # alignment=ft.MainAxisAlignment.CENTER,
                    col={"lg": 6},
                ),
                ft.Column(
                    [
                        ft.Container(self.graph_type),
                        ft.Container(self.chart, width=600),
                    ],
                    # horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    col={"lg": 6},
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Error用ダイアログ
        self.err_dlg = ft.AlertDialog(title="Error!")

        # フッター部分
        ## 結果のDataFrameの保存
        self.save_df_dialog = ft.FilePicker(on_result=self.save_df_result)
        self.btn_save_df = ft.ElevatedButton("Save Table", on_click=self.save_df)
        ## 結果のグラフの保存
        self.save_plot_dialog = ft.FilePicker(on_result=self.save_plot_result)
        self.btn_save_plot = ft.ElevatedButton("Save Plot", on_click=self.save_plot)
        if self.is_web is True:
            # Web版だとFilePickerはUploadできてもSaveはできないので非表示にしておく
            self.btn_save_df.visible = False
            self.btn_save_plot.visible = False

        self.row_foot = ft.Row([self.btn_save_df, self.btn_save_plot])

        return ft.Column([self.row_main, self.row_foot])

    def did_mount(self):
        """pageにmountされた後の処理。
        Overlayへ追加が必要なControl(FilePickerなど)を追加する
        """
        self.page.overlay.append(self.save_df_dialog)
        self.page.overlay.append(self.save_plot_dialog)
        self.page.update()

    def onchange_graph_type(self, e):
        """グラフ種類の選択ボタンが変更されたイベント

        Args:
            e (_type_): _description_
        Raises:
            ValueError: _description_
        """
        if e.control.value == "History":
            self.graph_eachtime = False
            self.show_result_plot()
        elif e.control.value == "EachTime":
            self.graph_eachtime = True
            self.show_result_plot()
        else:
            raise ValueError("Irregular Radio Value")

    def show_result_table(self):
        """シミュレーション結果をパーセンタイルごとにテーブルにして結果表示を行う関数"""

        def cell_text(v):
            if isinstance(v, str):
                return v
            elif isinstance(v, int):
                return f"{v:,}"
            else:
                return f"{v:.2%}"

        df = self.df_result_desc[
            [
                DataFrameKey.labels.value,
                DataFrameKey.result.value,
                DataFrameKey.profit.value,
                DataFrameKey.profit_ratio.value,
            ]
        ]
        self.dtbl.columns = [
            ft.DataColumn(ft.Text(c), numeric=True)
            if i > 0
            else ft.DataColumn(ft.Text(c))
            for i, c in enumerate(df.columns)
        ]
        self.dtbl.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(
                            cell_text(v),
                        )
                    )
                    for v in r[1:]
                ]
            )
            for r in df.itertuples()  # (idx, c1, c2, c3,...)
        ]

    def show_result_plot(self, save_fpath: str = None):
        """パーセンタイルをグラフ化して表示する関数。
        ただし、save_figでパスが指定されているならグラフの保存も行う

        Args:
            save_fpath (str, optional): グラフを保存するファイル名. Defaults to None.
        """
        if self.graph_eachtime is True:
            df = self.df_persentile_eachtime
        else:
            df = self.df_persentile_hisotry

        _df = df.drop(columns=[DataFrameKey.passing_year.value])
        year = df[DataFrameKey.passing_year.value]

        fig = plt.figure()
        ax = fig.add_subplot()
        for label, item in _df.items():
            # 利益率を%に直して表示
            r = item * 100
            ax.plot(year, r, label=label)

        ax.legend()
        ax.set_title("モンテカルロシミュレーション結果")
        ax.set_ylabel("累積利益率[%]")
        ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
        ax.set_xlabel("年数[年]")
        fig.tight_layout()

        # ファイル名が指定されていたら保存する
        if save_fpath is not None:
            fig.savefig(save_fpath, dpi=300)

        self.chart.figure = fig
        self.update()

    def set_sim_result(
        self,
        df_result_desc: pd.DataFrame,
        df_persentile_eachtime: pd.DataFrame,
        df_persentile_hisotry: pd.DataFrame,
    ):
        """シミュレーション結果をセットする関数

        Args:
            df_result_desc (pd.DataFrame): _description_
            df_persentile_eachtime (pd.DataFrame): _description_
            df_persentile_hisotry (pd.DataFrame): _description_
        """
        self.df_result_desc = df_result_desc
        self.df_persentile_eachtime = df_persentile_eachtime
        self.df_persentile_hisotry = df_persentile_hisotry

        self.show_result_table()
        self.show_result_plot()

        self.update()

    def has_result(self) -> bool:
        """シミュレーション結果を保持しているかboolで返す関数

        Returns:
            bool: シミュレーション結果を保持しているかどうか
        """
        if (
            self.df_result_desc is None
            or self.df_persentile_eachtime is None
            or self.df_persentile_hisotry is None
        ):
            return False
        else:
            return True

    def open_err_dlg(self, msg: str):
        """指定されたメッセージでError Dialogを開く関数

        Args:
            msg (str): エラー内容のメッセージ
        """
        self.err_dlg.content = ft.Text(msg)
        self.page.dialog = self.err_dlg
        self.err_dlg.open = True
        self.page.update()

    def save_df_result(self, e: ft.FilePickerResultEvent):
        """FilePickerの結果をもとに、DFの保存を行う関数

        Args:
            e (ft.FilePickerResultEvent): save_file()の結果を想定している
        """
        try:
            fpath = e.path
            if fpath:
                self.df_result_desc.to_csv(fpath, index=False)
        except Exception as e:
            self.open_err_dlg(f"保存中にエラーが発生しました: {e}")

    def save_df(self, e):
        """DataFrameの保存を行う関数。"""
        if self.df_result_desc is None:
            self.open_err_dlg("シミュレーション結果が存在しません")
        else:
            self.save_df_dialog.save_file(
                allowed_extensions=["csv"],
                file_name="result_table.csv",
                dialog_title="Save Result Table",
            )

    def save_plot_result(self, e: ft.FilePickerResultEvent):
        """FilePickerの結果をもとに、グラフの保存を行う関数

        Args:
            e (ft.FilePickerResultEvent): save_file()の結果を想定している
        """
        try:
            fpath = e.path
            if fpath:
                self.show_result_plot(fpath)
        except Exception as e:
            self.open_err_dlg(f"保存中にエラーが発生しました: {e}")

    def save_plot(self, e):
        """Plotの保存を行う関数。"""
        if self.df_result_desc is None:
            self.open_err_dlg("シミュレーション結果が存在しません")
        else:
            self.save_plot_dialog.save_file(
                allowed_extensions=[
                    "png",
                    "svg",
                    "jpg",
                    "pdf",
                    "ps",
                    "emf",
                    "eps",
                    "raw",
                    "rgba",
                    "svgz",
                    "tif",
                    "tiff",
                ],
                file_name="result_graph.png",
                dialog_title="Save Result Graph",
            )
