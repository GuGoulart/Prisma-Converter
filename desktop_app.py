"""
desktop_app.py - Ponto de Entrada do Aplicativo Desktop Nativo
Prisma Converter - PyInstaller + PyWebview + Waitress WSGI
"""

import os
import sys

# Define flag indicando que estamos rodando dentro do aplicativo Desktop nativo
os.environ["PRISMA_DESKTOP"] = "1"

import socket
import threading
import logging

# Se estiver rodando empacotado como executavel (.exe pelo PyInstaller)
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    os.chdir(bundle_dir)
    sys.path.insert(0, bundle_dir)

from app import app
from waitress import serve
import webview

# Desativa logs verbosos do Waitress no console do app
logging.getLogger('waitress').setLevel(logging.ERROR)

def encontrar_porta_livre():
    """Encontra uma porta TCP local disponivel dinamicamente."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def iniciar_servidor_wsgi(porta):
    """Inicia o servidor WSGI Waitress local em segundo plano."""
    try:
        serve(app, host='127.0.0.1', port=porta, threads=6, _quiet=True)
    except Exception as e:
        print(f"Erro ao iniciar servidor WSGI local: {e}")

def main():
    porta = encontrar_porta_livre()
    url_local = f"http://127.0.0.1:{porta}"

    # Inicia o servidor backend Flask local em uma thread daemon
    t = threading.Thread(target=iniciar_servidor_wsgi, args=(porta,), daemon=True)
    t.start()

    ico_path = os.path.abspath("static/logo.ico")

    # Inicia a janela do aplicativo nativo de desktop usando PyWebview
    webview.create_window(
        title='Prisma - Conversor de Arquivos',
        url=url_local,
        width=1280,
        height=820,
        min_size=(900, 600),
        resizable=True,
        text_select=True,
        confirm_close=False
    )

    # Inicia o loop de eventos da janela GUI
    webview.start(debug=False)

if __name__ == '__main__':
    main()
