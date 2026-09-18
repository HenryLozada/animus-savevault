"""
Script automatizado para compilar la aplicación a un ejecutable independiente (.exe)
utilizando PyInstaller.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def build():
    print("==================================================")
    print(" Compilando Animus SaveVault a Ejecutable (.exe)")
    print("==================================================")

    dist_dir = BASE_DIR / "dist"
    build_dir = BASE_DIR / "build"

    # Preparar comando PyInstaller
    # En Windows, el separador para --add-data es ';'
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",             # Modo carpeta para carga ultrarrápida y estabilidad
        "--windowed",           # Sin ventana de consola negra
        "--name", "AnimusSaveVault",
        "--add-data", f"{BASE_DIR / 'gui'};gui",
        "--add-data", f"{BASE_DIR / 'core'};core",
        str(BASE_DIR / "main.py")
    ]

    # Si existe carpeta data, incluirla
    data_dir = BASE_DIR / "data"
    if data_dir.exists():
        cmd.insert(-1, "--add-data")
        cmd.insert(-1, f"{data_dir};data")

    print(f"Ejecutando: {' '.join(cmd)}\n")
    res = subprocess.run(cmd, cwd=str(BASE_DIR))
    if res.returncode == 0:
        exe_path = dist_dir / "AnimusSaveVault" / "AnimusSaveVault.exe"
        print("\n==================================================")
        print(" ¡COMPILACIÓN EXITOSA!")
        print(f" Ejecutable generado en: {exe_path}")
        print("==================================================")
    else:
        print("\nError durante la compilación con PyInstaller.")

if __name__ == "__main__":
    build()
