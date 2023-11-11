from enum import Enum
import flet as ft
from multi_assets_sim import (
    MonteCarloInputView,
    MonteCarloParam,
    MonteCarloSim,
    MultiMonteCarloInputView,
    MultiMonteCarloParam,
    MultiMonteCarloSim,
    MonteCarloResultView,
)


class TabIdx(Enum):
    SingleAsset = 0
    MultiAsset = 1
    Result = 2


class SimApp(ft.UserControl):
    def __init__(self, is_web: bool):
        super().__init__()
        self.is_web = is_web

    def build(self):
        self.single_sim = MonteCarloSim()
        self.multi_sim = MultiMonteCarloSim()
        self.ctl_res = MonteCarloResultView(self.is_web)
        self.ctl_in_single = MonteCarloInputView(self.is_web, self.simulate_single)
        self.ctl_in_multi = MultiMonteCarloInputView(self.is_web, self.simulate_multi)

        self.tabs = ft.Tabs(
            selected_index=TabIdx.SingleAsset.value,
            animation_duration=300,
            # expand=True,
            tabs=[
                ft.Tab(
                    text="Single Asset Params",
                ),
                ft.Tab(
                    text="Multi Asset Params",
                ),
                ft.Tab(
                    text="Simulation Result",
                ),
            ],
            on_change=self.onchange_tabs,
        )

        self.cols = [
            ft.Column([self.ctl_in_single]),
            ft.Column([self.ctl_in_multi], visible=False),
            ft.Column([self.ctl_res], visible=False),
        ]

        self.err_dlg = ft.AlertDialog(
            title=ft.Text("Error!"), content=ft.Text("シミュレーションが実行されていません")
        )

        return ft.Column(
            controls=[
                ft.Row([self.tabs]),
                self.cols[0],
                self.cols[1],
                self.cols[2],
            ],
            expand=True,
        )

    def simulate_single(self, param: MonteCarloParam):
        self.single_sim.set_param(param)
        self.single_sim.simulate()
        df_desc = self.single_sim.get_percentile_describe()
        df_each = self.single_sim.get_percentile_eachtime()
        df_hist = self.single_sim.get_percentile_history()
        self.ctl_res.set_sim_result(df_desc, df_each, df_hist)
        self.toggle_tab(TabIdx.Result.value)

    def simulate_multi(self, param: MultiMonteCarloParam):
        self.multi_sim.set_param(param)
        self.multi_sim.simulate()
        df_desc = self.multi_sim.get_percentile_describe()
        df_each = self.multi_sim.get_percentile_eachtime()
        df_hist = self.multi_sim.get_percentile_history()
        self.ctl_res.set_sim_result(df_desc, df_each, df_hist)
        self.toggle_tab(TabIdx.Result.value)

    def onchange_tabs(self, e):
        idx = self.tabs.selected_index
        if idx == TabIdx.Result.value and self.ctl_res.has_result() is False:
            self.page.dialog = self.err_dlg
            self.err_dlg.open = True
            self.toggle_tab(TabIdx.SingleAsset.value)
            self.page.update()
        else:
            self.toggle_tab(idx)

    def toggle_tab(self, idx: int):
        self.tabs.selected_index = idx
        for i, c in enumerate(self.cols):
            if i == idx:
                c.visible = True
            else:
                c.visible = False
        self.update()
