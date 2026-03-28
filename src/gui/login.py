import flet as ft
from src.core.auth import UserManager


class LoginSystem(ft.Container):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.user_manager = UserManager()
        self.expand = True
        self.alignment = ft.Alignment.CENTER

        # UI Elements
        self.username_field = ft.TextField(
            label="Usuario",
            icon=ft.Icons.PERSON,
            border_radius=10,
            on_submit=self.handle_login
        )

        self.password_field = ft.TextField(
            label="Contraseña",
            icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=10,
            on_submit=self.handle_login
        )

        self.login_button = ft.ElevatedButton(
            content=ft.Text("Entrar", size=16, weight=ft.FontWeight.BOLD),
            width=200,
            height=50,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self.handle_login
        )

        self.error_text = ft.Text(color=ft.Colors.RED, visible=False)

        # Main Card Content
        self.content = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.LOCK, size=50, color=ft.Colors.PRIMARY),
                        ft.Text("AYL POS", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Acceso al Sistema", size=14, color=ft.Colors.SECONDARY),
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        self.username_field,
                        self.password_field,
                        self.error_text,
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        self.login_button,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=40,
                width=350,
            ),
            elevation=10,
        )

    async def handle_login(self, e):
        # Visual feedback
        self.login_button.disabled = True
        self.login_button.content = ft.ProgressRing(width=20, height=20, color=ft.Colors.WHITE)
        self.error_text.visible = False
        self.update()

        # Auth logic
        username = self.username_field.value
        password = self.password_field.value

        role = self.user_manager.authenticate(username, password)

        if role:
            await self.on_login_success(username, role)
        else:
            self.error_text.value = "Credenciales incorrectas"
            self.error_text.visible = True
            self.login_button.disabled = False
            self.login_button.content = ft.Text("Entrar", size=16, weight=ft.FontWeight.BOLD)
            self.update()

            snack = ft.SnackBar(
                content=ft.Text("Fallo en el inicio de sesión"),
                bgcolor=ft.Colors.RED
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()