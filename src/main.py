import sys
import os
import asyncio

# Add project root to sys.path to allow imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import flet as ft
from src.gui.login import LoginSystem
from src.gui.pos_view import POSView
from src.gui.reports_view import ReportsView
from src.gui.inventory_view import InventoryView
from src.gui.settings_view import SettingsView
from src.gui.theme import ThemeManager


class AYL_Application:
    def __init__(self, page: ft.Page):
        icon_path = os.path.join(project_root, "Pos.png")
        self.page = page
        self.page.window.icon = icon_path
        self.page.title = "Punto de Venta A&L"
        self.page.theme = ThemeManager.get_dark_theme()
        self.page.theme_mode = ft.ThemeMode.DARK

    async def initialize(self):
        """Async startup."""
        self._show_login()
        self.page.update()

    # ──────────────────────────────────────────────
    # View Switching
    # ──────────────────────────────────────────────

    def _configure_login_window(self):
        """Set window size for the login screen."""
        self.page.window.width = 440
        self.page.window.height = 620
        self.page.window.resizable = False
        self.page.window.full_screen = False
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.update()

    def _configure_pos_window(self):
        """Set window to fullscreen for the POS."""
        self.page.window.full_screen = True
        self.page.window.resizable = True
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.START
        self.page.update()

    def _show_login(self):
        self._configure_login_window()
        self.page.controls.clear()
        login_view = LoginSystem(on_login_success=self.handle_login_success)
        self.page.add(login_view)
        self.page.update()

    async def handle_login_success(self, username: str, role: str):
        """Transition from login → POS."""
        self._username = username
        self._role = role
        self._configure_pos_window()
        self._load_pos_view(username, role)

    def _load_pos_view(self, username: str, role: str):
        self.page.controls.clear()
        pos = POSView(
            username=username,
            role=role,
            on_logout=self._handle_logout,
            on_open_reports=self._show_reports if role == "admin" else None,
            on_open_inventory=self._show_inventory if role == "admin" else None,
            on_open_settings=self._show_settings if role == "admin" else None,
        )
        self.page.add(pos)
        self.page.update()

    def _show_reports(self, username: str, role: str):
        """Switch from POS → Reports view."""
        self.page.controls.clear()
        reports = ReportsView(
            username=username,
            role=role,
            on_back=lambda: self._load_pos_view(username, role),
        )
        self.page.add(reports)
        self.page.update()

    def _show_inventory(self, username: str, role: str):
        """Switch from POS → Inventory view."""
        self.page.controls.clear()
        inventory = InventoryView(
            username=username,
            role=role,
            on_back=lambda: self._load_pos_view(username, role),
        )
        self.page.add(inventory)
        self.page.update()

    def _show_settings(self, username: str, role: str):
        """Switch from POS → Settings view."""
        self.page.controls.clear()
        settings = SettingsView(
            username=username,
            role=role,
            on_back=lambda: self._load_pos_view(username, role),
        )
        self.page.add(settings)
        self.page.update()

    def _return_to_pos(self, username: str, role: str):
        """Generic return to POS."""
        self._load_pos_view(username, role)

    def _handle_logout(self):
        """Return to login screen."""
        self._show_login()


async def main(page: ft.Page):
    """Flet entry point."""
    app = AYL_Application(page)
    await app.initialize()


if __name__ == "__main__":
    ft.app(main)
