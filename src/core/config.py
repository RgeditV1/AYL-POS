import os
import platform

# Project root is two levels up from src/core/config.py
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CORE_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)

# Data directory in root (override on Windows)
if platform.system() == "Windows":
    localappdata = os.getenv("LOCALAPPDATA")
    if localappdata:
        DATA_DIR = os.path.join(localappdata, "AYL-POS", "data")
        BACKUP_DIR = os.path.join(localappdata, "AYL-POS", "backups")
    else:
        DATA_DIR = os.path.join(PROJECT_ROOT, "data")
        BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")
else:
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR, exist_ok=True)

# File Paths
PRODUCTS_CSV = os.path.join(DATA_DIR, "productos.csv")
SALES_CSV = os.path.join(DATA_DIR, "ventas.csv")
CASH_FLOW_CSV = os.path.join(DATA_DIR, "flujo_caja.csv")
TICKETS_CSV = os.path.join(DATA_DIR, "tickets.csv")
SETTINGS_JSON = os.path.join(DATA_DIR, "settings.json")
CREDENTIALS_FILE = os.path.join(DATA_DIR, ".credentials")
DB_PATH = os.path.join(DATA_DIR, "ayl_pos.db")
