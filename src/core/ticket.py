from datetime import datetime


DEFAULT_WIDTH = 32


def _pad_center(text: str, width: int) -> str:
    if len(text) >= width:
        return text[:width]
    left = (width - len(text)) // 2
    right = width - len(text) - left
    return " " * left + text + " " * right


def _pad_lr(left: str, right: str, width: int) -> str:
    space = width - len(left) - len(right)
    if space < 1:
        return left[: width - len(right) - 1] + " " + right
    return left + " " * space + right


def format_money(amount: float) -> str:
    return f"${amount:.2f}"


def build_ticket_text(settings, items, total, cashier, ticket_id, cash_received=None, change=None):
    width = DEFAULT_WIDTH
    now = datetime.now()

    lines = []
    business = settings.get("business_name", "")
    address = settings.get("address", "")
    phone = settings.get("phone", "")

    if business:
        lines.append(_pad_center(business.upper(), width))
    if address:
        lines.append(_pad_center(address, width))
    if phone:
        lines.append(_pad_center(phone, width))

    lines.append("-" * width)
    lines.append(_pad_lr("Fecha:", now.strftime("%Y-%m-%d %H:%M"), width))
    lines.append(_pad_lr("Cajero:", cashier or "-", width))
    lines.append(_pad_lr("Ticket:", ticket_id, width))
    lines.append("-" * width)

    for _, item in items.items():
        name = str(item.get("nombre", ""))[: width]
        qty = item.get("qty", 0)
        price = item.get("precio", 0.0)
        subtotal = qty * price
        lines.append(name)
        lines.append(_pad_lr(f"{qty} x {format_money(price)}", format_money(subtotal), width))

    lines.append("-" * width)
    lines.append(_pad_lr("TOTAL", format_money(total), width))

    if cash_received is not None:
        try:
            cash_val = float(cash_received)
            lines.append(_pad_lr("Efectivo", format_money(cash_val), width))
            if change is not None:
                lines.append(_pad_lr("Cambio", format_money(change), width))
        except Exception:
            pass

    lines.append("-" * width)
    lines.append(_pad_center("Gracias por su compra", width))
    lines.append("\n\n")
    return "\n".join(lines)


def build_report_text(settings, start_date, end_date, totals):
    width = DEFAULT_WIDTH
    lines = []
    business = settings.get("business_name", "")
    if business:
        lines.append(_pad_center(business.upper(), width))
    lines.append(_pad_center("REPORTE DE VENTAS", width))
    lines.append("-" * width)
    if start_date == end_date:
        lines.append(_pad_lr("Fecha:", start_date.strftime("%Y-%m-%d"), width))
    else:
        lines.append(_pad_lr("Desde:", start_date.strftime("%Y-%m-%d"), width))
        lines.append(_pad_lr("Hasta:", end_date.strftime("%Y-%m-%d"), width))
    lines.append("-" * width)
    lines.append(_pad_lr("Ventas", format_money(totals.get("sales", 0.0)), width))
    lines.append(_pad_lr("Entradas", format_money(totals.get("entries", 0.0)), width))
    lines.append(_pad_lr("Salidas", format_money(totals.get("exits", 0.0)), width))
    lines.append("-" * width)
    lines.append(_pad_lr("NETO", format_money(totals.get("net", 0.0)), width))
    lines.append("\n\n")
    return "\n".join(lines)
