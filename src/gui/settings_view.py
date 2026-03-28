import os
import zipfile
import flet as ft
from src.core.settings import SettingsManager
from src.core.auth import UserManager
from src.core.config import DATA_DIR, PRODUCTS_CSV, SALES_CSV, CASH_FLOW_CSV, SETTINGS_JSON


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

        self.settings_manager = SettingsManager()
        self.user_manager = UserManager()

        self._active_tab = 0  # 0=Tienda, 1=Usuarios, 2=Datos

        self._init_controls()
        self._build_ui()
        self._load_settings()

    # ──────────────────────────────────────────────
    # Controls init
    # ──────────────────────────────────────────────

    def _init_controls(self):
        # Store settings fields
        self.f_business = ft.TextField(label="Nombre del Negocio", border_radius=8, expand=True)
        self.f_address = ft.TextField(label="Dirección", border_radius=8, expand=True)
        self.f_phone = ft.TextField(
            label="Teléfono",
            border_radius=8,
            expand=True,
            keyboard_type=ft.KeyboardType.PHONE,
        )
        self.f_cashier = ft.TextField(label="Nombre del Cajero", border_radius=8, expand=True)

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

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Información del Negocio", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                    ft.Row([self.f_business], spacing=10),
                    ft.Row([self.f_address], spacing=10),
                    ft.Row([self.f_phone, self.f_cashier], spacing=10),
                    ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                    ft.Row([save_btn]),
                ],
                spacing=14,
            ),
        )

    def _load_settings(self):
        s = self.settings_manager.load_settings()
        self.f_business.value = s.get("business_name", "")
        self.f_address.value = s.get("address", "")
        self.f_phone.value = s.get("phone", "")
        self.f_cashier.value = s.get("cashier_name", "")
        try:
            self.f_business.update()
            self.f_address.update()
            self.f_phone.update()
            self.f_cashier.update()
        except Exception:
            pass

    def _save_settings(self, e=None):
        settings = {
            "business_name": self.f_business.value.strip(),
            "address": self.f_address.value.strip(),
            "phone": self.f_phone.value.strip(),
            "cashier_name": self.f_cashier.value.strip(),
            "logo_path": "",
        }
        success, message = self.settings_manager.save_settings(settings)
        self._show_snack(message, error=not success)

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
        self._refresh_users()

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
            ("productos.csv", "Catálogo de productos", PRODUCTS_CSV),
            ("ventas.csv", "Historial de ventas", SALES_CSV),
            ("flujo_caja.csv", "Flujo de caja", CASH_FLOW_CSV),
            ("settings.json", "Configuración", SETTINGS_JSON),
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
        files_to_export = [PRODUCTS_CSV, SALES_CSV, CASH_FLOW_CSV, SETTINGS_JSON]
        export_path = os.path.join(DATA_DIR, "backup_ayl_pos.zip")
        try:
            with zipfile.ZipFile(export_path, "w") as zipf:
                for fpath in files_to_export:
                    if os.path.exists(fpath):
                        zipf.write(fpath, arcname=os.path.basename(fpath))
            self._show_snack(f"✓ Backup exportado: {export_path}")
        except Exception as ex:
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
            self._show_snack(f"Error al importar: {ex}", error=True)

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def _show_snack(self, message: str, error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _go_back(self):
        if self.on_back:
            self.on_back()
