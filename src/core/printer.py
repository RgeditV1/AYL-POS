import platform
import subprocess
import sys
import tempfile
import os
import usb.core
import usb.util
from src.utils.resources import is_frozen_app

try:
    from escpos.printer import Usb, Win32Raw
    from escpos import exceptions as escpos_exceptions
except ModuleNotFoundError:
    Usb = None
    Win32Raw = None
    escpos_exceptions = None


class PrinterDetector:
    def __init__(self):
        self.PRINTER_CLASS = 0x07

    def _is_printer(self, dev):
        for cfg in dev:
            interface = usb.util.find_descriptor(cfg, bInterfaceClass=self.PRINTER_CLASS)
            if interface is not None:
                return True
        return False

    def get_available_printers(self):
        printers = []
        devices = usb.core.find(find_all=True)
        for dev in devices:
            try:
                if self._is_printer(dev):
                    manufacturer = usb.util.get_string(dev, dev.iManufacturer)
                    product = usb.util.get_string(dev, dev.iProduct)
                    printers.append({
                        "name": f"{manufacturer} {product}",
                        "vid": dev.idVendor,
                        "pid": dev.idProduct,
                        "device": dev,
                    })
            except Exception:
                printers.append({
                    "name": f"Unknown Printer ({hex(dev.idVendor)}:{hex(dev.idProduct)})",
                    "vid": dev.idVendor,
                    "pid": dev.idProduct,
                    "device": dev,
                })
        return printers

    def _connect_device(self, target):
        if Usb is None:
            return None
        try:
            interface_number = None
            out_ep = None
            for cfg in target["device"]:
                interface = usb.util.find_descriptor(cfg, bInterfaceClass=self.PRINTER_CLASS)
                if interface is None:
                    continue
                interface_number = interface.bInterfaceNumber
                out_ep = usb.util.find_descriptor(
                    interface,
                    custom_match=lambda e: usb.util.endpoint_direction(
                        e.bEndpointAddress
                    )
                    == usb.util.ENDPOINT_OUT,
                )
                if out_ep is not None:
                    break

            if interface_number is not None and out_ep is not None:
                return Usb(
                    target["vid"],
                    target["pid"],
                    interface=interface_number,
                    out_ep=out_ep.bEndpointAddress,
                )

            return Usb(target["vid"], target["pid"])
        except Exception:
            return None

    def connect_by_vid_pid(self, vid, pid):
        printers = self.get_available_printers()
        for p in printers:
            if p["vid"] == vid and p["pid"] == pid:
                return self._connect_device(p)
        return None


class PrinterManager:
    def __init__(self, settings):
        self.settings = settings or {}
        self.detector = PrinterDetector()

    def _selected_vid_pid(self):
        vid = self.settings.get("printer_vid")
        pid = self.settings.get("printer_pid")
        if vid in (None, "") or pid in (None, ""):
            return None
        try:
            return int(vid), int(pid)
        except Exception:
            return None

    def has_valid_printer(self):
        selected = self._selected_vid_pid()
        if not selected:
            return False
        vid, pid = selected
        for p in self.detector.get_available_printers():
            if p["vid"] == vid and p["pid"] == pid:
                return True
        return False

    def _connect_selected(self):
        selected = self._selected_vid_pid()
        if not selected:
            return None
        vid, pid = selected
        printer = self.detector.connect_by_vid_pid(vid, pid)
        if printer:
            return printer
        if platform.system() == "Windows" and Win32Raw:
            name = self.settings.get("printer_name")
            if name:
                return Win32Raw(name)
        return None

    def _print_direct(self, text):
        if Usb is None:
            return False, "Falta la dependencia 'python-escpos'."
        printer = self._connect_selected()
        if not printer:
            return False, "No hay impresora válida conectada."
        try:
            printer.text(text)
            printer.cut()
            return True, "Impresión enviada."
        except escpos_exceptions.DeviceNotFoundError as e:
            msg = str(e).lower()
            if "access denied" in msg or "insufficient permissions" in msg or "errno 13" in msg:
                return False, "Permisos insuficientes para acceder a la impresora USB."
            return False, f"Error de impresión: {e}"
        except Exception as e:
            return False, f"Error de impresión: {e}"

    def _print_with_sudo(self, text, sudo_password):
        if not sudo_password:
            return False, "Se requiere contraseña sudo para imprimir."
        selected = self._selected_vid_pid()
        if not selected:
            return False, "No hay impresora válida configurada."
        vid, pid = selected

        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
            f.write(text)
            tmp_path = f.name

        exe_path = os.path.realpath(sys.argv[0])
        if not os.path.isabs(exe_path):
            exe_path = os.path.abspath(exe_path)

        cmd = ["sudo", "-S", "-k", sys.executable]
        if is_frozen_app():
            cmd = ["sudo", "-S", "-k", exe_path]
            cmd.extend(
                [
                    "--print-file",
                    tmp_path,
                    "--vid",
                    str(vid),
                    "--pid",
                    str(pid),
                ]
            )
        else:
            cmd.extend(
                [
                    "-m",
                    "src.core.printer",
                    "--print-file",
                    tmp_path,
                    "--vid",
                    str(vid),
                    "--pid",
                    str(pid),
                ]
            )
        name = self.settings.get("printer_name")
        if name:
            cmd.extend(["--win32-name", name])

        try:
            proc = subprocess.run(
                cmd,
                input=(sudo_password + "\n").encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            return False, "No se encontró el comando sudo en este sistema."

        if proc.returncode != 0:
            return False, proc.stderr.decode().strip() or "No se pudo imprimir con sudo."

        return True, "Impresión enviada con sudo."

    def print_text(self, text, sudo_password=None, bypass_sudo=False):
        if platform.system() == "Linux" and self.settings.get("require_sudo_print") and not bypass_sudo:
            return self._print_with_sudo(text, sudo_password)
        return self._print_direct(text)


def _cli_print_from_file():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--print-file", required=True)
    parser.add_argument("--vid", required=False)
    parser.add_argument("--pid", required=False)
    parser.add_argument("--win32-name", required=False, default="")
    args = parser.parse_args()

    settings = {
        "printer_vid": args.vid or "",
        "printer_pid": args.pid or "",
        "printer_name": args.win32_name or "",
        "require_sudo_print": False,
    }

    try:
        with open(args.print_file, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"No se pudo leer el ticket: {e}")
        sys.exit(1)

    ok, msg = PrinterManager(settings).print_text(text, bypass_sudo=True)
    if not ok:
        print(msg)
        sys.exit(1)


if __name__ == "__main__":
    if "--print-file" in sys.argv:
        _cli_print_from_file()
