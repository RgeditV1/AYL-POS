from src.core.database import get_db_manager

class InventoryManager:
    """Manages product catalog and inventory stock in SQLite."""

    def __init__(self):
        self.db = get_db_manager()

    def load_products(self):
        """Fetch all products from the database."""
        conn = self.db.get_connection()
        products = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products")
            for row in cursor.fetchall():
                products.append(dict(row))
        except Exception:
            pass
        finally:
            conn.close()
        return products

    def find_product(self, barcode):
        """Find a single product by barcode."""
        lookup = barcode.strip().lstrip("0") or "0"
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE codigo = ?", (lookup,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        except Exception:
            pass
        finally:
            conn.close()
        return None

    def add_product(self, product):
        """Insert a new product into the database."""
        code = str(product.get("codigo", "")).strip().lstrip("0") or "0"
        nombre = str(product.get("nombre", "")).strip()
        precio = float(product.get("precio", 0.0))
        cantidad = int(product.get("cantidad", 0))
        costo = float(product.get("costo", 0.0))

        if not nombre:
            return False, "Nombre inválido."

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (codigo, nombre, precio, cantidad, costo) VALUES (?, ?, ?, ?, ?)",
                (code, nombre, precio, cantidad, costo)
            )
            conn.commit()
            return True, "Producto agregado exitosamente."
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                return False, "El código ya existe."
            return False, str(e)
        finally:
            conn.close()

    def update_stock(self, adjustments):
        """
        Update stock for multiple products.
        'adjustments' is a dict: {barcode: qty_to_subtract}
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            for barcode, qty in adjustments.items():
                lookup = barcode.strip().lstrip("0") or "0"
                cursor.execute(
                    "UPDATE products SET cantidad = cantidad - ? WHERE codigo = ?",
                    (qty, lookup)
                )
            conn.commit()
            return True, "Inventario actualizado."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def save_products(self, products):
        """
        Compatibility method to match legacy CSV API.
        In SQL, we usually update specific items, but this can perform bulk updates.
        """
        # Note: In a real SQL app we might not use this, but for compatibility:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products")
            for p in products:
                cursor.execute(
                    "INSERT INTO products (codigo, nombre, precio, cantidad, costo) VALUES (?, ?, ?, ?, ?)",
                    (p["codigo"], p["nombre"], p["precio"], p["cantidad"], p["costo"])
                )
            conn.commit()
            return True, "Catálogo sincronizado exitosamente."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
