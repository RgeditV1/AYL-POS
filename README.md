# A&L - Sistema de Punto de Venta

Sistema de Punto de Venta rápido y ligero.

## Inicio Rápido

### Instalación de Dependencias

Este proyecto utiliza [uv](https://github.com/astral-sh/uv) para la gestión de dependencias. Para instalar todo lo necesario:

```bash
uv sync
```

### Ejecución

Para iniciar el sistema:

```bash
uv sync && uv run python3 -m src.main
```

### Compilacion

```bash
uv run python3 /scripts/build_binary.py
```

### Credenciales por Defecto

- **Usuario:** `admin`
- **Contraseña:** `admin`

**Nota:** Cambie la contraseña después del primer inicio de sesión.

## Requisitos

- **Python:** 3.11 o superior (gestionado preferiblemente por `uv`)
- **Herramienta:** [uv](https://github.com/astral-sh/uv) instalada

Para otras dependencias, consulte la sección de **Instalación de Dependencias**.

**Importante:** Esta aplicación actualmente esta en desarollo para windows.

## Dependencias (Python)

Estas son las dependencias declaradas en `pyproject.toml`:

- `uv`
- `flet`
- `nuitka`
- `pyusb`
- `patchef`
- `python-escpos`
- `tkcalendar`

## Características

### Módulos Principales

1. **Punto de Venta (POS)** - Interfaz principal de ventas
2. **Gestión de Productos** - Añadir, editar y eliminar productos
3. **Reportes** - Reportes de ventas y flujo de caja
4. **Configuración** - Detalles del negocio y ajustes
4. **Impresion** - Utiliza python-escpos para imprimir directamente desde la interfaz

### Sistema de Usuarios

**Administrador:**
- Acceso total a todos los módulos
- Gestión de usuarios (crear, eliminar, cambiar contraseñas)
- Acceso a reportes y configuración

**Cajero:**
- Acceso solo a POS y Productos
- Sin acceso a reportes, configuración o gestión de usuarios

## Estructura de Archivos

```text
├── data
├── LICENSE
├── pyproject.toml
├── README.md
├── scripts
│   └── build_binary.py
├── src
│   ├── core
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── inventory.py
│   │   ├── printer.py
│   │   ├── sales.py
│   │   ├── settings.py
│   │   └── ticket.py
│   ├── gui
│   │   ├── about_view.py
│   │   ├── inventory_view.py
│   │   ├── login.py
│   │   ├── pos_view.py
│   │   ├── reports_view.py
│   │   ├── settings_view.py
│   │   └── theme.py
│   ├── logo.ico
│   ├── logo.png
│   ├── main.py
│   └── utils
│       └── resources.py
└── uv.lock
```

## Seguridad

- Contraseñas cifradas (PBKDF2 con SHA256)
- Control de acceso basado en roles
- Protección contra la auto-eliminación del usuario activo
- Protección del último usuario administrador

## Soporte

Para problemas o preguntas, consulte el código fuente o contacte al administrador del sistema.

## Licencia

Este proyecto está bajo la Licencia MIT y Licencia Privada. Para más detalles, vea el archivo [LICENSE](LICENSE).

---

**Versión:** 1.0  
**Última Actualización:** abril 2026
