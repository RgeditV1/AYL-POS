import os
import subprocess
import sys
import platform
import urllib.request
import ssl

def ensure_flet_client_downloaded(es_windows: bool):
    if not es_windows:
        return
    try:
        import flet_desktop
        import certifi
    except Exception:
        print("[!] No se pudo importar flet_desktop/certifi para descargar el cliente.")
        return

    file_name = "flet-windows.zip"
    version = flet_desktop.version.version
    default_url = f"https://github.com/flet-dev/flet/releases/download/v{version}/{file_name}"
    flet_url = os.environ.get("FLET_CLIENT_URL", default_url)

    target_dir = os.path.join(os.getcwd(), "flet_client")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, file_name)
    if os.path.exists(target_path):
        print(f"[+] Cliente Flet ya existe: {target_path}")
        return

    print(f"[+] Descargando cliente Flet v{version} desde {flet_url}")
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(flet_url, context=ctx) as r, open(target_path, "wb") as f:
        f.write(r.read())
    print(f"[+] Cliente Flet guardado en: {target_path}")

def main():
    # 1. Identificar el sistema operativo actual
    sistema = platform.system() # Retorna 'Windows', 'Linux' o 'Darwin'
    es_windows = sistema == "Windows"
    es_linux = sistema == "Linux"

    if not es_windows and not es_linux:
        print(f"Sistema {sistema} no soportado para este build.")
        sys.exit(1)

    # 2. Verificar/Instalar Nuitka
    try:
        subprocess.run([sys.executable, "-m", "nuitka", "--version"], 
                       check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"Nuitka no detectado en {sistema}. Instalando...")
        try:
            # Intentar con uv primero (ideal para tu entorno Arch)
            subprocess.run(["uv", "pip", "install", "nuitka"], check=True)
        except Exception:
            subprocess.run([sys.executable, "-m", "pip", "install", "nuitka"], check=True)

    # 3. Determinar el ejecutable de Python del entorno virtual
    if es_windows:
        venv_python = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
    else: # Linux/Arch
        venv_python = os.path.join(os.getcwd(), ".venv", "bin", "python3")
        
    py = venv_python if os.path.exists(venv_python) else sys.executable
    print(f"[+] Operando en: {sistema}")
    print(f"[+] Intérprete de build: {py}")

    # 3.5 Descarga el cliente Flet para incluirlo en el bundle (Windows)
    ensure_flet_client_downloaded(es_windows)

    # 4. Configuración Base del Comando
    exe_name = "AYL-POS-debug" if "--enable-console" in sys.argv else "AYL-POS"
    cmd = [
        py, "-m", "nuitka",
        "--standalone", # Cambiado de --onefile a --standalone
        "--output-dir=dist",
        f"--output-filename={exe_name}",
        "--follow-imports",
        "--assume-yes-for-downloads", # Evita prompts en entornos CI/CD
        "--include-data-files=src/logo.png=src/logo.png",
        "--include-data-files=src/logo.ico=src/logo.ico",
        "--include-package-data=escpos",
        "--include-package-data=flet",
        "--include-package-data=certifi",
        "src/main.py"
    ]

    # Incluir cliente de Flet predescargado si existe
    flet_client_dir = os.path.join(os.getcwd(), "flet_client")
    if os.path.isdir(flet_client_dir):
        cmd.append("--include-data-dir=flet_client=flet_client")

    # 5. Añadir Flags Específicos por Sistema Operativo
    if es_windows:
        print("[!] Aplicando optimizaciones para Windows...")
        windows_flags = [
            "--company-name=AYL-Software",
            "--product-name=AYL-POS",
            "--file-description=Sistema de Punto de Venta",
            "--product-version=1.0.3",
            "--file-version=2026.04.13.0",
            "--copyright=Copyright (c) 2026 AYL-Software",
            "--windows-icon-from-ico=src/logo.ico",
            "--include-module=win32print",
        ]
        if "--enable-console" in sys.argv:
            windows_flags.append("--windows-console-mode=force")
        else:
            windows_flags.append("--windows-console-mode=disable")
            
        cmd.extend(windows_flags)
    
    elif es_linux:
        print("[!] Aplicando configuraciones para Linux (Arch/Otros)...")
        # pero podrías añadir flags de optimización de performance
        #cmd.append("--lto=yes") # Link Time Optimization (más lento el build, más rápido el binario)

    # 6. Ejecución
    print("\n" + "="*40)
    print(f"INICIANDO COMPILACIÓN EN {sistema.upper()}")
    print("="*40)
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[SUCCESS] Binario AYL-POS creado en 'dist/AYL-POS.exe' (Windows) o 'dist/AYL-POS.bin' (Linux)")
    except subprocess.CalledProcessError as exc:
        print(f"\n[ERROR] Falló el build en {sistema}: {exc}")
        sys.exit(exc.returncode)

if __name__ == "__main__":
    main()
