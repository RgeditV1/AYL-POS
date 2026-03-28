# Xun-POS - Sistema de Punto de Venta

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
uv run python3 -m src.main
```

### Credenciales por Defecto

- **Usuario:** `admin`
- **Contraseña:** `admin`

**Nota:** Cambie la contraseña después del primer inicio de sesión.

## Requisitos

- **Sistema Operativo:** Linux (Ubuntu, Debian, Fedora, Arch, etc.)
- **Python:** 3.11 o superior (gestionado preferiblemente por `uv`)
- **Herramienta:** [uv](https://github.com/astral-sh/uv) instalada

Para otras dependencias, consulte la sección de **Instalación de Dependencias**.

**Importante:** Esta aplicación NO es compatible con Windows.

## Características

### Módulos Principales

1. **Punto de Venta (POS)** - Interfaz principal de ventas
2. **Gestión de Productos** - Añadir, editar y eliminar productos
3. **Reportes** - Reportes de ventas y flujo de caja
4. **Configuración** - Detalles del negocio y ajustes

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
data
├── flujo_caja.csv
├── .credentials # importante no perderlo
├── productos.csv
└── ventas.csv
src
├── core
│   ├── auth.py
│   ├── config.py
│   ├── inventory.py
│   ├── sales.py
│   ├── settings.py
│   └── thermal_printer.py
├── gui
│   ├── about_view.py
│   ├── inventory_view.py
│   ├── login.py
│   ├── pos_view.py
│   ├── reports_view.py
│   ├── settings_view.py
│   └── theme.py
├── main.py
└── Pos.png
```

## Gestión de Usuarios (Solo Administrador)

### Añadir Usuario
1. Inicie sesión como administrador
2. Seleccione la opción 5: "Añadir Nuevo Usuario"
3. Ingrese nombre de usuario y contraseña
4. Seleccione el rol (administrador o cajero)

### Cambiar Contraseña
1. Inicie sesión como administrador
2. Seleccione la opción 7: "Cambiar Contraseña"
3. Seleccione el usuario
4. Ingrese la nueva contraseña

### Eliminar Usuario
1. Inicie sesión como administrador
2. Seleccione la opción 6: "Eliminar Usuario"
3. Seleccione el usuario a eliminar
4. Confirme la eliminación

## Uso Diario

### Para Cajeros
1. Inicie sesión con credenciales de cajero
2. Acceda al POS para realizar ventas
3. Gestione el inventario de productos según sea necesario

### Para Administradores
1. Revise los reportes de ventas diariamente
2. Actualice el inventario y los precios
3. Gestione usuarios y la configuración del sistema
4. Supervise el flujo de caja

## Seguridad

- Contraseñas cifradas (PBKDF2 con SHA256)
- Control de acceso basado en roles
- Protección contra la auto-eliminación del usuario activo
- Protección del último usuario administrador

## Archivos de Datos

### productos.csv
Formato: `codigo_barras,nombre,precio,inventario`

### ventas.csv
Formato: `marca_tiempo,codigo_barras,nombre,cantidad,precio_unitario,precio_total`

### flujo_caja.csv
Formato: `marca_tiempo,tipo,monto,concepto`

## Notas

- Los archivos CSV utilizan formato UTF-8
- Las fechas están en formato AAAA-MM-DD (principalmente) o específico de la región
- La interfaz está completamente en español
- Los movimientos de flujo de caja se registran automáticamente con cada venta

## Actualización del Sistema

Para conservar los datos al actualizar:
1. Realice una copia de seguridad de los archivos .csv, .credentials y settings.json
2. Actualice los archivos .py
3. Restaure los datos guardados

## Soporte

Para problemas o preguntas, consulte el código fuente o contacte al administrador del sistema.

## Licencia

Este proyecto está bajo la Licencia MIT. Para más detalles, vea el archivo [LICENSE](LICENSE).

---

**Versión:** 2.0.0  
**Última Actualización:** Marzo 2026
