import os
import time
import shutil
import threading
import logging

log = logging.getLogger(__name__)

def limpar_residuos_loop(upload_folder, download_folder):
    limite = 15 * 60
    while True:
        time.sleep(300)  # PERF-005: verifica a cada 5 min (era 15 min)
        agora = time.time()
        for pasta in [upload_folder, download_folder]:
            if not os.path.exists(pasta):
                continue
            for item in os.listdir(pasta):
                c = os.path.join(pasta, item)
                try:
                    if agora - os.path.getmtime(c) > limite:
                        if os.path.isdir(c):
                            shutil.rmtree(c, ignore_errors=True)
                        else:
                            os.remove(c)
                except Exception as e:
                    log.warning(f"Erro ao limpar {c}: {e}")

def iniciar_limpeza(upload_folder, download_folder):
    t = threading.Thread(target=limpar_residuos_loop, args=(upload_folder, download_folder), daemon=True)
    t.start()
