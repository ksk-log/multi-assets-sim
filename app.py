import flet as ft
from multi_assets_sim import SimApp


def main(page: ft.Page):
    page.title = f"Monte Carlo Simulation of Assets (v0.1.6)"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    # page.scroll = ft.ScrollMode.ADAPTIVE

    page.add(SimApp(page.web))


ft.app(target=main)
# ft.app(target=main, view=ft.AppView.WEB_BROWSER)
