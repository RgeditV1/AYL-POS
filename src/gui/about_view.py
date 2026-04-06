import os
import flet as ft


class AboutView(ft.Container):
    """Simple About / Credits view."""

    def __init__(self, username: str, role: str, on_back=None):
        super().__init__()
        self.expand = True
        self.username = username
        self.role = role
        self.on_back = on_back

        self._build_ui()

    def _build_ui(self):
        header = self._build_header()
        body = self._build_body()

        self.content = ft.Column(
            [
                header,
                ft.Container(
                    content=body,
                    expand=True,
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            expand=True,
            spacing=0,
        )

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
                            ft.Text("Acerca de", size=18, weight=ft.FontWeight.BOLD),
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

    def _build_body(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(project_root, "logo.png")

        return ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Image(src=logo_path, width=96, height=96),
                            ft.Text("AYL POS", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "Sistema de Punto de Venta",
                                size=14,
                                color=ft.Colors.SECONDARY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=20,
                    border_radius=12,
                    bgcolor="#0F172A",
                    border=ft.Border.all(1, "#334155"),
                ),
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
                ft.Text("Creadores", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Soporte Tecnico A&L", size=14, text_align=ft.TextAlign.CENTER),
                ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
                ft.Text("Contacto", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("rgeditv1@protonmail.com", size=14, text_align=ft.TextAlign.CENTER),
                ft.Text("Icono", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Favicon/Surang", size=14, text_align=ft.TextAlign.CENTER),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _go_back(self):
        if self.on_back:
            self.on_back()
