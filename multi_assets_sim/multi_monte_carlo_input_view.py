import flet as ft
from typing import Callable
from .multi.multi_monte_carlo_param import MultiMonteCarloParam
from . import validate
from .table_keys import CtrlKey
from .cor_table_view import CorrelationTableView


class MultiMonteCarloInputView(ft.UserControl):
    """複数アセットのモンテカルロシミュレーションのパラメータ入力用View

    Args:
        ft (_type_): _description_
    """

    def __init__(
        self, is_web: bool, sim_evt_fn: Callable[[MultiMonteCarloParam], None]
    ):
        super().__init__()
        self.sim_param = MultiMonteCarloParam()
        self.sim_evt_fn = sim_evt_fn
        self.is_web = is_web

    def build(self):
        self.mc_result = None
        self.tf = {}

        self.tf[CtrlKey.year] = ft.TextField(
            label="operation year",
            hint_text="operation year",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=validate.textfield_int_changed,
            value=str(self.sim_param.year),
        )

        self.tf[CtrlKey.start] = ft.TextField(
            label="first amount of assets",
            hint_text="the amount of first assets",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=validate.textfield_int_changed,
            value=str(self.sim_param.start),
        )

        self.tf[CtrlKey.month] = ft.TextField(
            label="save / month",
            hint_text="amount of reserve money per month",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=validate.textfield_int_changed,
            value=str(self.sim_param.month),
        )
        self.tf[CtrlKey.size] = ft.TextField(
            label="simulation size",
            hint_text="size of monte carlo simulation: recomended 5000-10000",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=validate.textfield_int_changed,
            value=str(self.sim_param.size),
        )
        self.tf[CtrlKey.percentiles] = ft.TextField(
            label="percentiles",
            hint_text="value list of percentiles: ex 99, 97, 84, 50, 16, 3, 1",
            keyboard_type=ft.KeyboardType.TEXT,
            on_change=validate.textfield_percentile_changed,
            value=str(",".join([f"{p}" for p in self.sim_param.percentiles])),
        )
        self.cb_rebalance = ft.Checkbox(
            label="毎年資産構成に従ってリバランスする", value=self.sim_param.rebalance
        )
        labels = {
            CtrlKey.year: "運用年数",
            CtrlKey.start: "開始時資産",
            CtrlKey.month: "毎月積立額",
            CtrlKey.size: "シミュレーション数",
            CtrlKey.percentiles: "パーセンタイル",
        }

        # 相関入力ビュー
        self.cor_view = CorrelationTableView()
        self.cor_view.set_param(self.sim_param)

        # ボタン類
        self.btn_sim = ft.ElevatedButton("Simulate", on_click=self.click_sim)
        ## Paramの保存
        self.save_param_dialog = ft.FilePicker(on_result=self.save_param_result)
        self.btn_save_param = ft.ElevatedButton("Save YAML", on_click=self.save_param)
        ## Paramの保存
        self.load_param_dialog = ft.FilePicker(on_result=self.load_param_result)
        self.btn_load_param = ft.ElevatedButton("Load YAML", on_click=self.load_param)
        if self.is_web is True:
            # Web版だとFilePickerはUploadできてもSaveはできないので非表示にしておく
            self.btn_save_param.visible = False
            self.btn_load_param.visible = False

        # Error用ダイアログ
        self.err_dlg = ft.AlertDialog(title=ft.Text("Error!"))

        # 各行のコントロールを作成
        ckey = [
            CtrlKey.year,
            CtrlKey.start,
            CtrlKey.month,
            CtrlKey.size,
            CtrlKey.percentiles,
        ]
        ctrls = [
            ft.Row(
                [
                    ft.Text(labels[k], width=100),
                    self.tf[k],
                ],
            )
            for k in ckey
        ]
        ctrls.append(ft.Row([self.cb_rebalance]))
        ctrls.append(ft.ResponsiveRow([self.cor_view]))
        ctrls.append(ft.Row([self.btn_sim, self.btn_save_param, self.btn_load_param]))
        return ft.Column(ctrls)

    def did_mount(self):
        """pageにmountされた後の処理。
        Overlayへ追加が必要なControl(FilePickerなど)を追加する
        """
        self.page.overlay.append(self.save_param_dialog)
        self.page.overlay.append(self.load_param_dialog)
        self.page.update()

    def click_sim(self, e):
        """シミュレーションボタン実行時の動作

        Args:
            e (_type_): _description_
        """
        if self._set_param() is True:
            self.sim_evt_fn(self.sim_param)
        else:
            self.open_err_dlg("入力したシミュレーションパラメータの値が不正です")

    def open_err_dlg(self, msg: str):
        """指定されたメッセージでError Dialogを開く関数

        Args:
            msg (str): エラー内容のメッセージ
        """
        self.err_dlg.content = ft.Text(msg)
        self.page.dialog = self.err_dlg
        self.err_dlg.open = True
        self.page.update()

    def _set_param(self) -> bool:
        """入力からパラメータをセットして、正しく数値に変換できなければFalseを返す

        Returns:
            bool: TextFieldの入力が正しくパラメータに変換できればTrue,そうでなければFalseを返す
        """
        try:
            self.sim_param.year = int(self.tf[CtrlKey.year].value)
            self.sim_param.start = int(self.tf[CtrlKey.start].value)
            self.sim_param.month = int(self.tf[CtrlKey.month].value)
            self.sim_param.size = int(self.tf[CtrlKey.size].value)
            self.sim_param.percentiles = [
                int(p) for p in self.tf[CtrlKey.percentiles].value.split(",")
            ]
            self.sim_param.rebalance = self.cb_rebalance.value

            p = self.cor_view.get_param()
            self.sim_param.cor = p.cor
            self.sim_param.cov = p.cov
            self.sim_param.labels = p.labels
            self.sim_param.ratios = p.ratios
            self.sim_param.profits = p.profits
            self.sim_param.stds = p.stds

            self.sim_param.check_types()
            return True
        except ValueError:
            return False

    def save_param_result(self, e: ft.FilePickerResultEvent):
        """FilePickerの結果をもとに、Paramの保存を行う関数

        Args:
            e (ft.FilePickerResultEvent): save_file()の結果を想定している
        """
        try:
            fpath = e.path
            if fpath:
                self.sim_param.save_yaml(fpath)
        except Exception as e:
            self.open_err_dlg(f"保存中にエラーが発生しました: {e}")

    def save_param(self, e):
        """Paramの保存を行う関数。"""

        if self._set_param() is True:
            self.save_param_dialog.save_file(
                allowed_extensions=["yml"],
                file_name="sim_param.yml",
                dialog_title="Save Simulation Param",
            )
        else:
            self.open_err_dlg("入力したシミュレーションパラメータの値が不正です")

    def load_param_result(self, e: ft.FilePickerResultEvent):
        """FilePickerの結果をもとに、Paramの読込を行う関数

        Args:
            e (ft.FilePickerResultEvent): pick_files()の結果を想定している
        """
        try:
            if e.files is None:
                return
            fpath = e.files[0].path
            if fpath:
                self.sim_param = MultiMonteCarloParam.load_yaml(fpath)
                self.tf[CtrlKey.year].value = str(self.sim_param.year)
                self.tf[CtrlKey.start].value = str(self.sim_param.start)
                self.tf[CtrlKey.month].value = str(self.sim_param.month)
                self.tf[CtrlKey.size].value = str(self.sim_param.size)
                self.tf[CtrlKey.percentiles].value = ",".join(
                    [f"{p}" for p in self.sim_param.percentiles]
                )
                self.cb_rebalance.value = self.sim_param.rebalance
                self.cor_view.set_param(self.sim_param)
                self.cor_view.update_view()
                self.update()
        except Exception as e:
            self.open_err_dlg(f"読込中にエラーが発生しました: {e}")

    def load_param(self, e):
        """Paramの読込を行う関数。"""
        self.load_param_dialog.pick_files(
            allowed_extensions=["yml"],
            dialog_title="Load Simulation Param",
        )
