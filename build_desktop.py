"""
build_desktop.py - Script de Compilação do Prisma Converter para Executável Windows (.exe)
Empacota a aplicação em um arquivo standalone 'dist/Prisma.exe' com o ícone oficial.
"""

import os
import sys
import subprocess

def main():
    print("=" * 60)
    print("  Prisma Converter -- Compilador de Executavel Desktop (.exe)")
    print("=" * 60)

    # 1. Garante que pyinstaller, pywebview e waitress estejam instalados
    print("\nInstalacao/Verificacao de dependencias de build...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pywebview", "waitress", "pillow"])

    # 2. Gera/Verifica o icone .ico do aplicativo
    ico_path = os.path.abspath("static/logo.ico")
    if not os.path.exists(ico_path) and os.path.exists("static/icon-512.png"):
        try:
            from PIL import Image
            img = Image.open("static/icon-512.png")
            img.save(ico_path, format="ICO", sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
        except Exception as e:
            print(f"Aviso ao gerar logo.ico: {e}")

    # 3. Monta o comando do PyInstaller (--onefile para arquivo unico executavel)
    is_win = sys.platform.startswith("win")
    sep = ";" if is_win else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=Prisma",
        f"--icon={ico_path}" if os.path.exists(ico_path) else None,
        f"--add-data=templates{sep}templates",
        f"--add-data=static{sep}static",
        f"--add-data=core{sep}core",
        "desktop_app.py"
    ]
    cmd = [c for c in cmd if c is not None]

    print("\nCompilando o executavel standalone com PyInstaller...")
    print(f"Executando: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = os.path.abspath("dist/Prisma.exe" if is_win else "dist/Prisma")
        print("\n" + "=" * 60)
        print("COMPILACAO CONCLUIDA COM SUCESSO!")
        print("=" * 60)
        print(f"Executavel Standalone: {exe_path}")
        print("\nO arquivo 'Prisma.exe' eh 100% independente e pode ser movido para qualquer pasta!")
    else:
        print("\nHouve um erro durante a compilacao com PyInstaller.")

if __name__ == '__main__':
    main()
