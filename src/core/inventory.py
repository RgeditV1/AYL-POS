import csv
import os
from src.core.config import PRODUCTS_CSV
from src.utils.file_lock import flock, LOCK_SH, LOCK_EX, LOCK_UN

class InventoryManager:
    """Manages product catalog and inventory stock in CSV format."""

    def __init__(self, products_file=None):
        self.products_file = products_file or PRODUCTS_CSV
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """Ensure the products file exists with proper headers."""
        if not os.path.exists(self.products_file):
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(self.products_file), exist_ok=True)
                with open(self.products_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["codigo", "nombre", "precio", "cantidad", "costo"])
            except Exception as e:
                print(f"Error creando archivo de productos: {e}")

    def load_products(self):
        """Read CSV and return a list of dictionaries."""
        products = []
        try:
            with open(self.products_file, mode="r", encoding="utf-8") as file:
                # Shared lock for reading
                flock(file, LOCK_SH)
                try:
                    reader = csv.DictReader(file)
                    for row in reader:
                        # Normalize data
                        product = {
                            "codigo": row.get("codigo", "").strip().lstrip("0") or "0",
                            "nombre": row.get("nombre", "").strip(),
                            "precio": row.get("precio", "0.0"),
                            "cantidad": row.get("cantidad", "0"),
                            "costo": row.get("costo", "0.0")
                        }
                        products.append(product)
                finally:
                    flock(file, LOCK_UN)
        except Exception:
            pass
        return products

    def save_products(self, products):
        """Overwrite CSV with the given list of product dictionaries."""
        try:
            with open(self.products_file, "w", newline="", encoding="utf-8") as f:
                flock(f, LOCK_EX)
                try:
                    writer = csv.DictWriter(f, fieldnames=["codigo", "nombre", "precio", "cantidad", "costo"])
                    writer.writeheader()
                    for p in products:
                        writer.writerow({
                            "codigo":   p["codigo"],
                            "nombre":   p["nombre"],
                            "precio":   p["precio"],
                            "cantidad": p["cantidad"],
                            "costo":    p["costo"]
                        })
                finally:
                    flock(f, LOCK_UN)
            return True, "Catálogo guardado exitosamente."
        except Exception as e:
            return False, f"Error al guardar productos: {e}"

    def update_stock(self, adjustments):
        """
        Update stock for multiple products after a sale.
        'adjustments' is a dict: {barcode: qty_to_subtract}
        """
        try:
            with open(self.products_file, mode="r+", newline="", encoding="utf-8") as file:
                flock(file, LOCK_EX)
                try:
                    reader = csv.reader(file)
                    lines = list(reader)
                    if not lines:
                        return False, "El archivo de productos está vacío."

                    header = lines[0]
                    product_rows = lines[1:]
                    
                    # Create dict for quick lookup
                    products_map = {row[0]: row for row in product_rows}
                    changes_made = False

                    for barcode, qty in adjustments.items():
                        # Normalize barcode lookup
                        lookup = barcode.strip().lstrip("0") or "0"
                        if lookup in products_map:
                            try:
                                current_stock = int(products_map[lookup][3])
                                new_stock = current_stock - qty
                                products_map[lookup][3] = str(new_stock)
                                changes_made = True
                            except (ValueError, IndexError):
                                pass
                    
                    if changes_made:
                        file.seek(0)
                        file.truncate()
                        writer = csv.writer(file)
                        writer.writerow(header)
                        # Reconstruct to maintain original order if possible, though dict loses it
                        # For now, just rewrite all current rows
                        writer.writerows(product_rows)
                        return True, "Inventario actualizado."
                    return True, "No se requirieron cambios."
                finally:
                    flock(file, LOCK_UN)
        except Exception as e:
            return False, str(e)

    def find_product(self, barcode):
        """Find a single product by barcode."""
        products = self.load_products()
        lookup = barcode.strip().lstrip("0") or "0"
        for p in products:
            if p["codigo"] == lookup:
                return p
        return None

    def add_product(self, product):
        """Append a new product to the catalog."""
        products = self.load_products()
        code = str(product.get("codigo", "")).strip()
        if not code:
            return False, "Código inválido."
        code = code.lstrip("0") or "0"

        for p in products:
            if p.get("codigo") == code:
                return False, "El código ya existe."

        products.append({
            "codigo": code,
            "nombre": str(product.get("nombre", "")).strip(),
            "precio": str(product.get("precio", "0.0")).strip() or "0.0",
            "cantidad": str(product.get("cantidad", "0")).strip() or "0",
            "costo": str(product.get("costo", "0.0")).strip() or "0.0",
        })
        return self.save_products(products)
