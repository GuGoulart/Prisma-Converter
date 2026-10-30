"""Fila, cancelamento, autodestruição e histórico."""
import io
import os
import time

import pytest

from core import config, settings
from core.jobs import jobs
from core.processo import Controle, TempoEsgotado, executar
from core.tarefas import executar_tarefa
from tests.conftest import aguardar, arquivo, postar


@pytest.fixture(autouse=True)
def _politica_padrao():
    yield
    settings.definir_politica_retencao("15min")


def test_download_unico_entrega_o_conteudo_e_depois_apaga(cliente, amostras):
    settings.definir_politica_retencao("instant")
    st = aguardar(cliente, postar(cliente, "/api/file/criptografar", arquivo=arquivo(amostras, "t.csv"), senha="x"))
    job = jobs.obter(st["job_id"])
    caminho = job.caminho_saida
    com_conteudo = open(caminho, "rb").read()

    r = cliente.get(st["download_url"])
    corpo = r.get_data()
    r.close()
    assert corpo == com_conteudo and corpo.count(0) != len(corpo)
    assert not os.path.exists(caminho)
    assert cliente.get(st["download_url"]).status_code == 410


def test_falhas_nao_prendem_vagas(cliente, amostras):
    """Antes, 5 conversões sem download bloqueavam o app até reiniciar."""
    for _ in range(12):
        aguardar(cliente, postar(cliente, "/api/inverter", arquivo=(io.BytesIO(b"\xff\xfbruim"), "r.mp3")))
    st = aguardar(cliente, postar(cliente, "/api/inverter", arquivo=arquivo(amostras, "a.mp3")))
    assert st["erro"] is None


def test_varias_ferramentas_seguidas_sem_limite_artificial(cliente):
    for _ in range(15):
        assert postar(cliente, "/api/qr/gerar", texto="a").status_code == 202


def test_entradas_e_saidas_de_falha_nao_ficam_em_disco(cliente):
    antes = set(os.listdir(config.DOWNLOAD_DIR)), set(os.listdir(config.UPLOAD_DIR))
    st = aguardar(cliente, postar(cliente, "/api/inverter", arquivo=(io.BytesIO(b"\xff\xfbruim"), "r.mp3")))
    assert st["status"] == "erro"
    assert set(os.listdir(config.DOWNLOAD_DIR)) == antes[0]
    assert set(os.listdir(config.UPLOAD_DIR)) == antes[1]


def test_cancelar_encerra_o_processo():
    import sys
    controle = Controle()
    inicio = time.time()
    from threading import Timer
    Timer(0.3, controle.cancelar).start()
    from core.errors import JobCancelado
    with pytest.raises(JobCancelado):
        executar([sys.executable, "-c", "import time; time.sleep(60)"], controle)
    assert time.time() - inicio < 10


def test_limite_de_tempo_encerra_o_processo():
    import sys
    with pytest.raises(TempoEsgotado):
        executar([sys.executable, "-c", "import time; time.sleep(60)"], timeout=0.3)


def test_cancelar_job_pela_api(cliente):
    job = jobs.criar(nome_download="x")
    def trabalho(_j):
        import sys
        executar([sys.executable, "-c", "import time; time.sleep(60)"], job.controle)
    jobs.submeter(job, trabalho)
    time.sleep(0.5)
    r = cliente.post(f"/api/jobs/{job.id}/cancelar", headers={"X-CSRFToken": cliente.token})
    assert r.get_json()["ok"] is True
    fim = time.time() + 15
    while job.status != "cancelado" and time.time() < fim:
        time.sleep(0.05)
    assert job.status == "cancelado"


def test_worker_traduz_erro_e_mantem_mensagem_do_usuario():
    from core.errors import ErroUsuario
    with pytest.raises(ErroUsuario, match="Nenhum QR Code"):
        import tempfile
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "vazio.png")
            Image.new("RGB", (50, 50)).save(p)
            executar_tarefa("qr.ler", p)


def test_historico_mostra_e_expira(cliente, amostras):
    st = aguardar(cliente, postar(cliente, "/api/qr/gerar", texto="a"))
    pagina = cliente.get("/historico").get_data(as_text=True)
    assert "historico-card" in pagina and st["job_id"] in pagina and st["download_url"] in pagina

    job = jobs.obter(st["job_id"])
    caminho = job.caminho_saida
    jobs.limpar_expirados(agora=time.time() + 901)
    assert job.apagado and not os.path.exists(caminho)
    assert cliente.get(st["download_url"]).status_code == 410


def test_renovar_e_destruir(cliente):
    st = aguardar(cliente, postar(cliente, "/api/qr/gerar", texto="a"))
    h = {"X-CSRFToken": cliente.token}
    r = cliente.post(f"/api/historico/renovar/{st['job_id']}", headers=h)
    assert r.status_code == 200 and r.get_json()["expira_em"] > time.time()
    z = cliente.get("/api/historico/zip-todos")
    assert z.status_code == 200 and z.get_data()[:2] == b"PK"
    z.close()
    assert cliente.post("/api/historico/destruir-tudo", headers=h).get_json()["destruidos"] >= 1
    assert cliente.post(f"/api/historico/renovar/{st['job_id']}", headers=h).status_code == 410
    assert cliente.get("/api/historico/zip-todos").status_code == 404


def test_preferencia_de_retencao_persiste(cliente):
    h = {"X-CSRFToken": cliente.token}
    assert cliente.post("/api/historico/set-politica", json={"politica": "5min"}, headers=h).get_json()["politica"] == "5min"
    assert settings.politica_retencao() == "5min"
    st = aguardar(cliente, postar(cliente, "/api/qr/gerar", texto="a"))
    assert jobs.obter(st["job_id"]).politica == "5min"
    assert 'data-retention-policy="5min"' in cliente.get("/historico").get_data(as_text=True)


def test_limpeza_de_uploads_respeita_jobs_ativos(tmp_path):
    velha = config.UPLOAD_DIR / "velha"
    velha.mkdir(parents=True, exist_ok=True)
    (velha / "x").write_text("x")
    os.utime(velha, (1, 1))
    ativa = config.UPLOAD_DIR / "ativa"
    ativa.mkdir(exist_ok=True)
    os.utime(ativa, (1, 1))
    job = jobs.criar(pasta_entrada=str(ativa))
    jobs.limpar_uploads_antigos()
    assert not velha.exists() and ativa.exists()
    job.status = "cancelado"
    ativa.rmdir()
