"""Comportamento do processo real: encerramento automático, instância única e porta ocupada."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _iniciar(porta: int, dados: Path, **env) -> subprocess.Popen:
    ambiente = {**os.environ, "PORT": str(porta), "NO_BROWSER": "1", "PRISMA_DATA_DIR": str(dados), **env}
    ambiente.pop("SECRET_KEY", None)
    return subprocess.Popen([sys.executable, "app.py"], cwd=RAIZ, env=ambiente,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _encerrar(proc: subprocess.Popen) -> None:
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)


def _health(porta: int) -> dict | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/health", timeout=2) as r:
            return json.load(r)
    except OSError:
        return None


def _aguardar_no_ar(porta: int) -> None:
    fim = time.time() + 30
    while time.time() < fim:
        if _health(porta):
            return
        time.sleep(0.2)
    raise AssertionError("o servidor não subiu")


def test_encerra_quando_a_janela_fecha(tmp_path):
    porta = _porta_livre()
    proc = _iniciar(porta, tmp_path, PRISMA_SHUTDOWN_SECONDS="6")
    try:
        _aguardar_no_ar(porta)
        # Sem nenhum sinal recebido ainda, o servidor espera a primeira janela abrir.
        time.sleep(8)
        assert proc.poll() is None, "não pode encerrar antes de a janela abrir"
        # Em um venv do Windows, proc.pid é o lançador; o servidor real é um processo filho.
        assert (tmp_path / "instance" / "prisma.pid").read_text().strip().isdigit()

        pedido = urllib.request.Request(f"http://127.0.0.1:{porta}/api/heartbeat", method="POST")
        urllib.request.urlopen(pedido, timeout=2).close()
        assert proc.wait(timeout=30) == 0
        assert not (tmp_path / "instance" / "prisma.pid").exists()
    finally:
        _encerrar(proc)


def test_segunda_instancia_nao_sobe_outro_servidor(tmp_path):
    porta = _porta_livre()
    primeira = _iniciar(porta, tmp_path, NO_AUTO_SHUTDOWN="1")
    try:
        _aguardar_no_ar(porta)
        segunda = _iniciar(porta, tmp_path)
        assert segunda.wait(timeout=30) == 0
        assert primeira.poll() is None and _health(porta)
    finally:
        _encerrar(primeira)


def test_porta_ocupada_por_outro_programa(tmp_path):
    with socket.socket() as ocupada:
        ocupada.bind(("127.0.0.1", 0))
        ocupada.listen()
        porta = ocupada.getsockname()[1]
        proc = _iniciar(porta, tmp_path, NO_AUTO_SHUTDOWN="1")
        try:
            # Em vez de abrir o outro programa, o Prisma sobe em outra porta.
            time.sleep(6)
            assert proc.poll() is None
        finally:
            _encerrar(proc)


def test_chave_gerada_nao_e_a_antiga_e_persiste(tmp_path):
    porta = _porta_livre()
    proc = _iniciar(porta, tmp_path, NO_AUTO_SHUTDOWN="1")
    try:
        _aguardar_no_ar(porta)
        chave = (tmp_path / "instance" / "secret_key").read_text()
        assert len(chave) == 64 and "prisma_converter" not in chave
    finally:
        _encerrar(proc)
