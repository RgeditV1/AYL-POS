import os
import platform
import shutil
from src.utils.resources import get_resource_path

# Root del proyecto o bundle
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CORE_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)

# Direcciones de usuario persistentes
if platform.system() == "Windows":
    base_dir = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "AYL-POS")
else:
    # Linux / Mac - Sigue el estándar XDG ~/.local/share
    base_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "AYL-POS")

DATA_DIR = os.path.join(base_dir, "data")
BACKUP_DIR = os.path.join(base_dir, "backups")

# Asegurar que existan
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Lógica de inicialización (Copiar archivos iniciales si no existen)
# El bundle incluye data/ayl_pos.db y data/settings.json como plantillas
bundled_data = get_resource_path("data")
if os.path.exists(bundled_data):
    for item in os.listdir(bundled_data):
        s = os.path.join(bundled_data, item)
        d = os.path.join(DATA_DIR, item)
        if os.path.isfile(s) and not os.path.exists(d):
            try:
                shutil.copy2(s, d)
                print(f"[INIT] Copiado {item} a directorio de usuario.")
            except Exception as e:
                print(f"[ERROR] No se pudo copiar plantilla {item}: {e}")

# File Paths
PRODUCTS_CSV = os.path.join(DATA_DIR, "productos.csv")
SALES_CSV = os.path.join(DATA_DIR, "ventas.csv")
CASH_FLOW_CSV = os.path.join(DATA_DIR, "flujo_caja.csv")
TICKETS_CSV = os.path.join(DATA_DIR, "tickets.csv")
SETTINGS_JSON = os.path.join(DATA_DIR, "settings.json")
CREDENTIALS_FILE = os.path.join(DATA_DIR, ".credentials")
DB_PATH = os.path.join(DATA_DIR, "ayl_pos.db")
