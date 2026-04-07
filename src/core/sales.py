import csv
import json
import os
from datetime import datetime, date
from src.core.config import SALES_CSV, CASH_FLOW_CSV, TICKETS_CSV
from src.utils.file_lock import flock, LOCK_SH, LOCK_EX, LOCK_UN

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

        if not os.path.exists(TICKETS_CSV):
            with open(TICKETS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ticket_id", "fecha_hora", "cajero", "total", "estado", "items_json"])

    def log_sale(self, items, timestamp=None, sign=1):
        """Log a collection of sale items to ventas.csv."""
        if not items:
            return False, "No hay productos para registrar."

        timestamp = timestamp or datetime.now().isoformat()
        try:
            with open(self.sales_file, "a", newline="", encoding="utf-8") as f:
                flock(f, LOCK_EX)
                try:
                    writer = csv.writer(f)
                    for barcode, item in items.items():
                        qty = item.get("qty", 0) * sign
                        price = item.get("precio", 0.0)
                        total = qty * price
                        writer.writerow([
                            timestamp,
                            barcode,
                            item.get("nombre", "Unknown"),
                            qty,
                            price,
                            total,
                        ])
                    return True, "Venta registrada exitosamente."
                finally:
                    flock(f, LOCK_UN)
        except Exception as e:
            return False, f"Error al registrar venta: {e}"

    def create_ticket_id(self):
        now = datetime.now()
        return now.strftime("%Y%m%d%H%M%S%f")[:-3]

    def log_ticket(self, ticket_id, items, total, cashier, timestamp=None, status="activa"):
        if not items:
            return False, "No hay productos para registrar."
        timestamp = timestamp or datetime.now().isoformat()
        try:
            with open(TICKETS_CSV, "a", newline="", encoding="utf-8") as f:
                flock(f, LOCK_EX)
                try:
                    writer = csv.writer(f)
                    writer.writerow([
                        ticket_id,
                        timestamp,
                        cashier,
                        total,
                        status,
                        json.dumps(items, ensure_ascii=False),
                    ])
                    return True, "Ticket guardado."
                finally:
                    flock(f, LOCK_UN)
        except Exception as e:
            return False, f"Error al guardar ticket: {e}"

    def get_tickets_for_date(self, target_date: date):
        tickets = []
        try:
            with open(TICKETS_CSV, "r", encoding="utf-8") as f:
                flock(f, LOCK_SH)
                try:
                    reader = csv.DictReader(f)
                    for row in reader:
                        dt = datetime.fromisoformat(row["fecha_hora"]).date()
                        if dt == target_date:
                            tickets.append(row)
                finally:
                    flock(f, LOCK_UN)
        except FileNotFoundError:
            pass
        return tickets

    def get_ticket(self, ticket_id: str):
        try:
            with open(TICKETS_CSV, "r", encoding="utf-8") as f:
                flock(f, LOCK_SH)
                try:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row["ticket_id"] == ticket_id:
                            return row
                finally:
                    flock(f, LOCK_UN)
        except FileNotFoundError:
            return None
        return None

    def cancel_ticket(self, ticket_id: str):
        try:
            with open(TICKETS_CSV, "r", encoding="utf-8") as f:
                flock(f, LOCK_SH)
                try:
                    rows = list(csv.DictReader(f))
                finally:
                    flock(f, LOCK_UN)
        except FileNotFoundError:
            return False, "No hay tickets registrados."

        updated = False
        ticket_row = None
        for row in rows:
            if row["ticket_id"] == ticket_id:
                ticket_row = row
                if row["estado"] == "cancelada":
                    return False, "La venta ya fue cancelada."
                row["estado"] = "cancelada"
                updated = True
                break

        if not updated or ticket_row is None:
            return False, "Ticket no encontrado."

        ticket_date = datetime.fromisoformat(ticket_row["fecha_hora"]).date()
        if ticket_date != date.today():
            return False, "Solo se pueden cancelar ventas del día."

        # Rewrite file with updated status
        try:
            with open(TICKETS_CSV, "w", newline="", encoding="utf-8") as f:
                flock(f, LOCK_EX)
                try:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=["ticket_id", "fecha_hora", "cajero", "total", "estado", "items_json"]
                    )
                    writer.writeheader()
                    writer.writerows(rows)
                finally:
                    flock(f, LOCK_UN)
        except Exception as e:
            return False, f"No se pudo cancelar el ticket: {e}"

        return True, ticket_row

    def log_cash_flow(self, transaction_type, amount, concept):
        """Log a cash movement (Entrada, Salida, Venta) to flujo_caja.csv."""
        timestamp = datetime.now().isoformat()
        try:
            with open(self.cash_flow_file, "a", newline="", encoding="utf-8") as f:
                flock(f, LOCK_EX)
                try:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, transaction_type, amount, concept])
                    return True, "Movimiento de caja registrado."
                finally:
                    flock(f, LOCK_UN)
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
                flock(f, LOCK_SH)
                try:
                    reader = csv.DictReader(f)
                    for row in reader:
                        dt = datetime.fromisoformat(row["fecha_hora"]).date()
                        if start_date <= dt <= end_date:
                            totals["sales"] += float(row["total"])
                finally:
                    flock(f, LOCK_UN)
        except FileNotFoundError:
            pass

        # Process cash flow entries/exits
        try:
            with open(self.cash_flow_file, mode="r", encoding="utf-8") as f:
                flock(f, LOCK_SH)
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
                    flock(f, LOCK_UN)
        except FileNotFoundError:
            pass

        totals["net"] = totals["sales"] + totals["entries"] - totals["exits"]
        return totals
