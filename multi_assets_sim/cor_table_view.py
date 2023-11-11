import copy
import numpy as np
import flet as ft
from . import validate
from .multi import MultiMonteCarloParam


class CorrelationTableView(ft.UserControl):
    """相関行列を入力するためのView

    Args:
        ft (_type_): _description_
    """

    MAX_ROWS = 20

    def __init__(self):
        super().__init__()
        self.param = MultiMonteCarloParam()
        self.ctrls = None

    def build(self):
        # 行の削除・追加ボタン
        self.btn_plus = ft.IconButton(
            icon=ft.icons.ADD_CIRCLE, tooltip="Increase Row", on_click=self.click_add
        )
        self.btn_minus = ft.IconButton(
            icon=ft.icons.REMOVE_CIRCLE,
            tooltip="Decrease Row",
            on_click=self.click_remove,
        )
        self.btn_pm = ft.Row([self.btn_plus, self.btn_minus])

        # 入力コントロールの作成
        self._build_ctrls()
        self.container = ft.Row(
            [ft.Column([self.btn_pm] + self.ctrls)], scroll=ft.ScrollMode.AUTO
        )

        # Error用ダイアログ
        self.err_dlg = ft.AlertDialog(title=ft.Text("Error!"))

        return self.container

    def click_add(self, e):
        if len(self.param.labels) < CorrelationTableView.MAX_ROWS:
            self.param.add_items()
            self.update_view()
        else:
            self.open_err_dlg("これ以上アセット数は増やせません")

    def click_remove(self, e):
        if len(self.param.labels) > 1:
            self.param.remove_items()
            self.update_view()
        else:
            self.open_err_dlg("これ以上アセット数は減らせません")

    def open_err_dlg(self, msg: str):
        """指定されたメッセージでError Dialogを開く関数

        Args:
            msg (str): エラー内容のメッセージ
        """
        self.err_dlg.content = ft.Text(msg)
        self.page.dialog = self.err_dlg
        self.err_dlg.open = True
        self.page.update()

    def _build_ctrls(self):
        """Paramをもとにしてコントロールを作成する関数"""
        self.ctrls = []
        item_len = len(self.param.labels)
        for y in range(item_len):
            row = []
            for x in range(item_len + 4):
                if x == 0:
                    label = "アセット名"
                    w = 100
                    oc = None
                    v = self.param.labels[y]
                    dis = False
                elif x == 1:
                    label = "リターン"
                    w = 80
                    oc = validate.textfield_float_changed
                    v = str(self.param.profits[y])
                    dis = False
                elif x == 2:
                    label = "標準偏差"
                    w = 80
                    oc = validate.textfield_float_changed
                    v = str(self.param.stds[y])
                    dis = False
                elif x == 3:
                    label = "構成比"
                    w = 80
                    oc = validate.textfield_float_changed
                    v = str(self.param.ratios[y])
                    dis = False
                else:
                    i, j = y, x - 4
                    label = f"相関({y+1},{x-3})"
                    w = 80
                    oc = validate.textfield_float_changed
                    if i == j:
                        dis = True
                        v = str(self.param.cor[i, j])
                    elif i < j:
                        dis = True
                        v = ""
                    else:
                        dis = False
                        v = str(self.param.cor[i, j])
                c = ft.TextField(
                    label=label, width=w, on_change=oc, value=v, disabled=dis
                )
                row.append(c)
            self.ctrls.append(ft.Row(row))

    def _update_param_from_ctrls(self):
        """コントロールの値をParamへ反映させる関数"""
        labels = []
        profits = []
        stds = []
        ratios = []
        cor = []

        item_len = len(self.ctrls)

        for y in range(item_len):
            c = []
            for x in range(item_len + 4):
                tf = self.ctrls[y].controls[x]
                if x == 0:
                    labels.append(tf.value)
                elif x == 1:
                    profits.append(float(tf.value))
                elif x == 2:
                    stds.append(float(tf.value))
                elif x == 3:
                    ratios.append(float(tf.value))
                else:
                    try:
                        c.append(float(tf.value))
                    except ValueError:
                        c.append(0.0)
            cor.append(c)

        self.param.labels = labels
        self.param.profits = np.array(profits)
        self.param.ratios = np.array(ratios)
        self.param.stds = np.array(stds)
        self.param.cor = np.array(cor)

    def update_view(self):
        """現在のParamをもとに、コントロールへ値を反映させる関数"""
        dim = len(self.ctrls)
        item_len = len(self.param.labels)
        if dim != item_len:
            self._build_ctrls()
            self.container.controls = [
                ft.Row(
                    [ft.Column([self.btn_pm] + self.ctrls)], scroll=ft.ScrollMode.AUTO
                )
            ]
        else:
            for y in range(item_len):
                for x in range(item_len + 4):
                    tf = self.ctrls[y].controls[x]
                    if x == 0:
                        tf.value = self.param.labels[y]
                    elif x == 1:
                        tf.value = str(self.param.profits[y])
                    elif x == 2:
                        tf.value = str(self.param.stds[y])
                    elif x == 3:
                        tf.value = str(self.param.ratios[y])
                    else:
                        i, j = y, x - 4
                        if i < j:
                            tf.value = str(self.param.cor[i, j])
        self.update()

    def set_param(self, param: MultiMonteCarloParam):
        """Paramを与えてセットする関数。ViewのUpdateは行わない。

        Args:
            param (MultiMonteCarloParam): _description_
        """
        self.param = copy.deepcopy(param)

    def get_param(self) -> MultiMonteCarloParam:
        """現在のParamを返す関数。相関行列は対称行列にしている

        Returns:
            MultiMonteCarloParam: _description_
        """
        self._update_param_from_ctrls()
        param = copy.deepcopy(self.param)
        param.calc_cor_from_tril()
        param.calc_cov_from_cor()
        return param

    def print(self):
        self._update_param_from_ctrls()
        print(self.labels)
        print(self.profits)
        print(self.ratios)
        print(self.stds)
        print(self.cor)
