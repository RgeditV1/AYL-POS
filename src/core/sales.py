import csv
import fcntl
import os
from datetime import datetime
from src.core.config import SALES_CSV, CASH_FLOW_CSV

class SalesManager:
    """Manages sale entries and cash flow records in CSV format."""

    def __init__(self, sales_file=None, cash_flow_file=None):
        self.sales_file = sales_file or SALES_CSV
        self.cash_flow_file = cash_flow_file or CASH_FLOW_CSV
        self.ensure_files_exist()

    def ensure_files_exist(self):
        """Ensure necessary CSV logs exist with proper headers."""
        if not os.path.exists(self.sales_file):
            with open(self.sales_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["fecha_hora", "codigo", "nombre", "cantidad", "precio_unitario", "total"])
        
        if not os.path.exists(self.cash_flow_file):
            with open(self.cash_flow_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["fecha_hora", "tipo", "monto", "concepto"])

    def log_sale(self, items):
        """Log a collection of sale items to ventas.csv."""
        if not items:
            return False, "No hay productos para registrar."

        timestamp = datetime.now().isoformat()
        try:
            with open(self.sales_file, "a", newline="", encoding="utf-8") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    writer = csv.writer(f)
                    for barcode, item in items.items():
                        writer.writerow([
                            timestamp,
                            barcode,
                            item.get("nombre", "Unknown"),
                            item.get("qty", 0),
                            item.get("precio", 0.0),
                            item.get("qty", 0) * item.get("precio", 0.0),
                        ])
                    return True, "Venta registrada exitosamente."
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            return False, f"Error al registrar venta: {e}"

    def log_cash_flow(self, transaction_type, amount, concept):
        """Log a cash movement (Entrada, Salida, Venta) to flujo_caja.csv."""
        timestamp = datetime.now().isoformat()
        try:
            with open(self.cash_flow_file, "a", newline="", encoding="utf-8") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, transaction_type, amount, concept])
                    return True, "Movimiento de caja registrado."
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            return False, f"Error al registrar flujo de caja: {e}"

    def get_totals_for_range(self, start_date, end_date):
        """
        Calculate totals from sales and cash flow between dates.
        start_date and end_date are datetime.date objects.
        Returns a dict with sales, entries, exits, and net total.
        """
        totals = {
            "sales": 0.0,
            "entries": 0.0,
            "exits": 0.0,
            "net": 0.0
        }

        # Process sales
        try:
            with open(self.sales_file, mode="r", encoding="utf-8") as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    reader = csv.DictReader(f)
                    for row in reader:
                        dt = datetime.fromisoformat(row["fecha_hora"]).date()
                        if start_date <= dt <= end_date:
                            totals["sales"] += float(row["total"])
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except FileNotFoundError:
            pass

        # Process cash flow entries/exits
        try:
            with open(self.cash_flow_file, mode="r", encoding="utf-8") as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    reader = csv.DictReader(f)
                    for row in reader:
                        dt = datetime.fromisoformat(row["fecha_hora"]).date()
                        if start_date <= dt <= end_date:
                            amount = float(row["monto"])
                            if row["tipo"] == "Entrada":
                                totals["entries"] += amount
                            elif row["tipo"] == "Salida":
                                totals["exits"] += amount
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except FileNotFoundError:
            pass

        totals["net"] = totals["sales"] + totals["entries"] - totals["exits"]
        return totals
