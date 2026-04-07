import platform

if platform.system() == "Windows":
    from src.platform.windows.admin import is_admin  # noqa: F401
else:
    def is_admin():  # noqa: D401
        return True


def permission_hint():
    return "Permiso denegado. Ejecuta el programa como administrador en Windows."
