import csv
import json
import os
import sys
from datetime import datetime

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.config import PRODUCTS_CSV, TICKETS_CSV, CASH_FLOW_CSV, CREDENTIALS_FILE, DB_PATH
from src.core.database import get_db_manager

def migrate():
    print(f"Iniciando migración a SQLite ({DB_PATH})...")
    db = get_db_manager()
    conn = db.get_connection()
    cursor = conn.cursor()

    # 1. Migrate Users
    if os.path.exists(CREDENTIALS_FILE):
        print("Migrando usuarios...")
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(":")
                    if len(parts) >= 3:
                        username, pwd, role = parts[0], parts[1], parts[2]
                        cursor.execute(
                            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                            (username, pwd, role)
                        )
            print("✓ Usuarios migrados.")
        except Exception as e:
            print(f"Error migrando usuarios: {e}")

    # 2. Migrate Products
    if os.path.exists(PRODUCTS_CSV):
        print("Migrando productos...")
        try:
            with open(PRODUCTS_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute(
                        "INSERT OR IGNORE INTO products (codigo, nombre, precio, cantidad, costo) VALUES (?, ?, ?, ?, ?)",
                        (row["codigo"], row["nombre"], float(row["precio"]), int(row["cantidad"]), float(row["costo"]))
                    )
            print("✓ Productos migrados.")
        except Exception as e:
            print(f"Error migrando productos: {e}")

    # 3. Migrate Tickets and Sale Items
    if os.path.exists(TICKETS_CSV):
        print("Migrando tickets y detalles de venta...")
        try:
            with open(TICKETS_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ticket_id = row["ticket_id"]
                    cursor.execute(
                        "INSERT OR IGNORE INTO tickets (ticket_id, fecha_hora, cajero, total, estado) VALUES (?, ?, ?, ?, ?)",
                        (ticket_id, row["fecha_hora"], row["cajero"], float(row["total"]), row["estado"])
                    )
                    
                    # Migrate items from JSON
                    try:
                        items = json.loads(row["items_json"])
                        for code, item in items.items():
                            qty = item.get("qty", 0)
                            price = item.get("precio", 0.0)
                            cursor.execute(
                                "INSERT INTO sale_items (ticket_id, codigo, nombre, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?, ?)",
                                (ticket_id, code, item.get("nombre", "Unknown"), qty, price, qty * price)
                            )
                    except Exception:
                        pass
            print("✓ Tickets migrados.")
        except Exception as e:
            print(f"Error migrando tickets: {e}")

    # 4. Migrate Cash Flow
    if os.path.exists(CASH_FLOW_CSV):
        print("Migrando flujo de caja...")
        try:
            with open(CASH_FLOW_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute(
                        "INSERT INTO cash_flow (fecha_hora, tipo, monto, concepto) VALUES (?, ?, ?, ?)",
                        (row["fecha_hora"], row["tipo"], float(row["monto"]), row["concepto"])
                    )
            print("✓ Flujo de caja migrado.")
        except Exception as e:
            print(f"Error migrando flujo de caja: {e}")

    conn.commit()
    conn.close()
    print("\nMigración completada con éxito.")

if __name__ == "__main__":
    migrate()
