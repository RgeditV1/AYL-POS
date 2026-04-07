import os
import subprocess
import sys
import platform

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

    # 4. Configuración Base del Comando
    cmd = [
        py, "-m", "nuitka",
        "--onefile",
        "--output-dir=dist",
        "--output-filename=AYL-POS",
        "--follow-imports",
        "--include-data-dir=data=data",
        "--include-data-files=src/logo.png=src/logo.png",
        "--include-data-files=src/logo.ico=src/logo.ico",
        "--include-package-data=escpos",
        "--include-package-data=flet",
        "src/main.py"
    ]

    # 5. Añadir Flags Específicos por Sistema Operativo
    if es_windows:
        print("[!] Aplicando optimizaciones para Windows...")
        cmd.extend([
            "--windows-console-mode=disable",
            "--windows-company-name=AYL-Software",
            "--windows-product-name=AYL-POS",
            "--windows-file-description=Sistema de Punto de Venta",
            "--windows-product-version=0.9.0",
            "--windows-file-version=2026.4.7.0",
            "--windows-copyright=Copyright (c) 2026 AYL-Software",
            "--windows-icon-from-ico=src/logo.ico",
            "--include-module=win32print",
        ])
    
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
