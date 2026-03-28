import flet as ft
from src.core.inventory import InventoryManager


class InventoryView(ft.Container):
    """
    Flet reimplementation of legacy products_gui.py.
    Full product catalog manager: search, add, edit inline, delete, save.
    """

    def __init__(self, username: str, role: str, on_back=None):
        super().__init__()
        self.expand = True
        self.username = username
        self.role = role
        self.on_back = on_back

        self.inventory_manager = InventoryManager()
        self.all_products: list[dict] = []
        self.filtered_products: list[dict] = []

        # Sort state
        self._sort_col: str | None = None
        self._sort_reverse: bool = False

        # Editing state
        self._editing_idx: int | None = None

        self._init_controls()
        self._build_ui()
        self._load_products()

    # ──────────────────────────────────────────────
    # Controls init
    # ──────────────────────────────────────────────

    def _init_controls(self):
        self.search_field = ft.TextField(
            hint_text="Buscar producto...",
            expand=True,
            border_radius=8,
            on_change=self._on_search,
        )

        # "Add product" form
        self.f_code = ft.TextField(label="Código", border_radius=8, expand=True)
        self.f_name = ft.TextField(label="Nombre", border_radius=8, expand=True)
        self.f_price = ft.TextField(
            label="Precio",
            border_radius=8,
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.f_stock = ft.TextField(
            label="Cantidad",
            border_radius=8,
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.f_cost = ft.TextField(
            label="Costo",
            border_radius=8,
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Table header
        self._col_widths = [110, None, 80, 80, 80, 80]  # code, name(expand), price, stock, cost, actions

        # Table rows column
        self.rows_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=2,
        )

        # Status
        self.status_text = ft.Text("", size=13, color=ft.Colors.SECONDARY)

        # Unsaved changes indicator
        self._unsaved = False
        self.save_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.SAVE, size=16), ft.Text("Guardar cambios", size=13)],
                spacing=6, tight=True,
            ),
            on_click=self._save,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

    def _build_ui(self):
        header = self._build_header()
        toolbar = self._build_toolbar()
        add_form = self._build_add_form()
        table = self._build_table()

        self.content = ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Column(
                        [toolbar, add_form, ft.Divider(), table, self.status_text],
                        expand=True,
                        spacing=12,
                    ),
                    expand=True,
                    padding=20,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _build_header(self):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda e: self._go_back(),
                                tooltip="Volver al POS",
                            ),
                            ft.Text("Gestión de Inventario", size=18, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            ft.Text(
                                f"👤 {self.username}  [{self.role}]",
                                size=13,
                                color=ft.Colors.SECONDARY,
                            ),
                            self.save_btn,
                        ],
                        spacing=12,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=20, top=12, right=20, bottom=12),
            bgcolor="#1E293B",
            border=ft.Border(bottom=ft.BorderSide(1, "#334155")),
        )

    def _build_toolbar(self):
        return ft.Row(
            [
                self.search_field,
                ft.OutlinedButton(
                    content=ft.Row(
                        [ft.Icon(ft.Icons.REFRESH, size=16), ft.Text("Recargar", size=13)],
                        spacing=6, tight=True,
                    ),
                    on_click=lambda e: self._load_products(),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                ),
            ],
            spacing=10,
        )

    def _build_add_form(self):
        add_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.ADD, size=16), ft.Text("Agregar", size=14)],
                spacing=6, tight=True,
            ),
            on_click=lambda e: self._add_product(),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            height=48,
        )
        clear_btn = ft.OutlinedButton(
            content=ft.Text("Limpiar", size=13),
            on_click=lambda e: self._clear_form(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=48,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Agregar nuevo producto", size=14, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PRIMARY),
                    ft.Row(
                        [self.f_code, self.f_name, self.f_price, self.f_stock, self.f_cost, add_btn, clear_btn],
                        spacing=10,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.Padding(left=16, top=12, right=16, bottom=12),
            bgcolor="#1E293B",
            border_radius=10,
        )

    def _build_table(self):
        header_row = ft.Container(
            content=ft.Row(
                [
                    self._header_cell("Código", "codigo", width=110),
                    self._header_cell("Nombre", "nombre"),
                    self._header_cell("Precio", "precio", width=90),
                    self._header_cell("Cantidad", "cantidad", width=100),
                    self._header_cell("Costo", "costo", width=100),
                    ft.Container(width=110),  # actions column
                ],
                spacing=4,
            ),
            padding=ft.Padding(left=10, top=8, right=10, bottom=8),
            bgcolor="#334155",
            border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=0, bottom_right=0),
        )

        return ft.Column(
            [
                header_row,
                ft.Container(
                    content=self.rows_column,
                    expand=True,
                    bgcolor="#1E293B",
                    border_radius=ft.BorderRadius(top_left=0, top_right=0, bottom_left=8, bottom_right=8),
                    padding=4,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _header_cell(self, label: str, col_key: str, width: int | None = None):
        btn = ft.TextButton(
            content=ft.Text(label, size=12, weight=ft.FontWeight.BOLD),
            on_click=lambda e, k=col_key: self._sort_by(k),
            style=ft.ButtonStyle(
                padding=ft.Padding(left=0, top=0, right=0, bottom=0),
                shape=ft.RoundedRectangleBorder(radius=0),
            ),
        )
        if width:
            return ft.Container(content=btn, width=width)
        return ft.Container(content=btn, expand=True)

    # ──────────────────────────────────────────────
    # Data
    # ──────────────────────────────────────────────

    def did_mount(self):
        pass  # Already loaded in __init__

    def _load_products(self):
        self.all_products = self.inventory_manager.load_products()
        self.filtered_products = list(self.all_products)
        self._unsaved = False
        self._render_rows()
        self.status_text.value = f"{len(self.all_products)} productos cargados."
        try:
            self.status_text.update()
        except Exception:
            pass

    def _render_rows(self):
        self.rows_column.controls.clear()

        if not self.filtered_products:
            self.rows_column.controls.append(
                ft.Container(
                    content=ft.Text("Sin resultados.", color=ft.Colors.SECONDARY,
                                    size=14, text_align=ft.TextAlign.CENTER),
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                )
            )
        else:
            for idx, p in enumerate(self.filtered_products):
                self.rows_column.controls.append(self._make_row(idx, p))

        try:
            self.rows_column.update()
        except Exception:
            pass

    def _make_row(self, row_idx: int, p: dict):
        """Build an editable product row."""
        is_even = row_idx % 2 == 0
        bg = "#1E293B" if is_even else "#172032"

        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(p["codigo"], size=13, width=110, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(p["nombre"], size=13, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"${float(p.get('precio', 0)):.2f}", size=13, width=90,
                            text_align=ft.TextAlign.RIGHT),
                    ft.Text(str(p.get("cantidad", 0)), size=13, width=100,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text(f"${float(p.get('costo', 0)):.2f}", size=13, width=90,
                            text_align=ft.TextAlign.RIGHT),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_size=18,
                                tooltip="Editar",
                                on_click=lambda e, i=row_idx, prod=p: self._open_edit_dialog(i, prod),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=18,
                                icon_color=ft.Colors.RED,
                                tooltip="Eliminar",
                                on_click=lambda e, prod=p: self._confirm_delete(prod),
                            ),
                        ],
                        spacing=0,
                        width=110,
                    ),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=10, top=8, right=10, bottom=8),
            bgcolor=bg,
            border_radius=4,
        )

    # ──────────────────────────────────────────────
    # Search & Sort
    # ──────────────────────────────────────────────

    def _on_search(self, e):
        query = e.control.value.strip().lower()
        if not query:
            self.filtered_products = list(self.all_products)
        else:
            self.filtered_products = [
                p for p in self.all_products
                if query in p["nombre"].lower() or query in p["codigo"].lower()
                or query in str(p.get("precio", "")).lower()
                or query in str(p.get("cantidad", "")).lower()
            ]
        self._render_rows()
        self.status_text.value = f"{len(self.filtered_products)} de {len(self.all_products)} productos."
        try:
            self.status_text.update()
        except Exception:
            pass

    def _sort_by(self, col: str):
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False

        def sort_key(p):
            val = p.get(col, "")
            if col in ("precio", "cantidad", "codigo"):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
            return str(val).lower()

        self.all_products.sort(key=sort_key, reverse=self._sort_reverse)
        self._on_search(type("E", (), {"control": type("C", (), {"value": self.search_field.value or ""})()})())

    # ──────────────────────────────────────────────
    # Add Product
    # ──────────────────────────────────────────────

    def _add_product(self):
        code = self.f_code.value.strip().lstrip("0") or "0"
        name = self.f_name.value.strip()
        price_str = self.f_price.value.strip()
        stock_str = self.f_stock.value.strip() or "0"
        cost_str = self.f_cost.value.strip() or "0"

        # Validation
        if not code or not name or not price_str:
            self._show_snack("Código, nombre y precio son requeridos.", error=True)
            return
        try:
            float(price_str)
            int(stock_str)
            float(cost_str)
        except ValueError:
            self._show_snack("Precio, cantidad y costo deben ser números.", error=True)
            return
        if any(p["codigo"] == code for p in self.all_products):
            self._show_snack(f"El código '{code}' ya existe.", error=True)
            return

        new_p = {"codigo": code, "nombre": name, "precio": price_str, "cantidad": stock_str, "costo": cost_str}
        self.all_products.append(new_p)
        self.filtered_products = list(self.all_products)
        self._unsaved = True
        self._render_rows()
        self._clear_form()
        self.status_text.value = f"✓ Producto '{name}' agregado. Recuerda guardar."
        try:
            self.status_text.update()
        except Exception:
            pass

    def _clear_form(self):
        self.f_code.value = ""
        self.f_name.value = ""
        self.f_price.value = ""
        self.f_stock.value = ""
        self.f_cost.value = ""
        try:
            self.f_code.update()
            self.f_name.update()
            self.f_price.update()
            self.f_stock.update()
            self.f_cost.update()
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # Edit Dialog
    # ──────────────────────────────────────────────

    def _open_edit_dialog(self, row_idx: int, p: dict):
        """Open an inline edit dialog for a product."""
        e_code = ft.TextField(label="Código", value=p["codigo"], border_radius=8, autofocus=True)
        e_name = ft.TextField(label="Nombre", value=p["nombre"], border_radius=8)
        e_price = ft.TextField(
            label="Precio", value=str(p.get("precio", "")),
            border_radius=8, keyboard_type=ft.KeyboardType.NUMBER,
        )
        e_stock = ft.TextField(
            label="Cantidad", value=str(p.get("cantidad", "0")),
            border_radius=8, keyboard_type=ft.KeyboardType.NUMBER,
        )
        e_cost = ft.TextField(
            label="Costo", value=str(p.get("costo", "0")),
            border_radius=8, keyboard_type=ft.KeyboardType.NUMBER,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Editar: {p['nombre']}", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [e_code, e_name, e_price, e_stock, e_cost],
                tight=True,
                spacing=12,
                width=320,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Guardar"),
                    on_click=lambda e: self._save_edit(
                        dialog, row_idx, p,
                        e_code.value, e_name.value, e_price.value, e_stock.value, e_cost.value,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.PRIMARY,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _save_edit(self, dialog, row_idx, original, code, name, price_str, stock_str, cost_str):
        """Validate and apply an edit."""
        code = code.strip().lstrip("0") or "0"
        name = name.strip()
        price_str = price_str.strip()
        stock_str = stock_str.strip() or "0"
        cost_str = cost_str.strip() or "0"

        if not code or not name or not price_str:
            self._show_snack("Todos los campos son requeridos.", error=True)
            return
        try:
            float(price_str)
            int(stock_str)
            float(cost_str)
        except ValueError:
            self._show_snack("Precio, cantidad y costo deben ser números.", error=True)
            return
        # Check code uniqueness (excluding current)
        if code != original["codigo"] and any(p["codigo"] == code for p in self.all_products):
            self._show_snack(f"El código '{code}' ya existe.", error=True)
            return

        # Find in all_products and update
        for p in self.all_products:
            if p["codigo"] == original["codigo"]:
                p["codigo"] = code
                p["nombre"] = name
                p["precio"] = price_str
                p["cantidad"] = stock_str
                p["costo"] = cost_str
                break

        self._unsaved = True
        self._close_dialog(dialog)
        self._render_rows()
        self.status_text.value = f"✓ '{name}' actualizado. Recuerda guardar."
        try:
            self.status_text.update()
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────

    def _confirm_delete(self, p: dict):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar eliminación", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                f"¿Eliminar '{p['nombre']}' (código: {p['codigo']})?\nEsta acción no se puede deshacer.",
                size=14,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Eliminar"),
                    on_click=lambda e: self._delete_product(dialog, p),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _delete_product(self, dialog, p: dict):
        self.all_products = [x for x in self.all_products if x["codigo"] != p["codigo"]]
        self.filtered_products = [x for x in self.filtered_products if x["codigo"] != p["codigo"]]
        self._unsaved = True
        self._close_dialog(dialog)
        self._render_rows()
        self.status_text.value = f"✓ '{p['nombre']}' eliminado. Recuerda guardar."
        try:
            self.status_text.update()
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # Save
    # ──────────────────────────────────────────────

    def _save(self, e=None):
        if not self._unsaved:
            self._show_snack("No hay cambios pendientes.")
            return

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar guardado", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                f"¿Guardar {len(self.all_products)} productos? Esto sobreescribirá el catálogo.",
                size=14,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Guardar"),
                    on_click=lambda e: self._do_save(dialog),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _do_save(self, dialog):
        success, message = self.inventory_manager.save_products(self.all_products)
        self._close_dialog(dialog)
        if success:
            self._unsaved = False
            self._show_snack("✓ Catálogo guardado exitosamente.")
        else:
            self._show_snack(f"Error: {message}", error=True)

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def _show_snack(self, message: str, error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _go_back(self):
        if self._unsaved:
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Cambios sin guardar", size=16, weight=ft.FontWeight.BOLD),
                content=ft.Text("Hay cambios sin guardar. ¿Salir de todas formas?", size=14),
                actions=[
                    ft.TextButton(
                        content=ft.Text("Cancelar"),
                        on_click=lambda e: self._close_dialog(dialog),
                    ),
                    ft.FilledButton(
                        content=ft.Text("Salir sin guardar"),
                        on_click=lambda e: self._force_back(dialog),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ],
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
        else:
            if self.on_back:
                self.on_back()

    def _force_back(self, dialog):
        self._close_dialog(dialog)
        if self.on_back:
            self.on_back()
