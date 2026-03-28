#!/usr/bin/env python3

import base64
import getpass
import hashlib
import hmac
import os
import platform
import subprocess
import sys


# ANSI Color codes for terminal
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


# Prevent execution on Windows OS
if platform.system() == "Windows":
    print("=" * 60)
    print("ERROR: Esta aplicación no es compatible con Windows")
    print("=" * 60)
    print("\nEste sistema POS está diseñado exclusivamente para sistemas Unix")
    print("(Linux, macOS, BSD, etc.) y no puede ejecutarse en Windows.")
    print("\nPor favor, utilice un sistema Linux o macOS para ejecutar esta aplicación.")
    print("=" * 60)
    sys.exit(1)


from src.core.auth import UserManager


class LoginSystem:
    """Main login system with menu interface."""

    def __init__(self):
        self.user_manager = UserManager()
        self.current_user = None
        self.current_role = None
        # Track legacy directory for running sub-apps
        self.legacy_dir = os.path.dirname(os.path.abspath(__file__))

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system("clear" if os.name != "nt" else "cls")

    def print_header(self, title):
        """Print a formatted header with colors."""
        print("\n" + Colors.BLUE + "╔" + "=" * 68 + "╗" + Colors.RESET)
        print(
            Colors.BLUE
            + "║"
            + Colors.RESET
            + Colors.BOLD
            + Colors.CYAN
            + f"{title:^68}"
            + Colors.RESET
            + Colors.BLUE
            + "║"
            + Colors.RESET
        )
        print(Colors.BLUE + "╚" + "=" * 68 + "╝" + Colors.RESET)

    def print_box(self, content, color=Colors.WHITE):
        """Print content in a box."""
        lines = content.split("\n")
        max_len = max(len(line) for line in lines)

        print(color + "┌" + "─" * (max_len + 2) + "┐" + Colors.RESET)
        for line in lines:
            print(
                color
                + "│"
                + Colors.RESET
                + f" {line:<{max_len}} "
                + color
                + "│"
                + Colors.RESET
            )
        print(color + "└" + "─" * (max_len + 2) + "┘" + Colors.RESET)

    def print_menu_item(self, number, text, icon=""):
        """Print a formatted menu item."""
        print(
            f"  {Colors.BOLD}{Colors.CYAN}{number}.{Colors.RESET} {icon} {Colors.WHITE}{text}{Colors.RESET}"
        )

    def print_section(self, title):
        """Print a section header."""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}{title}{Colors.RESET}")

    def login(self):
        """Handle user login."""
        self.clear_screen()

        # ASCII Art Logo
        print(f"\n{Colors.CYAN}{Colors.BOLD}")
        print("─" * 80)
        print(f"{Colors.BRIGHT_WHITE}{'Xun-POS':^80}{Colors.RESET}")
        print("─" * 80)
        print(f"{Colors.RESET}")
        print(f"{Colors.WHITE}{'POS gratuito, rápido, ligero y para Linux.'.center(80)}{Colors.RESET}")
        print(f"{Colors.RESET}")

        print(
            f"\n{Colors.BRIGHT_WHITE}╔════════════════════════════════════════════════════════════════════╗{Colors.RESET}"
        )
        print(
            f"{Colors.BRIGHT_WHITE}║{Colors.RESET}  {Colors.BOLD}Por favor ingrese sus credenciales{Colors.RESET}                              {Colors.BRIGHT_WHITE}║{Colors.RESET}"
        )
        print(
            f"{Colors.BRIGHT_WHITE}╚════════════════════════════════════════════════════════════════════╝{Colors.RESET}"
        )

        username = input(f"{Colors.CYAN}Usuario:{Colors.RESET} ").strip()
        password = getpass.getpass(f"{Colors.CYAN}Contraseña:{Colors.RESET} ")

        role = self.user_manager.authenticate(username, password)

        if role:
            self.current_user = username
            self.current_role = role
            role_display = "Administrador" if role == "admin" else "Cajero"
            print(
                f"\n{Colors.BG_GREEN}{Colors.BOLD} ÉXITO {Colors.RESET} {Colors.GREEN}¡Inicio de sesión exitoso!{Colors.RESET}"
            )
            print(
                f"{Colors.BRIGHT_WHITE}Bienvenido, {Colors.BOLD}{Colors.CYAN}{username}{Colors.RESET} {Colors.BRIGHT_BLACK}({role_display}){Colors.RESET}"
            )
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return True
        else:
            print(
                f"\n{Colors.BG_RED}{Colors.BOLD} ERROR {Colors.RESET} {Colors.RED}Usuario o contraseña inválidos.{Colors.RESET}"
            )
            input(
                f"\n{Colors.YELLOW}Presione Enter para intentar de nuevo...{Colors.RESET}"
            )
            return False

    def admin_menu(self):
        """Display and handle admin menu."""
        while True:
            self.clear_screen()

            print(f"\n{Colors.BRIGHT_BLACK}┌{'─' * 68}┐{Colors.RESET}")
            print(
                f"{Colors.BRIGHT_BLACK}│{Colors.RESET} {Colors.BOLD}Sesión Activa:{Colors.RESET} {Colors.CYAN}{self.current_user}{Colors.RESET} {Colors.BRIGHT_BLACK}(Administrador){Colors.RESET}                    {Colors.BRIGHT_BLACK}│{Colors.RESET}"
            )
            print(f"{Colors.BRIGHT_BLACK}└{'─' * 68}┘{Colors.RESET}")

            self.print_section("OPERACIONES POS")
            self.print_menu_item("1", "Punto de Venta", "")
            self.print_menu_item("2", "Productos", "")
            self.print_menu_item("3", "Reportes", "")
            self.print_menu_item("4", "Configuración", "")

            self.print_section("GESTIÓN DE USUARIOS")
            self.print_menu_item("5", "Agregar Nuevo Usuario", "")
            self.print_menu_item("6", "Eliminar Usuario", "")
            self.print_menu_item("7", "Cambiar Contraseña", "")
            self.print_menu_item("8", "Listar Usuarios", "")

            self.print_section("SESIÓN")
            self.print_menu_item("9", "Cerrar Sesión", "")
            self.print_menu_item("0", "Salir", "")

            choice = input(
                f"\n{Colors.BOLD}{Colors.GREEN}>{Colors.RESET} {Colors.WHITE}Ingrese su opción:{Colors.RESET} "
            ).strip()

            if choice == "1":
                self.run_python_app("pos_gui.py")
            elif choice == "2":
                self.run_python_app("products_gui.py")
            elif choice == "3":
                self.run_python_app("reports_gui.py")
            elif choice == "4":
                self.run_python_app("settings_gui.py")
            elif choice == "5":
                self.add_user_menu()
            elif choice == "6":
                self.delete_user_menu()
            elif choice == "7":
                self.change_password_menu()
            elif choice == "8":
                self.list_users_menu()
            elif choice == "9":
                print(f"\n{Colors.GREEN}Sesión cerrada exitosamente.{Colors.RESET}")
                input(
                    f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}"
                )
                return
            elif choice == "0":
                print(f"\n{Colors.CYAN}¡Adiós!{Colors.RESET}")
                sys.exit(0)
            else:
                print(f"\n{Colors.RED}Opción inválida.{Colors.RESET}")
                input(
                    f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}"
                )

    def cashier_menu(self):
        """Display and handle cashier menu."""
        while True:
            self.clear_screen()

            print(f"\n{Colors.BRIGHT_BLACK}┌{'─' * 68}┐{Colors.RESET}")
            print(
                f"{Colors.BRIGHT_BLACK}│{Colors.RESET} {Colors.BOLD}Sesión Activa:{Colors.RESET} {Colors.CYAN}{self.current_user}{Colors.RESET} {Colors.BRIGHT_BLACK}(Cajero){Colors.RESET}                            {Colors.BRIGHT_BLACK}│{Colors.RESET}"
            )
            print(f"{Colors.BRIGHT_BLACK}└{'─' * 68}┘{Colors.RESET}")

            self.print_section("OPERACIONES DISPONIBLES")
            self.print_menu_item("1", "Punto de Venta", "")
            self.print_menu_item("2", "Productos", "")

            self.print_section("SESIÓN")
            self.print_menu_item("3", "Cerrar Sesión", "")
            self.print_menu_item("0", "Salir", "")

            choice = input(
                f"\n{Colors.BOLD}{Colors.GREEN}>{Colors.RESET} {Colors.WHITE}Ingrese su opción:{Colors.RESET} "
            ).strip()

            if choice == "1":
                self.run_python_app("pos_gui.py")
            elif choice == "2":
                self.run_python_app("products_gui.py")
            elif choice == "3":
                print(f"\n{Colors.GREEN}Sesión cerrada exitosamente.{Colors.RESET}")
                input(
                    f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}"
                )
                return
            elif choice == "0":
                print(f"\n{Colors.CYAN}¡Adiós!{Colors.RESET}")
                sys.exit(0)
            else:
                print(f"\n{Colors.RED}Opción inválida.{Colors.RESET}")
                input(
                    f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}"
                )

    def run_python_app(self, script_name):
        """Run a Python GUI application."""
        # Look for the script in the legacy directory
        full_path = os.path.join(self.legacy_dir, script_name)
        
        if not os.path.exists(full_path):
            print(f"\n{Colors.RED}Error: {full_path} no encontrado.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        try:
            print(f"\n{Colors.CYAN}Iniciando {script_name}...{Colors.RESET}")
            # Ensure the project root is in PYTHONPATH so sub-processes can import from src
            env = os.environ.copy()
            project_root = os.path.dirname(os.path.dirname(self.legacy_dir))
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{project_root}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = project_root

            # Wait for process and check for error
            result = subprocess.run([sys.executable, full_path, self.current_role] if script_name == "pos_gui.py" and self.current_role else [sys.executable, full_path], env=env)
            if result.returncode != 0:
                 print(f"\n{Colors.BG_RED}{Colors.BOLD} ERROR {Colors.RESET} {Colors.RED}El programa '{script_name}' terminó inesperadamente (Código {result.returncode}).{Colors.RESET}")
                 input(f"{Colors.YELLOW}Presione Enter para ver los detalles arriba y regresar al menú...{Colors.RESET}")
        except Exception as e:
            print(f"\n{Colors.RED}Error ejecutando {script_name}: {e}{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")

    def add_user_menu(self):
        """Menu for adding a new user."""
        self.clear_screen()
        self.print_header("AGREGAR NUEVO USUARIO")

        print(
            f"\n{Colors.BRIGHT_WHITE}Ingrese detalles del nuevo usuario:{Colors.RESET}\n"
        )

        username = input(f"{Colors.CYAN}Usuario:{Colors.RESET} ").strip()
        if not username:
            print(
                f"\n{Colors.RED}El nombre de usuario no puede estar vacío.{Colors.RESET}"
            )
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        password = getpass.getpass(f"{Colors.CYAN}Contraseña:{Colors.RESET} ")
        if not password:
            print(f"\n{Colors.RED}La contraseña no puede estar vacía.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        password_confirm = getpass.getpass(
            f"{Colors.CYAN}Confirmar Contraseña:{Colors.RESET} "
        )
        if password != password_confirm:
            print(f"\n{Colors.RED}Las contraseñas no coinciden.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        print(f"\n{Colors.BOLD}{Colors.YELLOW}Seleccione Rol:{Colors.RESET}")
        print(
            f"  {Colors.CYAN}1.{Colors.RESET} Administrador {Colors.BRIGHT_BLACK}(Acceso Total){Colors.RESET}"
        )
        print(
            f"  {Colors.CYAN}2.{Colors.RESET} Cajero {Colors.BRIGHT_BLACK}(Acceso Limitado){Colors.RESET}"
        )
        role_choice = input(
            f"\n{Colors.GREEN}>{Colors.RESET} Ingrese opción (1-2): "
        ).strip()

        if role_choice == "1":
            role = "admin"
        elif role_choice == "2":
            role = "cashier"
        else:
            print(f"\n{Colors.RED}Selección de rol inválida.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        success, message = self.user_manager.create_user(username, password, role)
        if success:
            role_display = "Administrador" if role == "admin" else "Cajero"
            print(
                f"\n{Colors.BG_GREEN}{Colors.BOLD} ÉXITO {Colors.RESET} {Colors.GREEN}{message}{Colors.RESET}"
            )
            print(
                f"{Colors.BRIGHT_WHITE}  Usuario: {Colors.CYAN}{username}{Colors.RESET}"
            )
            print(f"{Colors.BRIGHT_WHITE}  Rol: {Colors.CYAN}{role_display}{Colors.RESET}")
        else:
            print(
                f"\n{Colors.BG_RED}{Colors.BOLD} ERROR {Colors.RESET} {Colors.RED}{message}{Colors.RESET}"
            )

        input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")

    def delete_user_menu(self):
        """Menu for deleting a user."""
        self.clear_screen()
        self.print_header("ELIMINAR USUARIO")

        users = self.user_manager.list_users()
        if not users:
            print(f"\n{Colors.RED}No se encontraron usuarios.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        print(f"\n{Colors.BOLD}{Colors.YELLOW}Usuarios Actuales:{Colors.RESET}")
        for username, data in users.items():
            role_display = "Administrador" if data["role"] == "admin" else "Cajero"
            print(
                f"  {Colors.CYAN}{username}{Colors.RESET} {Colors.BRIGHT_BLACK}({role_display}){Colors.RESET}"
            )

        username = input(
            f"\n{Colors.GREEN}>{Colors.RESET} Ingrese usuario a eliminar {Colors.BRIGHT_BLACK}(o Presione Enter para cancelar){Colors.RESET}: "
        ).strip()
        if not username:
            return

        if username == self.current_user:
            print(
                f"\n{Colors.RED}No puede eliminar su propia cuenta mientras está conectado.{Colors.RESET}"
            )
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        confirm = (
            input(
                f"\n{Colors.YELLOW}ADVERTENCIA:{Colors.RESET}  ¿Está seguro de que desea eliminar a '{Colors.CYAN}{username}{Colors.RESET}'? {Colors.BRIGHT_WHITE}(si/no):{Colors.RESET} "
            )
            .strip()
            .lower()
        )
        if confirm != "si" and confirm != "yes":
            print(f"\n{Colors.GREEN}Eliminación cancelada.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        success, message = self.user_manager.delete_user(username)
        if success:
            print(
                f"\n{Colors.BG_GREEN}{Colors.BOLD} ÉXITO {Colors.RESET} {Colors.GREEN}{message}{Colors.RESET}"
            )
        else:
            print(
                f"\n{Colors.BG_RED}{Colors.BOLD} ERROR {Colors.RESET} {Colors.RED}{message}{Colors.RESET}"
            )

        input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")

    def change_password_menu(self):
        """Menu for changing a user's password."""
        self.clear_screen()
        self.print_header("CAMBIAR CONTRASEÑA")

        users = self.user_manager.list_users()
        if not users:
            print(f"\n{Colors.RED}No se encontraron usuarios.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        print(f"\n{Colors.BOLD}{Colors.YELLOW}Usuarios Actuales:{Colors.RESET}")
        for username, data in users.items():
            print(f"  {Colors.CYAN}{username}{Colors.RESET}")

        username = input(
            f"\n{Colors.GREEN}>{Colors.RESET} Ingrese usuario {Colors.BRIGHT_BLACK}(o Presione Enter para cancelar){Colors.RESET}: "
        ).strip()
        if not username:
            return

        if username not in users:
            print(f"\n{Colors.RED}Usuario no encontrado.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        new_password = getpass.getpass(
            f"\n{Colors.CYAN}Ingrese nueva contraseña:{Colors.RESET} "
        )
        if not new_password:
            print(f"\n{Colors.RED}La contraseña no puede estar vacía.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        password_confirm = getpass.getpass(
            f"{Colors.CYAN}Confirme nueva contraseña:{Colors.RESET} "
        )
        if new_password != password_confirm:
            print(f"\n{Colors.RED}Las contraseñas no coinciden.{Colors.RESET}")
            input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")
            return

        success, message = self.user_manager.change_password(username, new_password)
        if success:
            print(
                f"\n{Colors.BG_GREEN}{Colors.BOLD} ÉXITO {Colors.RESET} {Colors.GREEN}{message}{Colors.RESET}"
            )
        else:
            print(
                f"\n{Colors.BG_RED}{Colors.BOLD} ERROR {Colors.RESET} {Colors.RED}{message}{Colors.RESET}"
            )

        input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")

    def list_users_menu(self):
        """Menu for listing all users."""
        self.clear_screen()
        self.print_header("LISTAR USUARIOS")

        users = self.user_manager.list_users()
        if not users:
            print(f"\n{Colors.RED}No se encontraron usuarios.{Colors.RESET}")
        else:
            print(
                f"\n{Colors.BOLD}{Colors.CYAN}{'Usuario':<25} {'Rol':<20}{Colors.RESET}"
            )
            print(f"{Colors.BRIGHT_BLACK}{'-' * 45}{Colors.RESET}")
            for username, data in users.items():
                role_display = "Administrador" if data["role"] == "admin" else "Cajero"
                print(
                    f"{Colors.CYAN}{username:<25}{Colors.RESET} {Colors.WHITE}{role_display:<20}{Colors.RESET}"
                )

        input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.RESET}")

    def run(self):
        """Main application loop."""
        while True:
            if self.login():
                if self.current_role == "admin":
                    self.admin_menu()
                elif self.current_role == "cashier":
                    self.cashier_menu()

                # Reset after logout
                self.current_user = None
                self.current_role = None


if __name__ == "__main__":
    try:
        app = LoginSystem()
        app.run()
    except KeyboardInterrupt:
        print("\n\n¡Adiós!")
        sys.exit(0)
