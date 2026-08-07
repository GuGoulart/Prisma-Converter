import os
import time
import shutil
import threading
import logging

log = logging.getLogger(__name__)

# Tempo de retenção dos arquivos temporários (15 minutos)
_LIMITE_SEGUNDOS = 15 * 60

# Intervalo entre cada varredura de limpeza (5 minutos)
_INTERVALO_VARREDURA = 300


def _remover_item_seguro(caminho: str):
    """Zera os bytes de um arquivo ou pasta antes de deletar fisicamente do disco."""
    try:
        if os.path.isfile(caminho):
            sz = os.path.getsize(caminho)
            with open(caminho, "r+b") as f:
                f.write(b"\x00" * sz)
                f.flush()
                os.fsync(f.fileno())
            os.remove(caminho)
        elif os.path.isdir(caminho):
            for root, _, files in os.walk(caminho, topdown=False):
                for file_name in files:
                    fp = os.path.join(root, file_name)
                    try:
                        sz = os.path.getsize(fp)
                        with open(fp, "r+b") as f:
                            f.write(b"\x00" * sz)
                            f.flush()
                            os.fsync(f.fileno())
                        os.remove(fp)
                    except Exception:
                        pass
            shutil.rmtree(caminho, ignore_errors=True)
    except Exception:
        if os.path.exists(caminho):
            if os.path.isdir(caminho):
                shutil.rmtree(caminho, ignore_errors=True)
            else:
                os.remove(caminho)


def _limpar_pasta(pasta: str, agora: float, limite: float):
    """Apaga arquivos e diretórios mais antigos que `limite` segundos em `pasta` com Zero-Fill seguro."""
    if not os.path.exists(pasta):
        return
    for item in os.listdir(pasta):
        caminho = os.path.join(pasta, item)
        try:
            if agora - os.path.getmtime(caminho) > limite:
                _remover_item_seguro(caminho)
                log.debug(f"[cleanup] Removido com Zero-Fill: {caminho}")
        except Exception as e:
            log.warning(f"[cleanup] Erro ao remover {caminho}: {e}")


def limpar_orphans_inicializacao(upload_folder: str, download_folder: str):
    """
    Limpeza única de arquivos órfãos na inicialização do servidor.
    Remove arquivos que sobreviveram a uma reinicialização inesperada
    (ex: crash durante processamento, deploy sem graceful shutdown).

    Esta função é executada uma única vez no startup e não bloqueia
    o início do servidor — é executada em thread daemon.
    """
    def _run():
        try:
            agora = time.time()
            log.info("[cleanup] Limpeza de inicialização: removendo arquivos órfãos...")
            _limpar_pasta(upload_folder, agora, _LIMITE_SEGUNDOS)
            _limpar_pasta(download_folder, agora, _LIMITE_SEGUNDOS)
            log.info("[cleanup] Limpeza de inicialização concluída.")
        except Exception as e:
            log.warning(f"[cleanup] Erro na limpeza de inicialização: {e}")

    threading.Thread(target=_run, daemon=True).start()


def limpar_residuos_loop(upload_folder: str, download_folder: str):
    """
    Loop de limpeza periódica (a cada 5 minutos).
    Remove arquivos com mais de 15 minutos de `upload_folder` e `download_folder`.

    NOTA ARQUITETURAL: Em ambientes com múltiplas réplicas (Render escalonado),
    cada instância limpa apenas os seus próprios arquivos. Para compartilhamento
    de estado entre instâncias, configure um Render Disk persistente ou Redis.
    """
    while True:
        time.sleep(_INTERVALO_VARREDURA)
        agora = time.time()
        _limpar_pasta(upload_folder, agora, _LIMITE_SEGUNDOS)
        _limpar_pasta(download_folder, agora, _LIMITE_SEGUNDOS)


def iniciar_limpeza(upload_folder: str, download_folder: str):
    """Inicializa o sistema de limpeza: limpeza imediata de órfãos + loop periódico."""
    # 1. Limpeza única de arquivos que sobreviveram ao restart anterior
    limpar_orphans_inicializacao(upload_folder, download_folder)

    # 2. Loop de limpeza periódica
    t = threading.Thread(
        target=limpar_residuos_loop,
        args=(upload_folder, download_folder),
        daemon=True
    )
    t.start()
