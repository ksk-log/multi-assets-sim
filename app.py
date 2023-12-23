import flet as ft
from multi_assets_sim import SimApp
import toml


def main(page: ft.Page):
    with open("pyproject.toml", encoding="utf-8") as f:
        dict_toml = toml.load(f)
        version = dict_toml["tool"]["poetry"]["version"]

    page.title = f"Monte Carlo Simulation of Assets (v{version})"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    # page.scroll = ft.ScrollMode.ADAPTIVE

    page.add(SimApp(page.web))


ft.app(target=main)
# ft.app(target=main, view=ft.AppView.WEB_BROWSER)
