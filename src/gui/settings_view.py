import os
import platform
import zipfile
from datetime import datetime
import flet as ft
from src.core.settings import SettingsManager
from src.core.auth import UserManager
from src.core.printer import PrinterDetector, PrinterManager
from src.core.config import (DATA_DIR, BACKUP_DIR, PRODUCTS_CSV,
                            SALES_CSV, CASH_FLOW_CSV, SETTINGS_JSON, DB_PATH)
from src.app_platform.admin import is_admin, permission_hint


class SettingsView(ft.Container):
    """
    Flet reimplementation of settings_gui.py + user management.
    Tabs: Tienda | Usuarios | Datos
    """

    def __init__(self, username: str, role: str, on_back=None):
        super().__init__()
        self.expand = True
        self.username = username
        self.role = role
        self.on_back = on_back
        self._pending_snacks = []
        self._pending_load = True

        self.settings_manager = SettingsManager()
        self.user_manager = UserManager()
        self.printer_detector = PrinterDetector()
        self.printer_manager = PrinterManager({})
        self.settings = {}

        self._active_tab = 0  # 0=Tienda, 1=Usuarios, 2=Datos

        self._init_controls()
        self._build_ui()
        # Defer settings load until control is mounted

    # ──────────────────────────────────────────────
    # Controls init
    # ──────────────────────────────────────────────

    def _init_controls(self):
        # Store settings fields
        self.f_business = ft.TextField(label="Nombre del Negocio", border_radius=8, width=450)
        self.f_address = ft.TextField(label="Dirección", border_radius=8, width=450)
        self.f_cashier = ft.TextField(label="Nombre del Cajero", border_radius=8, width=450)
        self.f_phone = ft.TextField(
            label="Teléfono",
            border_radius=8,
            width=450,
            keyboard_type=ft.KeyboardType.PHONE,
        )

        # Users table
        self.users_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=4)

        # New user form
        self.f_new_username = ft.TextField(label="Usuario", border_radius=8, expand=True)
        self.f_new_password = ft.TextField(
            label="Contraseña",
            border_radius=8,
            expand=True,
            password=True,
            can_reveal_password=True,
        )
        self.f_new_role = ft.Dropdown(
            label="Rol",
            options=[
                ft.dropdown.Option(key="admin", text="Administrador"),
                ft.dropdown.Option(key="cajero", text="Cajero"),
            ],
            value="cajero",
            border_radius=8,
            width=180,
        )

        # Tab content (built once, swapped in _switch_tab)
        self._tab_content = ft.Container(expand=True)

        # Printers
        self._printer_map = {}
        self._loaded_printer_key = ""
        self.f_printer = ft.Dropdown(
            label="Impresora",
            options=[],
            border_radius=8,
            expand=True,
        )
        self.refresh_printers_btn = ft.OutlinedButton(
            content=ft.Text("Actualizar", size=12),
            on_click=lambda e: self._refresh_printers(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.print_test_btn = ft.OutlinedButton(
            content=ft.Text("Impresión prueba", size=12),
            on_click=lambda e: self._print_test_ticket(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.require_sudo_checkbox = ft.Checkbox(
            label="Solicitar contraseña sudo al imprimir (Linux)",
            value=False,
            visible=platform.system() == "Linux",
        )
        self.ticket_paper_mm = 58
        self.paper_58_btn = ft.OutlinedButton(
            content=ft.Text("58mm", size=12),
            on_click=lambda e: self._set_ticket_paper(58),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.paper_80_btn = ft.OutlinedButton(
            content=ft.Text("80mm", size=12),
            on_click=lambda e: self._set_ticket_paper(80),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self._update_ticket_paper_buttons()

    # ──────────────────────────────────────────────
    # UI Assembly
    # ──────────────────────────────────────────────

    def _build_ui(self):
        header = self._build_header()

        # Manual tab bar (since ft.Tabs API is incompatible in this version)
        self._tab_labels = ["🏪 Tienda", "👤 Usuarios", "💾 Datos"]
        self._tab_btn_refs = []
        tab_bar_controls = []
        for i, label in enumerate(self._tab_labels):
            btn = ft.ElevatedButton(
                content=ft.Text(label, size=13),
                on_click=lambda e, idx=i: self._switch_tab(idx),
                height=38,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    bgcolor=ft.Colors.PRIMARY if i == 0 else None,
                    color=ft.Colors.WHITE if i == 0 else None,
                ),
            )
            self._tab_btn_refs.append(btn)
            tab_bar_controls.append(btn)

        self._tab_bar = ft.Row(tab_bar_controls, spacing=6)

        # Initial content
        self._tab_content = ft.Container(
            content=self._build_store_tab(),
            expand=True,
        )

        self.content = ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Column(
                        [
                            self._tab_bar,
                            ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                            self._tab_content,
                        ],
                        expand=True,
                        spacing=8,
                    ),
                    expand=True,
                    padding=20,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _switch_tab(self, idx: int):
        self._active_tab = idx
        # Update button styles
        for i, btn in enumerate(self._tab_btn_refs):
            btn.style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=ft.Colors.PRIMARY if i == idx else None,
                color=ft.Colors.WHITE if i == idx else None,
            )

        # Swap tab content
        builders = [self._build_store_tab, self._build_users_tab, self._build_data_tab]
        self._tab_content.content = builders[idx]()

        try:
            self._tab_bar.update()
            self._tab_content.update()
        except Exception:
            pass

        # Refresh users list when switching to that tab
        if idx == 1:
            self._refresh_users()

    def _build_header(self):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda e: self._go_back(),
                                tooltip="Volver al POS",
                            ),
                            ft.Text("Configuración", size=18, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        f"👤 {self.username}  [{self.role}]",
                        size=13,
                        color=ft.Colors.SECONDARY,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=20, top=12, right=20, bottom=12),
            bgcolor="#1E293B",
            border=ft.Border(bottom=ft.BorderSide(1, "#334155")),
        )

    # ──────────────────────────────────────────────
    # Tab: Store Settings
    # ──────────────────────────────────────────────

    def _build_store_tab(self):
        save_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.SAVE, size=16), ft.Text("Guardar", size=14)],
                spacing=6, tight=True,
            ),
            on_click=self._save_settings,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            height=48,
        )

        return ft.Column(
            [
                ft.Column(
                    [
                        ft.Text("Información del Negocio", size=16, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                        ft.Row([self.f_business], spacing=10),
                        ft.Row([self.f_address], spacing=10),
                        ft.Row([self.f_phone], spacing=10),
                        ft.Row([self.f_cashier], spacing=10),
                        ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
                        ft.Text("Impresora", size=16, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                        ft.Row([self.f_printer, self.refresh_printers_btn], width=450, spacing=10),
                        ft.Row([self.print_test_btn], spacing=10),
                        self.require_sudo_checkbox,
                        ft.Divider(height=6, color=ft.Colors.TRANSPARENT),
                        ft.Text("Tamaño de papel", size=14, weight=ft.FontWeight.BOLD),
                        ft.Row([self.paper_58_btn, self.paper_80_btn], spacing=8),
                    ],
                    spacing=14,
                    scroll=ft.ScrollMode.ALWAYS,
                    expand=True,
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([save_btn]),
            ],
            spacing=0,
        )

    def _load_settings(self):
        s = self.settings_manager.load_settings()
        self.settings = s
        self.printer_manager = PrinterManager(self.settings)
        self.f_business.value = s.get("business_name", "")
        self.f_address.value = s.get("address", "")
        self.f_phone.value = s.get("phone", "")
        self.f_cashier.value = s.get("cashier_name", "")
        self._loaded_printer_key = ""
        if platform.system() == "Windows":
            name = s.get("printer_name", "")
            if name:
                self._loaded_printer_key = name
        else:
            vid = s.get("printer_vid", "")
            pid = s.get("printer_pid", "")
            if vid != "" and pid != "":
                self._loaded_printer_key = f"{vid}:{pid}"
        self.require_sudo_checkbox.value = bool(s.get("require_sudo_print", False))
        try:
            self.ticket_paper_mm = int(s.get("ticket_paper_mm", 58))
        except Exception:
            self.ticket_paper_mm = 58
        self._update_ticket_paper_buttons()
        self._refresh_printers()
        try:
            self.f_business.update()
            self.f_address.update()
            self.f_phone.update()
            self.f_cashier.update()
            self.f_printer.update()
            self.require_sudo_checkbox.update()
            self.paper_58_btn.update()
            self.paper_80_btn.update()
        except Exception:
            pass

    def _save_settings(self, e=None):
        selected_key = self.f_printer.value or ""
        printer_name = ""
        printer_vid = ""
        printer_pid = ""
        if selected_key in self._printer_map:
            p = self._printer_map[selected_key]
            printer_name = p.get("name", "")
            printer_vid = p.get("vid", "")
            printer_pid = p.get("pid", "")

        settings = {
            "business_name": self.f_business.value.strip(),
            "address": self.f_address.value.strip(),
            "phone": self.f_phone.value.strip(),
            "cashier_name": self.f_cashier.value.strip(),
            "logo_path": "",
            "printer_name": printer_name,
            "printer_vid": "" if platform.system() == "Windows" else printer_vid,
            "printer_pid": "" if platform.system() == "Windows" else printer_pid,
            "require_sudo_print": bool(self.require_sudo_checkbox.value),
            "ticket_paper_mm": int(self.ticket_paper_mm),
        }
        success, message = self.settings_manager.save_settings(settings)
        if success:
            self.settings = settings
            self.printer_manager = PrinterManager(self.settings)
        self._show_snack(message, error=not success)

    def _refresh_printers(self):
        printers = self.printer_detector.get_available_printers()
        if self.printer_detector.last_error:
            self._show_snack(self.printer_detector.last_error, error=True)
        self._printer_map = {}
        options = []
        for p in printers:
            if platform.system() == "Windows":
                key = p["name"]
            else:
                key = f"{p['vid']}:{p['pid']}"
            self._printer_map[key] = p
            if platform.system() == "Windows":
                label = p["name"]
            else:
                label = f"{p['name']} ({p['vid']}:{p['pid']})"
            options.append(ft.dropdown.Option(key=key, text=label))

        self.f_printer.options = options
        if self._loaded_printer_key in self._printer_map:
            self.f_printer.value = self._loaded_printer_key
        else:
            self.f_printer.value = None
        try:
            self.f_printer.update()
        except Exception:
            pass

    def _set_ticket_paper(self, mm: int):
        self.ticket_paper_mm = mm
        self._update_ticket_paper_buttons()
        try:
            self.paper_58_btn.update()
            self.paper_80_btn.update()
        except Exception:
            pass

    def _update_ticket_paper_buttons(self):
        def style(selected: bool):
            return ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=ft.Colors.PRIMARY if selected else None,
                color=ft.Colors.WHITE if selected else None,
            )

        self.paper_58_btn.style = style(self.ticket_paper_mm == 58)
        self.paper_80_btn.style = style(self.ticket_paper_mm == 80)

    # ──────────────────────────────────────────────
    # Tab: Users
    # ──────────────────────────────────────────────

    def _build_users_tab(self):
        add_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.PERSON_ADD, size=16), ft.Text("Agregar", size=14)],
                spacing=6, tight=True,
            ),
            on_click=self._add_user,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            height=48,
        )

        header_row = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Usuario", size=12, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text("Rol", size=12, weight=ft.FontWeight.BOLD, width=120),
                    ft.Container(width=200),
                ],
                spacing=4,
            ),
            padding=ft.Padding(left=12, top=8, right=12, bottom=8),
            bgcolor="#334155",
            border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=0, bottom_right=0),
        )

        return ft.Column(
            [
                ft.Text("Gestión de Usuarios", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Nuevo usuario", size=14, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.PRIMARY),
                            ft.Row(
                                [self.f_new_username, self.f_new_password, self.f_new_role, add_btn],
                                spacing=10,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.Padding(left=16, top=12, right=16, bottom=12),
                    bgcolor="#1E293B",
                    border_radius=10,
                ),
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                ft.Text("Usuarios registrados", size=14, weight=ft.FontWeight.BOLD),
                header_row,
                ft.Container(
                    content=self.users_column,
                    expand=True,
                    bgcolor="#1E293B",
                    border_radius=ft.BorderRadius(top_left=0, top_right=0, bottom_left=8, bottom_right=8),
                    padding=4,
                ),
            ],
            expand=True,
            spacing=10,
        )

    def did_mount(self):
        if self._pending_load:
            self._pending_load = False
            self._load_settings()
        self._refresh_users()
        if self._pending_snacks:
            for msg, is_error in self._pending_snacks:
                self._show_snack(msg, error=is_error)
            self._pending_snacks.clear()

    def _refresh_users(self):
        users = self.user_manager.load_users()
        self.users_column.controls.clear()

        if not users:
            self.users_column.controls.append(
                ft.Container(
                    content=ft.Text("Sin usuarios registrados.", color=ft.Colors.SECONDARY,
                                    size=14, text_align=ft.TextAlign.CENTER),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                )
            )
        else:
            for i, (uname, data) in enumerate(users.items()):
                role = data.get("role", "cajero")
                is_you = uname == self.username
                bg = "#1E293B" if i % 2 == 0 else "#172032"

                role_badge = ft.Container(
                    content=ft.Text(
                        "Admin" if role == "admin" else "Cajero",
                        size=12,
                        color=ft.Colors.WHITE,
                    ),
                    bgcolor=ft.Colors.PRIMARY if role == "admin" else "#475569",
                    border_radius=20,
                    padding=ft.Padding(left=10, top=4, right=10, bottom=4),
                    width=80,
                    alignment=ft.Alignment.CENTER,
                )

                name_display = ft.Row(
                    [
                        ft.Text(uname, size=14, expand=True),
                        ft.Text("(tú)", size=11, color=ft.Colors.SECONDARY, italic=True)
                        if is_you else ft.Container(width=0),
                    ]
                )

                self.users_column.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                name_display,
                                role_badge,
                                ft.Row(
                                    [
                                        ft.ElevatedButton(
                                            content=ft.Row(
                                                [ft.Icon(ft.Icons.LOCK_RESET, size=14),
                                                 ft.Text("Contraseña", size=12)],
                                                spacing=4, tight=True,
                                            ),
                                            on_click=lambda e, u=uname: self._change_password_dialog(u),
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=6),
                                            ),
                                            height=34,
                                        ),
                                        ft.ElevatedButton(
                                            content=ft.Row(
                                                [ft.Icon(ft.Icons.DELETE_OUTLINE, size=14),
                                                 ft.Text("Eliminar", size=12)],
                                                spacing=4, tight=True,
                                            ),
                                            on_click=lambda e, u=uname: self._confirm_delete_user(u),
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=6),
                                                bgcolor=ft.Colors.RED if not is_you else "#475569",
                                                color=ft.Colors.WHITE,
                                            ),
                                            disabled=is_you,
                                            height=34,
                                        ),
                                    ],
                                    spacing=6,
                                    width=200,
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                        bgcolor=bg,
                        border_radius=4,
                    )
                )

        try:
            self.users_column.update()
        except Exception:
            pass

    def _add_user(self, e=None):
        uname = self.f_new_username.value.strip()
        pwd = self.f_new_password.value.strip()
        role = self.f_new_role.value or "cajero"

        if not uname or not pwd:
            self._show_snack("Usuario y contraseña son requeridos.", error=True)
            return

        success, message = self.user_manager.create_user(uname, pwd, role)
        self._show_snack(message, error=not success)

        if success:
            self.f_new_username.value = ""
            self.f_new_password.value = ""
            self.f_new_role.value = "cajero"
            try:
                self.f_new_username.update()
                self.f_new_password.update()
                self.f_new_role.update()
            except Exception:
                pass
            self._refresh_users()

    def _change_password_dialog(self, uname: str):
        pwd_field = ft.TextField(
            label=f"Nueva contraseña para '{uname}'",
            password=True,
            can_reveal_password=True,
            border_radius=8,
            autofocus=True,
        )
        pwd_confirm = ft.TextField(
            label="Confirmar contraseña",
            password=True,
            can_reveal_password=True,
            border_radius=8,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Cambiar contraseña — {uname}", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [pwd_field, pwd_confirm],
                tight=True,
                spacing=12,
                width=300,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Cambiar"),
                    on_click=lambda e: self._do_change_password(dialog, uname, pwd_field, pwd_confirm),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.PRIMARY,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _do_change_password(self, dialog, uname, pwd_field, pwd_confirm):
        pwd = pwd_field.value.strip()
        confirm = pwd_confirm.value.strip()

        if not pwd:
            self._show_snack("La contraseña no puede estar vacía.", error=True)
            return
        if pwd != confirm:
            self._show_snack("Las contraseñas no coinciden.", error=True)
            return

        success, message = self.user_manager.change_password(uname, pwd)
        self._close_dialog(dialog)
        self._show_snack(message, error=not success)

    def _confirm_delete_user(self, uname: str):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar eliminación", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                f"¿Eliminar al usuario '{uname}'?\nEsta acción no se puede deshacer.", size=14
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Eliminar"),
                    on_click=lambda e: self._delete_user(dialog, uname),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _delete_user(self, dialog, uname: str):
        success, message = self.user_manager.delete_user(uname)
        self._close_dialog(dialog)
        self._show_snack(message, error=not success)
        if success:
            self._refresh_users()

    # ──────────────────────────────────────────────
    # Tab: Data (Export / Import)
    # ──────────────────────────────────────────────

    def _build_data_tab(self):
        files_info = [
            ("ayl_pos.db", "Base de datos relacional (Usuarios, Inventario, Ventas)", DB_PATH),
            ("settings.json", "Configuración de la tienda", SETTINGS_JSON),
        ]

        file_rows = []
        for fname, desc, fpath in files_info:
            exists = os.path.exists(fpath)
            size = (
                f"{os.path.getsize(fpath) / 1024:.1f} KB" if exists else "No existe"
            )
            file_rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.INSERT_DRIVE_FILE_OUTLINED if exists else ft.Icons.WARNING_AMBER,
                                size=18,
                                color=ft.Colors.SECONDARY if exists else ft.Colors.ORANGE,
                            ),
                            ft.Column(
                                [
                                    ft.Text(fname, size=13, weight=ft.FontWeight.W_500),
                                    ft.Text(desc, size=11, color=ft.Colors.SECONDARY),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Text(size, size=12, color=ft.Colors.SECONDARY, width=80,
                                    text_align=ft.TextAlign.RIGHT),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=14, top=10, right=14, bottom=10),
                    bgcolor="#1E293B",
                    border_radius=8,
                )
            )

        export_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.DOWNLOAD, size=16), ft.Text("Exportar ZIP", size=14)],
                spacing=6, tight=True,
            ),
            on_click=self._export_data,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            height=48,
        )

        import_btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.UPLOAD_FILE, size=16), ft.Text("Importar ZIP", size=14)],
                spacing=6, tight=True,
            ),
            on_click=self._import_data,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=48,
        )

        return ft.Column(
            [
                ft.Text("Archivos de datos", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"Directorio: {DATA_DIR}", size=12, color=ft.Colors.SECONDARY),
                ft.Divider(height=6, color=ft.Colors.TRANSPARENT),
                *file_rows,
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                ft.Text("Backup y restauración", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Exporta todos los datos como un archivo ZIP.\n"
                    "Importar reemplazará los datos actuales.",
                    size=13,
                    color=ft.Colors.SECONDARY,
                ),
                ft.Row([export_btn, import_btn], spacing=12),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

    def _export_data(self, e=None):
        files_to_export = [DB_PATH, SETTINGS_JSON]
        export_path = os.path.join(BACKUP_DIR, "backup_data_pos.zip")
        try:
            with zipfile.ZipFile(export_path, "w") as zipf:
                for fpath in files_to_export:
                    if os.path.exists(fpath):
                        zipf.write(fpath, arcname=os.path.basename(fpath))
            self._show_snack(f"✓ Backup exportado: {export_path}")
        except Exception as ex:
            if isinstance(ex, PermissionError) or "permission denied" in str(ex).lower():
                if not is_admin():
                    self._show_snack(permission_hint(), error=True)
                    return
            self._show_snack(f"Error al exportar: {ex}", error=True)

    def _import_data(self, e=None):
        path_field = ft.TextField(
            label="Ruta al archivo .zip",
            hint_text="/home/usuario/backup.zip",
            expand=True,
            border_radius=8,
            autofocus=True,
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Importar datos", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    ft.Text(
                        "⚠️ Esta acción reemplazará todos los datos actuales.",
                        size=13,
                        color=ft.Colors.ORANGE,
                    ),
                    path_field,
                ],
                tight=True,
                spacing=12,
                width=380,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Importar"),
                    on_click=lambda e: self._do_import(dialog, path_field.value),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.ORANGE,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _do_import(self, dialog, zip_path: str):
        zip_path = zip_path.strip()
        if not zip_path or not os.path.exists(zip_path):
            self._show_snack("Ruta inválida o archivo no encontrado.", error=True)
            return
        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(DATA_DIR)
            self._close_dialog(dialog)
            self._load_settings()
            self._show_snack("✓ Datos importados exitosamente.")
        except Exception as ex:
            if isinstance(ex, PermissionError) or "permission denied" in str(ex).lower():
                if not is_admin():
                    self._show_snack(permission_hint(), error=True)
                    return
            self._show_snack(f"Error al importar: {ex}", error=True)

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def _show_snack(self, message: str, error: bool = False):
        if not getattr(self, "page", None):
            self._pending_snacks.append((message, error))
            return
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _get_runtime_printer_settings(self):
        settings = dict(self.settings or {})
        settings["require_sudo_print"] = bool(self.require_sudo_checkbox.value)
        selected_key = self.f_printer.value or ""
        printer_name = ""
        printer_vid = ""
        printer_pid = ""
        if selected_key in self._printer_map:
            p = self._printer_map[selected_key]
            printer_name = p.get("name", "")
            printer_vid = p.get("vid", "")
            printer_pid = p.get("pid", "")
        settings["printer_name"] = printer_name
        settings["printer_vid"] = "" if platform.system() == "Windows" else printer_vid
        settings["printer_pid"] = "" if platform.system() == "Windows" else printer_pid
        return settings

    def _try_print_text(self, text):
        runtime_settings = self._get_runtime_printer_settings()
        runtime_printer = PrinterManager(runtime_settings)
        if not runtime_printer.has_valid_printer():
            self._show_snack("No hay impresora válida configurada.", error=True)
            return
        if platform.system() == "Linux" and runtime_settings.get("require_sudo_print"):
            self._prompt_sudo_and_print(text, runtime_printer)
            return
        self._show_snack("Enviando a impresora...")
        self.page.run_thread(self._print_worker, text, runtime_printer, None)

    def _print_worker(self, text, printer_manager, sudo_password=None):
        ok, msg = printer_manager.print_text(text, sudo_password=sudo_password)
        self._log_print_result(ok, msg)
        self.page.run_task(self._after_print, ok, msg)

    async def _after_print(self, ok, msg):
        if ok:
            self._show_snack("Prueba enviada a la impresora.")
        else:
            self._show_snack(msg or "No se pudo imprimir la prueba.", error=True)

    def _prompt_sudo_and_print(self, text, printer_manager):
        password_field = ft.TextField(
            label="Contraseña sudo",
            password=True,
            can_reveal_password=True,
            border_radius=8,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Permisos para imprimir", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    ft.Text("Se requiere contraseña sudo para imprimir.", size=12),
                    password_field,
                ],
                tight=True,
                spacing=8,
                width=320,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Imprimir"),
                    on_click=lambda e: self._do_sudo_print(dialog, text, printer_manager, password_field.value),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.PRIMARY,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _do_sudo_print(self, dialog, text, printer_manager, password):
        self._close_dialog(dialog)
        self._show_snack("Enviando a impresora...")
        self.page.run_thread(self._print_worker, text, printer_manager, password)

    def _log_print_result(self, ok, msg):
        ts = datetime.now().isoformat(timespec="seconds")
        status = "OK" if ok else "ERROR"
        print(f"[PRINT {status}] {ts} · {msg}")

    def _print_test_ticket(self):
        test_text = (
            "=== AYL POS ===\n"
            "IMPRESION DE PRUEBA\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "----------------\n\n"
        )
        self._try_print_text(test_text)

    def _go_back(self):
        if self.on_back:
            self.on_back()
