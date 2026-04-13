import asyncio
import json
import platform
from datetime import datetime
import flet as ft
from src.core.inventory import InventoryManager
from src.core.sales import SalesManager
from src.core.settings import SettingsManager
from src.core.printer import PrinterManager
from src.core.ticket import build_ticket_text


class POSView(ft.Container):
    """Main POS View. Reimplementation of legacy pos_gui.py in Flet."""

    def __init__(self, username: str, role: str, on_logout=None, on_open_reports=None,
                 on_open_inventory=None, on_open_settings=None, on_open_about=None):
        super().__init__()
        self.expand = True
        self.username = username
        self.role = role
        self.on_logout = on_logout
        self.on_open_reports = on_open_reports
        self.on_open_inventory = on_open_inventory
        self.on_open_settings = on_open_settings
        self.on_open_about = on_open_about

        # Core managers
        self.inventory_manager = InventoryManager()
        self.sales_manager = SalesManager()
        self.settings_manager = SettingsManager()

        # Load data
        self.settings = self.settings_manager.load_settings()
        self.printer_manager = PrinterManager(self.settings)
        self._reload_products()

        # Sale state: multiple tickets
        self.active_tickets = {1: {}, 2: {}}
        self.current_ticket_id = 1
        self.last_ticket_id = None

        # Build UI controls
        self._init_controls()
        self._build_ui()

    @property
    def sale_items(self):
        return self.active_tickets[self.current_ticket_id]

    def _reload_products(self):
        """Load products into a dict indexed by code."""
        products_list = self.inventory_manager.load_products()
        self.products = {p["codigo"]: p for p in products_list}

    # ──────────────────────────────────────────────
    # UI Construction
    # ──────────────────────────────────────────────

    def _init_controls(self):
        """Initialize all reusable controls."""
        # Header clock
        self.date_text = ft.Text("", size=12, color=ft.Colors.SECONDARY)
        self.clock_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD)

        # Search field
        self.search_field = ft.TextField(
            hint_text="Buscar por nombre o código... (Enter para agregar)",
            autofocus=True,
            expand=True,
            border_radius=10,
            on_change=self._on_search_change,
            on_submit=self._add_first_match,
        )

        # Suggestions dropdown
        self.suggestions_list = ft.ListView(
            height=0,
            spacing=0,
            visible=False,
        )

        # Items in left panel
        self.items_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=6,
        )

        # Items in right panel (compact)
        self.order_items_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            height=100,
            spacing=2,
        )

        # Total
        self.total_text = ft.Text(
            "$0.00", size=38, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY
        )

        # Status
        self.status_text = ft.Text("", color=ft.Colors.SECONDARY, size=13)

        # Ticket tabs
        self.ticket_tabs_row = ft.Row(spacing=4)
        self._refresh_ticket_tabs()

    def _build_ui(self):
        """Assemble the full POS layout."""
        header = self._build_header()
        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()

        self.content = ft.Column(
            [
                header,
                ft.Row(
                    [left_panel, right_panel],
                    expand=True,
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _build_header(self):
        business_name = self.settings.get("business_name", "AYL POS")

        nav_buttons = []
        if self.role == "admin":
            for label, handler in [
                ("Productos", self._open_products),
                ("Reportes", self._open_reports),
                ("Ajustes", self._open_settings),
            ]:
                nav_buttons.append(
                    ft.TextButton(
                        content=ft.Text(label, size=13),
                        on_click=handler,
                    )
                )

        nav_buttons.append(
            ft.TextButton(
                content=ft.Text("Acerca de", size=13),
                on_click=self._open_about,
            )
        )

        nav_buttons.append(
            ft.OutlinedButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.LOGOUT, size=16), ft.Text("Salir", size=13)],
                    spacing=4,
                    tight=True,
                ),
                on_click=self._logout,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            )
        )

        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                business_name,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Row(
                                [self.date_text, ft.Text("·", size=12), self.clock_text],
                                spacing=6,
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Row(
                        [
                            ft.Text(
                                f"👤 {self.username}  [{self.role}]",
                                size=13,
                                color=ft.Colors.SECONDARY,
                            ),
                            *nav_buttons,
                        ],
                        spacing=8,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=20, top=12, right=20, bottom=12),
            bgcolor="#1E293B",
            border=ft.Border(
                bottom=ft.BorderSide(1, "#334155")
            ),
        )

    def _build_left_panel(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Venta", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([self.search_field], spacing=8),
                    ft.Container(
                        content=self.suggestions_list,
                        bgcolor="#1E293B",
                        border_radius=8,
                        visible=True,
                    ),
                    self.status_text,
                    ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                    self.items_column,
                ],
                expand=True,
                spacing=10,
            ),
            expand=True,
            padding=20,
        )

    def _build_right_panel(self):
        pay_button = ft.FilledButton(
            content=ft.Text("F1 · COBRAR", size=17, weight=ft.FontWeight.BOLD),
            height=60,
            on_click=self._show_payment_dialog,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                bgcolor="#10B981",
                color=ft.Colors.WHITE,
            ),
        )

        clear_button = ft.OutlinedButton(
            content=ft.Text("Limpiar ticket", size=13),
            expand=True,
            on_click=self._clear_sale,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=12, top=8, right=12, bottom=8),
            ),
        )

        reprint_button = ft.OutlinedButton(
            content=ft.Text("Reimprimir ticket", size=13),
            expand=True,
            on_click=lambda e: self._open_reprint_dialog(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=12, top=8, right=12, bottom=8),
            ),
        )

        reprint_last_button = ft.OutlinedButton(
            content=ft.Text("Reimprimir último", size=13),
            expand=True,
            on_click=lambda e: self._reprint_last_ticket(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=12, top=8, right=12, bottom=8),
            ),
        )

        cancel_sale_button = ft.OutlinedButton(
            content=ft.Text("Cancelar venta", size=13),
            expand=True,
            on_click=lambda e: self._open_cancel_sale_dialog(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=12, top=8, right=12, bottom=8),
            ),
        )


        free_item_button = ft.OutlinedButton(
            content=ft.Text("Artículo libre", size=13),
            expand=True,
            on_click=lambda e: self._open_free_item_dialog(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=12, top=8, right=12, bottom=8),
            ),
        )

        cash_in_button = ft.TextButton(
            content=ft.Text("+ Entrada", size=12, color=ft.Colors.GREEN),
            on_click=lambda e: self._open_cash_flow("Entrada"),
            expand=True,
        )
        cash_out_button = ft.TextButton(
            content=ft.Text("- Salida", size=12, color=ft.Colors.RED),
            on_click=lambda e: self._open_cash_flow("Salida"),
            expand=True,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Tickets:", size=13, color=ft.Colors.SECONDARY),
                    self.ticket_tabs_row,
                    ft.Divider(),
                    ft.Text("Orden actual:", size=13, color=ft.Colors.SECONDARY),
                    self.order_items_column,
                    ft.Divider(),
                    ft.Row(
                        [
                            ft.Text("TOTAL", size=20, weight=ft.FontWeight.BOLD),
                            self.total_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                    pay_button,
                    ft.Divider(height=2, color=ft.Colors.TRANSPARENT),
                    ft.Row([clear_button, reprint_button], spacing=8),
                    ft.Divider(height=2, color=ft.Colors.TRANSPARENT),
                    ft.Row([reprint_last_button, cancel_sale_button], spacing=8),
                    ft.Divider(height=2, color=ft.Colors.TRANSPARENT),
                    ft.Row([free_item_button], spacing=8),
                    ft.Divider(),
                    ft.Row(
                        [cash_in_button, cash_out_button],
                        spacing=8,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            width=340,
            padding=20,
            bgcolor="#1E293B",
        )

    # ──────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────

    def did_mount(self):
        self.page.run_task(self._start_clock)
        # Keyboard shortcut: F1 → pay
        self.page.on_keyboard_event = self._on_keyboard

    def will_unmount(self):
        self.page.on_keyboard_event = None

    async def _start_clock(self):
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        while self.page:
            now = datetime.now()
            self.date_text.value = (
                f"{dias[now.weekday()]}, {now.day} de {meses[now.month - 1]}"
            )
            self.clock_text.value = now.strftime("%I:%M:%S %p")
            try:
                self.date_text.update()
                self.clock_text.update()
            except Exception:
                break
            await asyncio.sleep(1)

    def _on_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "F1":
            self._show_payment_dialog()

    # ──────────────────────────────────────────────
    # Ticket Management
    # ──────────────────────────────────────────────

    def _refresh_ticket_tabs(self):
        self.ticket_tabs_row.controls.clear()
        for t_id in sorted(self.active_tickets.keys()):
            is_active = t_id == self.current_ticket_id
            count = len(self.active_tickets[t_id])
            label = f"#{t_id}" + (f" ({count})" if count else "")
            self.ticket_tabs_row.controls.append(
                ft.ElevatedButton(
                    content=ft.Text(label, size=13),
                    on_click=lambda e, tid=t_id: self._switch_ticket(tid),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        bgcolor=ft.Colors.PRIMARY if is_active else None,
                        color=ft.Colors.WHITE if is_active else None,
                    ),
                    height=36,
                )
            )
        try:
            self.ticket_tabs_row.update()
        except Exception:
            pass

    def _switch_ticket(self, ticket_id):
        self.current_ticket_id = ticket_id
        self._refresh_ticket_tabs()
        self._refresh_items_list()
        self._update_total()

    # ──────────────────────────────────────────────
    # Search Logic
    # ──────────────────────────────────────────────

    def _on_search_change(self, e):
        query = e.control.value.strip().lower()
        if len(query) < 1:
            self.suggestions_list.controls.clear()
            self.suggestions_list.height = 0
            self.suggestions_list.visible = False
            try:
                self.suggestions_list.update()
            except Exception:
                pass
            return

        scored = []
        for code, p in self.products.items():
            name = p["nombre"].lower()
            if query in name or query in code.lower():
                score = 3 if name.startswith(query) else (2 if code.lower().startswith(query) else 1)
                scored.append((score, code, p))

        scored.sort(key=lambda x: (-x[0], x[2]["nombre"]))
        results = scored[:8]

        self.suggestions_list.controls.clear()
        for _, code, p in results:
            precio = float(p.get("precio", 0))
            self.suggestions_list.controls.append(
                ft.ListTile(
                    title=ft.Text(p["nombre"], size=14),
                    subtitle=ft.Text(f"Cód: {code}  ·  ${precio:.2f}", size=12),
                    on_click=lambda e, c=code: self._add_product_by_code(c),
                    dense=True,
                    shape=ft.RoundedRectangleBorder(radius=0),
                )
            )

        self.suggestions_list.height = min(len(results) * 60, 200)
        self.suggestions_list.visible = bool(results)
        try:
            self.suggestions_list.update()
        except Exception:
            pass

    def _add_first_match(self, e):
        query = self.search_field.value.strip()
        if not query:
            return

        # Exact barcode
        normalized = query.lstrip("0") or "0"
        if normalized in self.products:
            self._add_product_by_code(normalized)
            return

        # Exact name
        for code, p in self.products.items():
            if p["nombre"].lower() == query.lower():
                self._add_product_by_code(code)
                return

        # First partial match
        query_lower = query.lower()
        for code, p in self.products.items():
            if query_lower in p["nombre"].lower() or query_lower in code.lower():
                self._add_product_by_code(code)
                return

        self.status_text.value = f"Producto '{query}' no encontrado."
        try:
            self.status_text.update()
        except Exception:
            pass

    def _add_product_by_code(self, code: str):
        product = self.products.get(code)
        if not product:
            return

        ticket = self.active_tickets[self.current_ticket_id]
        self._add_or_increment_item(
            ticket=ticket,
            code=code,
            name=product["nombre"],
            price=float(product.get("precio", 0)),
            qty=1,
            allow_name_merge=False,
        )

        self.search_field.value = ""
        self.suggestions_list.controls.clear()
        self.suggestions_list.visible = False
        self.suggestions_list.height = 0
        self.status_text.value = f"✓ {product['nombre']} agregado."

        self._refresh_items_list()
        self._refresh_ticket_tabs()
        self._update_total()

        try:
            self.search_field.update()
            self.suggestions_list.update()
            self.status_text.update()
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # Sale Items
    # ──────────────────────────────────────────────

    def _increment_qty(self, code):
        ticket = self.active_tickets[self.current_ticket_id]
        if code in ticket:
            ticket[code]["qty"] += 1
            self._refresh_items_list()
            self._refresh_ticket_tabs()
            self._update_total()

    def _decrement_qty(self, code):
        ticket = self.active_tickets[self.current_ticket_id]
        if code in ticket:
            ticket[code]["qty"] -= 1
            if ticket[code]["qty"] <= 0:
                del ticket[code]
            self._refresh_items_list()
            self._refresh_ticket_tabs()
            self._update_total()

    def _refresh_items_list(self):
        ticket = self.active_tickets[self.current_ticket_id]
        self.items_column.controls.clear()
        self.order_items_column.controls.clear()

        if not ticket:
            self.items_column.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Sin productos. Busca algo para empezar.",
                        color=ft.Colors.SECONDARY,
                        size=14,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                )
            )

        for code, item in ticket.items():
            subtotal = item["qty"] * item["precio"]

            # Left panel row (full detail)
            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    item["nombre"],
                                    size=14,
                                    weight=ft.FontWeight.W_500,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    f"${item['precio']:.2f} c/u",
                                    size=12,
                                    color=ft.Colors.SECONDARY,
                                ),
                            ],
                            expand=True,
                            spacing=2,
                        ),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                    icon_size=20,
                                    icon_color=ft.Colors.RED,
                                    on_click=lambda e, c=code: self._decrement_qty(c),
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        str(item["qty"]),
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    width=36,
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                    icon_size=20,
                                    icon_color=ft.Colors.GREEN,
                                    on_click=lambda e, c=code: self._increment_qty(c),
                                ),
                            ],
                            spacing=0,
                        ),
                        ft.Text(
                            f"${subtotal:.2f}",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            width=72,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=14, top=10, right=14, bottom=10),
                border_radius=10,
                bgcolor="#1E293B",
                margin=ft.Margin(left=0, top=0, right=0, bottom=0),
            )
            self.items_column.controls.append(row)

            # Right panel row (compact)
            self.order_items_column.controls.append(
                ft.Row(
                    [
                        ft.Text(
                            item["nombre"],
                            size=12,
                            expand=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            color=ft.Colors.SECONDARY,
                        ),
                        ft.Text(f"×{item['qty']}", size=12, width=28),
                        ft.Text(
                            f"${subtotal:.2f}",
                            size=12,
                            weight=ft.FontWeight.W_500,
                            width=60,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                    ],
                    spacing=4,
                )
            )

        try:
            self.items_column.update()
            self.order_items_column.update()
        except Exception:
            pass

    def _update_total(self):
        ticket = self.active_tickets[self.current_ticket_id]
        total = sum(item["qty"] * item["precio"] for item in ticket.values())
        self.total_text.value = f"${total:.2f}"
        try:
            self.total_text.update()
        except Exception:
            pass

    def _clear_sale(self, e=None):
        self.active_tickets[self.current_ticket_id] = {}
        self.search_field.value = ""
        self.status_text.value = ""
        self._refresh_items_list()
        self._refresh_ticket_tabs()
        self._update_total()
        try:
            self.search_field.update()
            self.status_text.update()
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # Payment Dialog
    # ──────────────────────────────────────────────

    def _show_payment_dialog(self, e=None):
        ticket = self.active_tickets[self.current_ticket_id]
        if not ticket:
            self._show_snack("No hay productos en el ticket.", error=True)
            return

        total = sum(item["qty"] * item["precio"] for item in ticket.values())
        change_text = ft.Text(
            "Cambio: $0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN,
        )

        cash_field = ft.TextField(
            label="Efectivo recibido",
            prefix=ft.Text("$"),
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            border_radius=8,
            on_change=lambda e: self._calc_change(e, total, change_text),
        )

        # Order summary for dialog
        summary_rows = []
        for code, item in ticket.items():
            subtotal = item["qty"] * item["precio"]
            summary_rows.append(
                ft.Row(
                    [
                        ft.Text(item["nombre"], size=13, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"×{item['qty']}", size=13, color=ft.Colors.SECONDARY, width=30),
                        ft.Text(f"${subtotal:.2f}", size=13, weight=ft.FontWeight.W_500, width=65,
                                text_align=ft.TextAlign.RIGHT),
                    ]
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Cobrar  —  Total: ${total:.2f}", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Column(summary_rows, spacing=4, scroll=ft.ScrollMode.AUTO),
                        height=min(len(ticket) * 28 + 16, 160),
                        bgcolor="#1E293B",
                        border_radius=8,
                        padding=10,
                    ),
                    ft.Divider(),
                    cash_field,
                    ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                    change_text,
                ],
                tight=True,
                spacing=12,
                width=340,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("✓ Confirmar Pago", size=15),
                    on_click=lambda e: self._complete_payment(
                        dialog, ticket, total, cash_field.value
                    ),
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

    def _calc_change(self, e, total, change_text):
        try:
            cash = float(e.control.value or 0)
            diff = cash - total
            if diff >= 0:
                change_text.value = f"Cambio: ${diff:.2f}"
                change_text.color = ft.Colors.GREEN
            else:
                change_text.value = f"Falta: ${abs(diff):.2f}"
                change_text.color = ft.Colors.RED
        except ValueError:
            change_text.value = "Cambio: $0.00"
        try:
            change_text.update()
        except Exception:
            pass

    def _complete_payment(self, dialog, ticket, total, cash_received=None):
        ticket_id = self.sales_manager.create_ticket_id()
        cash_val = None
        change = None
        if cash_received not in (None, ""):
            try:
                cash_val = float(cash_received)
                change = cash_val - total
            except ValueError:
                cash_val = None
                change = None

        # Log sale to CSV and tickets
        ok_ticket, msg_ticket = self.sales_manager.log_ticket(
            ticket_id, ticket, total, self.username
        )
        if not ok_ticket:
            self._show_snack(msg_ticket, error=True)
            return
        self.last_ticket_id = ticket_id
        self.sales_manager.log_sale(ticket)

        # Update inventory stock
        adjustments = {code: item["qty"] for code, item in ticket.items()}
        self.inventory_manager.update_stock(adjustments)
        self._reload_products()

        self._close_dialog(dialog)
        self._clear_sale()

        ticket_text = build_ticket_text(
            self.settings, ticket, total, self.username, ticket_id, cash_val, change
        )
        self._try_print_text(ticket_text, on_success=f"✓ Venta de ${total:.2f} registrada.",
                             on_skip=f"✓ Venta de ${total:.2f} registrada (sin impresión).")

    # ──────────────────────────────────────────────
    # Cash Flow Dialog
    # ──────────────────────────────────────────────

    def _open_cash_flow(self, tipo: str):
        amount_field = ft.TextField(
            label=f"Monto ({tipo})",
            prefix=ft.Text("$"),
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            border_radius=8,
        )
        concept_field = ft.TextField(
            label="Concepto",
            border_radius=8,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{tipo} de Efectivo", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [amount_field, concept_field],
                tight=True,
                spacing=12,
                width=280,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Registrar"),
                    on_click=lambda e: self._save_cash_flow(
                        dialog, tipo, amount_field.value, concept_field.value
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN if tipo == "Entrada" else ft.Colors.RED,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _save_cash_flow(self, dialog, tipo, amount_str, concept):
        try:
            amount = float(amount_str or 0)
            if amount <= 0:
                self._show_snack("El monto debe ser mayor a cero.", error=True)
                return
            self.sales_manager.log_cash_flow(tipo, amount, concept or "(Sin concepto)")
            self._close_dialog(dialog)
            self._show_snack(f"{tipo} de ${amount:.2f} registrada.")
        except ValueError:
            self._show_snack("Monto inválido.", error=True)

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

    def _try_print_text(self, text, on_success=None, on_skip=None):
        if not self.printer_manager.has_valid_printer():
            if on_skip:
                self._show_snack(on_skip)
            return

        if platform.system() == "Linux" and self.settings.get("require_sudo_print"):
            self._prompt_sudo_and_print(text, on_success, on_skip)
            return

        self._show_snack("Enviando a impresora...")
        self.page.run_thread(self._print_worker, text, on_success, on_skip)

    def _print_worker(self, text, on_success=None, on_skip=None):
        ok, msg = self.printer_manager.print_text(text)
        self._log_print_result(ok, msg)
        self.page.run_task(self._after_print, ok, msg, on_success, on_skip)

    async def _after_print(self, ok, msg, on_success=None, on_skip=None):
        if ok:
            if on_success:
                self._show_snack(on_success)
        else:
            if on_skip:
                self._show_snack(f"{on_skip} · {msg}", error=True)
            else:
                self._show_snack(msg, error=True)

    def _log_print_result(self, ok, msg):
        ts = datetime.now().isoformat(timespec="seconds")
        status = "OK" if ok else "ERROR"
        print(f"[PRINT {status}] {ts} · {msg}")

    def _prompt_sudo_and_print(self, text, on_success=None, on_skip=None):
        password_field = ft.TextField(
            label="Contraseña sudo",
            password=True,
            can_reveal_password=True,
            border_radius=8,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Permisos para imprimir", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    ft.Text("Ingresa la contraseña sudo para imprimir.", size=13),
                    password_field,
                ],
                tight=True,
                spacing=10,
                width=300,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Imprimir"),
                    on_click=lambda e: self._do_sudo_print(dialog, text, password_field.value,
                                                         on_success, on_skip),
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

    def _do_sudo_print(self, dialog, text, password, on_success=None, on_skip=None):
        self._close_dialog(dialog)
        ok, msg = self.printer_manager.print_text(text, sudo_password=password)
        if ok:
            if on_success:
                self._show_snack(on_success)
        else:
            if on_skip:
                self._show_snack(f"{on_skip} · {msg}", error=True)

    def _open_reprint_dialog(self):
        today = datetime.now().date()
        tickets = self.sales_manager.get_tickets_for_date(today)
        if self.sales_manager.last_error:
            self._show_snack(self.sales_manager.last_error, error=True)
            return
        if not tickets:
            self._show_snack("No hay tickets de hoy para reimprimir.", error=True)
            return

        options = []
        for t in tickets:
            label = f"{t['ticket_id']} · ${float(t['total']):.2f} · {t['estado']}"
            options.append(ft.dropdown.Option(key=t["ticket_id"], text=label))

        ticket_dropdown = ft.Dropdown(
            label="Ticket",
            options=options,
            border_radius=8,
            expand=True,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Reimprimir Ticket", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column([ticket_dropdown], tight=True, spacing=8, width=320),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Reimprimir"),
                    on_click=lambda e: self._reprint_ticket(dialog, ticket_dropdown.value),
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

    def _reprint_ticket(self, dialog, ticket_id):
        if not ticket_id:
            return
        if dialog:
            self._close_dialog(dialog)
        row = self.sales_manager.get_ticket(ticket_id)
        if self.sales_manager.last_error:
            self._show_snack(self.sales_manager.last_error, error=True)
            return
        if not row:
            self._show_snack("Ticket no encontrado.", error=True)
            return
        try:
            items = json.loads(row.get("items_json") or "{}")
        except Exception:
            items = {}
        total = float(row.get("total", 0.0))
        ticket_text = build_ticket_text(self.settings, items, total, row.get("cajero", ""),
                                        ticket_id)
        self._try_print_text(ticket_text, on_success="Ticket reimpreso.",
                             on_skip="No se pudo imprimir el ticket.")

    def _reprint_last_ticket(self):
        if not self.last_ticket_id:
            self._show_snack("No hay un último ticket registrado.", error=True)
            return
        self._reprint_ticket(None, self.last_ticket_id)

    def _open_cancel_sale_dialog(self):
        today = datetime.now().date()
        tickets = [t for t in self.sales_manager.get_tickets_for_date(today) if t["estado"] == "activa"]
        if self.sales_manager.last_error:
            self._show_snack(self.sales_manager.last_error, error=True)
            return
        if not tickets:
            self._show_snack("No hay ventas activas para cancelar hoy.", error=True)
            return

        options = []
        for t in tickets:
            label = f"{t['ticket_id']} · ${float(t['total']):.2f}"
            options.append(ft.dropdown.Option(key=t["ticket_id"], text=label))

        ticket_dropdown = ft.Dropdown(
            label="Venta",
            options=options,
            border_radius=8,
            expand=True,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cancelar Venta", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column([ticket_dropdown], tight=True, spacing=8, width=320),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cerrar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Cancelar venta"),
                    on_click=lambda e: self._cancel_ticket(dialog, ticket_dropdown.value),
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

    def _cancel_ticket(self, dialog, ticket_id):
        if not ticket_id:
            return
        if dialog:
            self._close_dialog(dialog)
        ok, result = self.sales_manager.cancel_ticket(ticket_id)
        if not ok:
            self._show_snack(result, error=True)
            return
        try:
            items = json.loads(result.get("items_json") or "{}")
        except Exception:
            items = {}

        # Revert stock and register negative sale
        adjustments = {code: -item.get("qty", 0) for code, item in items.items()}
        ok_stock, msg_stock = self.inventory_manager.update_stock(adjustments)
        if not ok_stock:
            self._show_snack(msg_stock, error=True)
            return
        ok_sale, msg_sale = self.sales_manager.log_sale(items, sign=-1)
        if not ok_sale:
            self._show_snack(msg_sale, error=True)
            return
        self._reload_products()
        self._show_snack("Venta cancelada y revertida.", error=False)

    def _open_free_item_dialog(self):
        name_field = ft.TextField(label="Nombre del artículo", border_radius=8)
        price_field = ft.TextField(
            label="Precio",
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        qty_field = ft.TextField(
            label="Cantidad",
            value="1",
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        code_field = ft.TextField(
            label="Código (para inventario)",
            border_radius=8,
            disabled=True,
        )
        add_inventory_checkbox = ft.Checkbox(
            label="Agregar al inventario",
            value=False,
            on_change=lambda e: self._toggle_free_item_inventory(code_field, e.control.value),
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Artículo fuera de inventario", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    name_field,
                    price_field,
                    qty_field,
                    add_inventory_checkbox,
                    code_field,
                ],
                tight=True,
                spacing=10,
                width=340,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar"),
                    on_click=lambda e: self._close_dialog(dialog),
                ),
                ft.FilledButton(
                    content=ft.Text("Agregar"),
                    on_click=lambda e: self._add_free_item(
                        dialog,
                        name_field.value,
                        price_field.value,
                        qty_field.value,
                        add_inventory_checkbox.value,
                        code_field.value,
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

    def _toggle_free_item_inventory(self, code_field, enabled):
        code_field.disabled = not enabled
        if enabled:
            code_field.value = code_field.value or self._generate_free_item_code()
        try:
            code_field.update()
        except Exception:
            pass

    def _generate_free_item_code(self):
        return f"OTR-{datetime.now().strftime('%H%M%S')}"

    def _add_or_increment_item(self, ticket, code, name, price, qty=1, allow_name_merge=False):
        if code in ticket:
            ticket[code]["qty"] += qty
            return
        if allow_name_merge:
            for _, item in ticket.items():
                if item["nombre"].strip().lower() == name.strip().lower() and float(item["precio"]) == float(price):
                    item["qty"] += qty
                    return
        ticket[code] = {
            "nombre": name.strip(),
            "precio": float(price),
            "qty": qty,
        }

    def _add_free_item(self, dialog, name, price, qty, add_inventory, code_value):
        if not name or not str(name).strip():
            self._show_snack("Ingresa un nombre válido.", error=True)
            return
        try:
            price_val = float(price)
        except Exception:
            self._show_snack("Precio inválido.", error=True)
            return
        try:
            qty_val = int(float(qty))
            if qty_val <= 0:
                raise ValueError()
        except Exception:
            self._show_snack("Cantidad inválida.", error=True)
            return

        code = code_value.strip() if add_inventory else self._generate_free_item_code()
        if not code:
            self._show_snack("Código inválido.", error=True)
            return

        # Add to ticket
        ticket = self.active_tickets[self.current_ticket_id]
        self._add_or_increment_item(
            ticket=ticket,
            code=code,
            name=name,
            price=price_val,
            qty=qty_val,
            allow_name_merge=True,
        )

        if add_inventory:
            ok, msg = self.inventory_manager.add_product({
                "codigo": code,
                "nombre": name.strip(),
                "precio": f"{price_val:.2f}",
                "cantidad": str(qty_val),
                "costo": "0.0",
            })
            if not ok:
                self._show_snack(msg, error=True)
            else:
                self._reload_products()

        self._close_dialog(dialog)
        self._refresh_items_list()
        self._refresh_ticket_tabs()
        self._update_total()
        self._show_snack("Artículo agregado al ticket.")

    def _open_products(self, e=None):
        if self.on_open_inventory:
            self.on_open_inventory(self.username, self.role)
        else:
            self._show_snack("Módulo de Inventario no disponible.")

    def _open_settings(self, e=None):
        if self.on_open_settings:
            self.on_open_settings(self.username, self.role)
        else:
            self._show_snack("Módulo de Ajustes no disponible.")

    def _open_reports(self, e=None):
        if self.on_open_reports:
            self.on_open_reports(self.username, self.role)
        else:
            self._show_snack("Módulo de Reportes no disponible.")

    def _open_about(self, e=None):
        if self.on_open_about:
            self.on_open_about(self.username, self.role)
        else:
            self._show_snack("Módulo de Acerca de no disponible.")

    def _logout(self, e=None):
        if self.on_logout:
            self.on_logout()
