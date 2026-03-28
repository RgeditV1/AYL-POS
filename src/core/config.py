import os

# Project root is two levels up from src/core/config.py
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CORE_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)

# Data directory in root
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# File Paths
PRODUCTS_CSV = os.path.join(DATA_DIR, "productos.csv")
SALES_CSV = os.path.join(DATA_DIR, "ventas.csv")
CASH_FLOW_CSV = os.path.join(DATA_DIR, "flujo_caja.csv")
SETTINGS_JSON = os.path.join(DATA_DIR, "settings.json")
CREDENTIALS_FILE = os.path.join(DATA_DIR, ".credentials")
