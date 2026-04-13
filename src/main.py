import sys
import os
import asyncio
import platform
import shutil
import tempfile
import zipfile
import tarfile
from pathlib import Path

# Add project root to sys.path to allow imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.resources import get_resource_path

def _configure_ssl_certs():
    """Ensure SSL certs resolve correctly on Windows bundled builds."""
    if os.environ.get("SSL_CERT_FILE"):
        return
    try:
        import certifi
    except Exception:
        return
    cert_path = certifi.where()
    os.environ["SSL_CERT_FILE"] = cert_path
    os.environ.setdefault("REQUESTS_CA_BUNDLE", cert_path)


def _maybe_preload_flet_client():
    """Preload Flet desktop client from bundled archive to avoid internet."""
    try:
        import flet_desktop
        from flet.utils import is_windows, is_macos, is_linux
    except Exception:
        return

    if is_windows():
        artifact = "flet-windows.zip"
    elif is_macos():
        artifact = "flet-macos.tar.gz"
    else:
        return

    candidates = [
        get_resource_path("flet_client", artifact),
        get_resource_path("src", "flet_client", artifact),
    ]
    archive_path = next((p for p in candidates if os.path.exists(p)), None)
    if not archive_path:
        return

    flavor = os.environ.get("FLET_DESKTOP_FLAVOR", "").strip().lower()
    if flavor not in ("full", "light"):
        flavor = "full" if not is_linux() else "light"

    cache_dir = Path.home().joinpath(
        ".flet", "client", f"flet-desktop-{flavor}-{flet_desktop.version.version}"
    )
    if cache_dir.exists():
        return

    temp_extract = cache_dir.parent / f"{cache_dir.name}.preload"
    shutil.rmtree(temp_extract, ignore_errors=True)
    temp_extract.mkdir(parents=True, exist_ok=True)

    try:
        if artifact.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(str(temp_extract))
        else:
            with tarfile.open(archive_path, "r:gz") as tar_arch:
                tar_arch.extractall(str(temp_extract))
        temp_extract.rename(cache_dir)
    except Exception:
        shutil.rmtree(temp_extract, ignore_errors=True)


_configure_ssl_certs()
_maybe_preload_flet_client()

import flet as ft
from src.gui.login import LoginSystem, LOBBY_WIDTH, LOBBY_HEIGHT
from src.gui.pos_view import POSView
from src.gui.about_view import AboutView
from src.gui.reports_view import ReportsView
from src.gui.inventory_view import InventoryView
from src.gui.settings_view import SettingsView
from src.gui.theme import ThemeManager


class AYL_Application:
    def __init__(self, page: ft.Page):
        icon_name = "logo.ico" if platform.system() == "Windows" else "logo.png"
        icon_path = get_resource_path("src", icon_name)
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
        self.page.window.width = LOBBY_WIDTH
        self.page.window.height = LOBBY_HEIGHT
        self.page.window.resizable = True
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
        login_view = LoginSystem(
            on_login_success=self.handle_login_success,
            on_open_about=self._show_about_from_login,
        )
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
            on_open_about=self._show_about,
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

    def _show_about(self, username: str, role: str):
        """Switch from POS → About view."""
        self.page.controls.clear()
        about = AboutView(
            username=username,
            role=role,
            on_back=lambda: self._load_pos_view(username, role),
        )
        self.page.add(about)
        self.page.update()

    def _show_about_from_login(self):
        """Show About from login screen."""
        self.page.controls.clear()
        about = AboutView(
            username="Invitado",
            role="visitante",
            on_back=self._show_login,
        )
        self.page.add(about)
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
    ft.run(main)
