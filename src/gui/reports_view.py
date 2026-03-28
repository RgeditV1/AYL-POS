import csv
import os
import tempfile
import webbrowser
from datetime import date, datetime, timedelta

import flet as ft
from src.core.sales import SalesManager
from src.core.settings import SettingsManager
from src.core.config import SALES_CSV, CASH_FLOW_CSV


class ReportsView(ft.Container):
    """
    Flet reimplementation of the legacy reports_gui.py.
    Shows sales and cash-flow for a date range with totals and HTML export.
    """

    def __init__(self, username: str, role: str, on_back=None):
        super().__init__()
        self.expand = True
        self.username = username
        self.role = role
        self.on_back = on_back

        self.sales_manager = SalesManager()
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()

        self.start_date: date = date.today()
        self.end_date: date = date.today()

        self._init_controls()
        self._build_ui()

    # ──────────────────────────────────────────────
    # Controls init
    # ──────────────────────────────────────────────

    def _init_controls(self):
        today_str = date.today().isoformat()

        # Date pickers
        self.start_picker = ft.TextField(
            label="Desde",
            value=today_str,
            width=150,
            border_radius=8,
            on_blur=self._on_date_change,
            on_submit=self._on_date_change,
            hint_text="YYYY-MM-DD",
        )
        self.end_picker = ft.TextField(
            label="Hasta",
            value=today_str,
            width=150,
            border_radius=8,
            on_blur=self._on_date_change,
            on_submit=self._on_date_change,
            hint_text="YYYY-MM-DD",
        )

        # Sales table rows
        self.sales_rows = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=2,
        )

        # Cash flow table rows
        self.cash_rows = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=2,
        )

        # Totals
        self.total_ventas = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD)
        self.total_entradas = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        self.total_salidas = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
        self.total_neto = ft.Text("$0.00", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY)

        # Date range label
        self.range_label = ft.Text(
            f"Reporte del: {date.today().strftime('%Y-%m-%d')}",
            size=16,
            weight=ft.FontWeight.W_500,
        )

    def _build_ui(self):
        header = self._build_header()
        controls_bar = self._build_controls_bar()
        tables = self._build_tables()
        summary = self._build_summary()

        self.content = ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Column(
                        [controls_bar, tables, summary],
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
                            ft.Text("Reportes", size=18, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        f"👤 {self.username}  [{self.role}]",
                        size=13,
                        color=ft.Colors.SECONDARY,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=20, top=12, right=20, bottom=12),
            bgcolor="#1E293B",
            border=ft.Border(bottom=ft.BorderSide(1, "#334155")),
        )

    def _build_controls_bar(self):
        today_btn = ft.OutlinedButton(
            content=ft.Text("Hoy", size=13),
            on_click=lambda e: self._set_quick_range("today"),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        yesterday_btn = ft.OutlinedButton(
            content=ft.Text("Ayer", size=13),
            on_click=lambda e: self._set_quick_range("yesterday"),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        week_btn = ft.OutlinedButton(
            content=ft.Text("Esta semana", size=13),
            on_click=lambda e: self._set_quick_range("week"),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        month_btn = ft.OutlinedButton(
            content=ft.Text("Este mes", size=13),
            on_click=lambda e: self._set_quick_range("month"),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        export_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.PRINT, size=16), ft.Text("Exportar HTML", size=13)],
                spacing=6,
                tight=True,
            ),
            on_click=lambda e: self._export_html(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
            ),
        )

        refresh_btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.REFRESH, size=16), ft.Text("Actualizar", size=13)],
                spacing=6,
                tight=True,
            ),
            on_click=lambda e: self._on_date_change(None),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        return ft.Column(
            [
                self.range_label,
                ft.Row(
                    [
                        self.start_picker,
                        ft.Text("→", size=16),
                        self.end_picker,
                        ft.VerticalDivider(width=12),
                        today_btn,
                        yesterday_btn,
                        week_btn,
                        month_btn,
                        ft.VerticalDivider(width=12),
                        refresh_btn,
                        export_btn,
                    ],
                    spacing=8,
                    wrap=True,
                ),
            ],
            spacing=8,
        )

    def _build_tables(self):
        # Column headers for sales
        sales_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Hora", size=12, weight=ft.FontWeight.BOLD, width=140),
                    ft.Text("Producto", size=12, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text("Cant.", size=12, weight=ft.FontWeight.BOLD, width=60, text_align=ft.TextAlign.CENTER),
                    ft.Text("Total", size=12, weight=ft.FontWeight.BOLD, width=80, text_align=ft.TextAlign.RIGHT),
                ],
                spacing=4,
            ),
            padding=ft.Padding(left=10, top=6, right=10, bottom=6),
            bgcolor="#334155",
            border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=0, bottom_right=0),
        )

        # Column headers for cash flow
        cash_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Hora", size=12, weight=ft.FontWeight.BOLD, width=140),
                    ft.Text("Tipo", size=12, weight=ft.FontWeight.BOLD, width=70),
                    ft.Text("Monto", size=12, weight=ft.FontWeight.BOLD, width=80, text_align=ft.TextAlign.RIGHT),
                    ft.Text("Concepto", size=12, weight=ft.FontWeight.BOLD, expand=True),
                ],
                spacing=4,
            ),
            padding=ft.Padding(left=10, top=6, right=10, bottom=6),
            bgcolor="#334155",
            border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=0, bottom_right=0),
        )

        sales_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Ventas", size=15, weight=ft.FontWeight.BOLD),
                    sales_header,
                    ft.Container(
                        content=self.sales_rows,
                        expand=True,
                        bgcolor="#1E293B",
                        border_radius=ft.BorderRadius(top_left=0, top_right=0, bottom_left=8, bottom_right=8),
                        padding=6,
                    ),
                ],
                expand=True,
                spacing=4,
            ),
            expand=True,
        )

        cash_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Flujo de Caja", size=15, weight=ft.FontWeight.BOLD),
                    cash_header,
                    ft.Container(
                        content=self.cash_rows,
                        expand=True,
                        bgcolor="#1E293B",
                        border_radius=ft.BorderRadius(top_left=0, top_right=0, bottom_left=8, bottom_right=8),
                        padding=6,
                    ),
                ],
                expand=True,
                spacing=4,
            ),
            expand=True,
        )

        return ft.Row(
            [sales_panel, cash_panel],
            expand=True,
            spacing=20,
        )

    def _build_summary(self):
        def stat_card(label, value_widget, bg="#1E293B"):
            return ft.Container(
                content=ft.Column(
                    [ft.Text(label, size=13, color=ft.Colors.SECONDARY), value_widget],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                expand=True,
                padding=16,
                bgcolor=bg,
                border_radius=10,
                alignment=ft.Alignment.CENTER,
            )

        return ft.Row(
            [
                stat_card("Ventas Totales", self.total_ventas),
                stat_card("Entradas", self.total_entradas),
                stat_card("Salidas", self.total_salidas),
                stat_card("TOTAL NETO", self.total_neto, bg="#0F172A"),
            ],
            spacing=12,
        )

    # ──────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────

    def did_mount(self):
        self._load_data()

    # ──────────────────────────────────────────────
    # Date Handling
    # ──────────────────────────────────────────────

    def _set_quick_range(self, period: str):
        today = date.today()
        if period == "today":
            self.start_date = today
            self.end_date = today
        elif period == "yesterday":
            yesterday = today - timedelta(days=1)
            self.start_date = yesterday
            self.end_date = yesterday
        elif period == "week":
            self.start_date = today - timedelta(days=today.weekday())
            self.end_date = today
        elif period == "month":
            self.start_date = today.replace(day=1)
            self.end_date = today

        self.start_picker.value = self.start_date.isoformat()
        self.end_picker.value = self.end_date.isoformat()
        try:
            self.start_picker.update()
            self.end_picker.update()
        except Exception:
            pass
        self._load_data()

    def _on_date_change(self, e):
        try:
            self.start_date = date.fromisoformat(self.start_picker.value.strip())
            self.end_date = date.fromisoformat(self.end_picker.value.strip())
        except ValueError:
            self._show_snack("Formato de fecha inválido. Use YYYY-MM-DD.", error=True)
            return
        self._load_data()

    # ──────────────────────────────────────────────
    # Data Loading
    # ──────────────────────────────────────────────

    def _load_data(self):
        """Read CSVs and populate tables."""
        s = self.start_date
        e = self.end_date

        # Update range label
        if s == e:
            self.range_label.value = f"Reporte del: {s.strftime('%Y-%m-%d')}"
        else:
            self.range_label.value = f"Reporte: {s.strftime('%Y-%m-%d')} → {e.strftime('%Y-%m-%d')}"

        # --- Sales ---
        self.sales_rows.controls.clear()
        sales_data = []  # for export
        total_ventas_val = 0.0

        try:
            with open(SALES_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_date = datetime.fromisoformat(row["fecha_hora"]).date()
                    if s <= row_date <= e:
                        row_time = datetime.fromisoformat(row["fecha_hora"]).strftime("%Y-%m-%d %H:%M")
                        total_val = float(row["total"])
                        total_ventas_val += total_val
                        sales_data.append((row_time, row["nombre"], row["cantidad"], total_val))
                        self.sales_rows.controls.append(
                            self._table_row([
                                ft.Text(row_time, size=12, width=140, color=ft.Colors.SECONDARY),
                                ft.Text(row["nombre"], size=12, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(row["cantidad"], size=12, width=60, text_align=ft.TextAlign.CENTER),
                                ft.Text(f"${total_val:.2f}", size=12, width=80, text_align=ft.TextAlign.RIGHT,
                                        weight=ft.FontWeight.W_500),
                            ])
                        )
        except FileNotFoundError:
            pass

        if not self.sales_rows.controls:
            self.sales_rows.controls.append(
                ft.Container(
                    content=ft.Text("Sin ventas en el período.", color=ft.Colors.SECONDARY, size=13,
                                    text_align=ft.TextAlign.CENTER),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                )
            )

        # --- Cash Flow ---
        self.cash_rows.controls.clear()
        cash_data = []  # for export
        total_entradas_val = 0.0
        total_salidas_val = 0.0

        try:
            with open(CASH_FLOW_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tipo = row["tipo"]
                    if tipo not in ("Entrada", "Salida"):
                        continue
                    row_date = datetime.fromisoformat(row["fecha_hora"]).date()
                    if s <= row_date <= e:
                        row_time = datetime.fromisoformat(row["fecha_hora"]).strftime("%Y-%m-%d %H:%M")
                        amount = float(row["monto"])
                        is_entrada = tipo == "Entrada"
                        if is_entrada:
                            total_entradas_val += amount
                        else:
                            total_salidas_val += amount
                        cash_data.append((row_time, tipo, amount, row["concepto"]))
                        self.cash_rows.controls.append(
                            self._table_row([
                                ft.Text(row_time, size=12, width=140, color=ft.Colors.SECONDARY),
                                ft.Text(tipo, size=12, width=70,
                                        color=ft.Colors.GREEN if is_entrada else ft.Colors.RED,
                                        weight=ft.FontWeight.W_500),
                                ft.Text(f"${amount:.2f}", size=12, width=80, text_align=ft.TextAlign.RIGHT),
                                ft.Text(row["concepto"], size=12, expand=True, overflow=ft.TextOverflow.ELLIPSIS,
                                        color=ft.Colors.SECONDARY),
                            ])
                        )
        except FileNotFoundError:
            pass

        if not self.cash_rows.controls:
            self.cash_rows.controls.append(
                ft.Container(
                    content=ft.Text("Sin movimientos de caja en el período.", color=ft.Colors.SECONDARY, size=13,
                                    text_align=ft.TextAlign.CENTER),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                )
            )

        # --- Totals ---
        neto = total_ventas_val + total_entradas_val - total_salidas_val
        self.total_ventas.value = f"${total_ventas_val:.2f}"
        self.total_entradas.value = f"${total_entradas_val:.2f}"
        self.total_salidas.value = f"${total_salidas_val:.2f}"
        self.total_neto.value = f"${neto:.2f}"

        # Store for export
        self._sales_data = sales_data
        self._cash_data = cash_data

        try:
            self.update()
        except Exception:
            pass

    def _table_row(self, cells):
        return ft.Container(
            content=ft.Row(cells, spacing=4),
            padding=ft.Padding(left=10, top=6, right=10, bottom=6),
            border_radius=6,
        )

    # ──────────────────────────────────────────────
    # Export
    # ──────────────────────────────────────────────

    def _export_html(self):
        """Generate HTML report and open in browser."""
        s = self.start_date
        e = self.end_date
        business = self.settings.get("business_name", "AYL POS")

        sales_rows_html = ""
        for row_time, nombre, cantidad, total in getattr(self, "_sales_data", []):
            time_short = row_time.split(" ")[1] if " " in row_time else row_time
            sales_rows_html += f"""
        <div class="item">
            <div>{nombre} (x{cantidad})</div>
            <div class="item-line"><span>{time_short}</span><span>${total:.2f}</span></div>
        </div>"""

        if not sales_rows_html:
            sales_rows_html = '<div class="item" style="text-align:center">Sin ventas</div>'

        cash_rows_html = ""
        for row_time, tipo, amount, concepto in getattr(self, "_cash_data", []):
            time_short = row_time.split(" ")[1] if " " in row_time else row_time
            symbol = "+" if tipo == "Entrada" else "-"
            cash_rows_html += f"""
        <div class="item">
            <div>{symbol} {concepto}</div>
            <div class="item-line"><span>{time_short}</span><span>${amount:.2f}</span></div>
        </div>"""

        if not cash_rows_html:
            cash_rows_html = '<div class="item" style="text-align:center">Sin movimientos</div>'

        tv = self.total_ventas.value
        te = self.total_entradas.value
        ts = self.total_salidas.value
        tn = self.total_neto.value

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte - {s} a {e}</title>
    <style>
        body {{ font-family: 'Courier New', monospace; max-width: 380px; margin: auto; padding: 20px; font-size: 13px; }}
        .header {{ text-align: center; border-bottom: 2px dashed #000; padding-bottom: 10px; margin-bottom: 10px; }}
        h1 {{ margin: 4px 0; font-size: 16px; }}
        .section-title {{ font-weight: bold; text-align: center; border-bottom: 1px dashed #000; margin: 12px 0 6px 0; padding-bottom: 3px; }}
        .item {{ margin: 5px 0; line-height: 1.4; }}
        .item-line {{ display: flex; justify-content: space-between; }}
        .totals {{ border-top: 2px solid #000; margin-top: 15px; padding-top: 10px; }}
        .total-row {{ display: flex; justify-content: space-between; margin: 4px 0; font-weight: bold; }}
        .grand {{ border-top: 2px solid #000; margin-top: 8px; padding-top: 6px; font-size: 15px; }}
        .footer {{ text-align: center; margin-top: 15px; border-top: 2px dashed #000; padding-top: 10px; font-size: 11px; }}
        @media print {{ body {{ padding: 0; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{business}</h1>
        <div>REPORTE DE VENTAS</div>
        <div>{s} — {e}</div>
        <div>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
    <div class="section-title">VENTAS</div>
    {sales_rows_html}
    <div class="section-title">FLUJO DE CAJA</div>
    {cash_rows_html}
    <div class="totals">
        <div class="total-row"><span>Ventas Totales:</span><span>{tv}</span></div>
        <div class="total-row"><span>Entradas:</span><span>{te}</span></div>
        <div class="total-row"><span>Salidas:</span><span>{ts}</span></div>
        <div class="total-row grand"><span>TOTAL NETO:</span><span>{tn}</span></div>
    </div>
    <div class="footer">AYL-POS · Generado automáticamente</div>
</body>
</html>"""

        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
            tmp.write(html)
            tmp.close()
            webbrowser.open(f"file://{os.path.realpath(tmp.name)}")
            self._show_snack("Reporte HTML abierto en el navegador.")
        except Exception as ex:
            self._show_snack(f"Error al exportar: {ex}", error=True)

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _show_snack(self, message: str, error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _go_back(self):
        if self.on_back:
            self.on_back()
