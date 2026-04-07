import json
from datetime import datetime, date
from src.core.database import get_db_manager

class SalesManager:
    """Manages sale entries, tickets, and cash flow using SQLite."""

    def __init__(self):
        self.db = get_db_manager()
        self.last_error = None

    def create_ticket_id(self):
        """Generate a unique ticket ID."""
        now = datetime.now()
        return now.strftime("%Y%m%d%H%M%S%f")[:-3]

    def log_ticket(self, ticket_id, items, total, cashier, timestamp=None, status="activa"):
        """Save a ticket header and its items into the database."""
        if not items:
            return False, "No hay productos para registrar."
        
        timestamp = timestamp or datetime.now().isoformat()
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            # 1. Save ticket header
            cursor.execute(
                "INSERT INTO tickets (ticket_id, fecha_hora, cajero, total, estado) VALUES (?, ?, ?, ?, ?)",
                (ticket_id, timestamp, cashier, total, status)
            )

            # 2. Save sale items
            for code, item in items.items():
                qty = item.get("qty", 0)
                price = item.get("precio", 0.0)
                cursor.execute(
                    """INSERT INTO sale_items (ticket_id, codigo, nombre, cantidad, precio_unitario, subtotal) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (ticket_id, code, item.get("nombre", "Unknown"), qty, price, qty * price)
                )

            conn.commit()
            return True, "Ticket guardado."
        except Exception as e:
            return False, f"Error al guardar ticket: {e}"
        finally:
            conn.close()

    def get_ticket(self, ticket_id: str):
        """Fetch a single ticket by its ID."""
        self.last_error = None
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
            row = cursor.fetchone()
            if row:
                ticket = dict(row)
                # Fetch items to simulate the legacy 'items_json' field for compatibility
                cursor.execute("SELECT * FROM sale_items WHERE ticket_id = ?", (ticket_id,))
                items_rows = cursor.fetchall()
                items_dict = {}
                for ir in items_rows:
                    items_dict[ir["codigo"]] = {
                        "nombre": ir["nombre"],
                        "precio": ir["precio_unitario"],
                        "qty": ir["cantidad"]
                    }
                ticket["items_json"] = json.dumps(items_dict, ensure_ascii=False)
                return ticket
        except Exception as e:
            self.last_error = f"Error al leer ticket: {e}"
        finally:
            conn.close()
        return None

    def get_tickets_for_date(self, target_date: date):
        """Fetch all tickets for a specific date."""
        self.last_error = None
        tickets = []
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            # In SQLite, date comparison requires careful formatting if stored as ISO string
            # We fetch all and filter or use date() function if format is consistent
            cursor.execute("SELECT * FROM tickets WHERE date(fecha_hora) = date(?)", (target_date.isoformat(),))
            for row in cursor.fetchall():
                tickets.append(dict(row))
        except Exception as e:
            self.last_error = f"Error al leer tickets: {e}"
        finally:
            conn.close()
        return tickets

    def cancel_ticket(self, ticket_id: str, allow_any_date: bool = False):
        """Mark a ticket as canceled and return the canceled row."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Ticket no encontrado."
            
            ticket = dict(row)
            if ticket["estado"] == "cancelada":
                return False, "La venta ya fue cancelada."

            if not allow_any_date:
                ticket_date = datetime.fromisoformat(ticket["fecha_hora"]).date()
                if ticket_date != date.today():
                    return False, "Solo se pueden cancelar ventas del día."

            # Update status
            cursor.execute("UPDATE tickets SET estado = 'cancelada' WHERE ticket_id = ?", (ticket_id,))
            conn.commit()
            
            # Repopulate items_json for legacy compatibility in return
            cursor.execute("SELECT * FROM sale_items WHERE ticket_id = ?", (ticket_id,))
            items_dict = {r["codigo"]: {"nombre": r["nombre"], "precio": r["precio_unitario"], "qty": r["cantidad"]} 
                          for r in cursor.fetchall()}
            ticket["estado"] = "cancelada"
            ticket["items_json"] = json.dumps(items_dict, ensure_ascii=False)
            
            return True, ticket
        except Exception as e:
            return False, f"No se pudo cancelar el ticket: {e}"
        finally:
            conn.close()

    def log_cash_flow(self, transaction_type, amount, concept):
        """Log a cash movement (Entrada, Salida, Venta) to the database."""
        timestamp = datetime.now().isoformat()
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO cash_flow (fecha_hora, tipo, monto, concepto) VALUES (?, ?, ?, ?)",
                (timestamp, transaction_type, amount, concept)
            )
            conn.commit()
            return True, "Movimiento de caja registrado."
        except Exception as e:
            return False, f"Error al registrar flujo de caja: {e}"
        finally:
            conn.close()

    def get_totals_for_range(self, start_date, end_date):
        """Calculate totals from sales and cash flow between dates."""
        totals = {"sales": 0.0, "entries": 0.0, "exits": 0.0, "net": 0.0}
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            # Sales totals (Total from active tickets)
            cursor.execute(
                "SELECT SUM(total) as total FROM tickets WHERE date(fecha_hora) BETWEEN date(?) AND date(?) AND estado = 'activa'",
                (start_date.isoformat(), end_date.isoformat())
            )
            row = cursor.fetchone()
            totals["sales"] = row["total"] or 0.0

            # Cash flow entries
            cursor.execute(
                "SELECT SUM(monto) as total FROM cash_flow WHERE date(fecha_hora) BETWEEN date(?) AND date(?) AND tipo = 'Entrada'",
                (start_date.isoformat(), end_date.isoformat())
            )
            totals["entries"] = cursor.fetchone()["total"] or 0.0

            # Cash flow exits
            cursor.execute(
                "SELECT SUM(monto) as total FROM cash_flow WHERE date(fecha_hora) BETWEEN date(?) AND date(?) AND tipo = 'Salida'",
                (start_date.isoformat(), end_date.isoformat())
            )
            totals["exits"] = cursor.fetchone()["total"] or 0.0

            totals["net"] = totals["sales"] + totals["entries"] - totals["exits"]
        except Exception:
            pass
        finally:
            conn.close()
        return totals

    def log_sale(self, items, timestamp=None, sign=1):
        """
        Legacy compatibility: Logs individual items to the old flattened format logic.
        In SQL, individual item logging is handled by log_ticket.
        This provides a mock implementation if needed by legacy callers.
        """
        # For now, this is effectively replaced by log_ticket in the new flow
        return True, "Venta registrada (SQL)."
