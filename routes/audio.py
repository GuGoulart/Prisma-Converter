"""
routes/audio.py — Blueprint com todos os endpoints de processamento de áudio.

Ferramentas:
  POST /api/converter   — Conversor Universal
  POST /api/cortar      — Audio Cutter
  POST /api/juntar      — Audio Joiner
  POST /api/volume      — Volume Booster / Normalizer
  POST /api/velocidade  — Speed Changer
  POST /api/inverter    — Audio Reverser
  POST /api/transcrever — Transcritor de Áudio
  GET  /download/<nome> — Download do arquivo processado
"""
import os
import uuid
import time
import logging

from flask import Blueprint, request, jsonify, send_file, after_this_request, session
from werkzeug.utils import secure_filename

from core.security import (
    validar_csrf, validar_extensao_audio, obter_extensao, rate_limit_required
)
from core.audio_processor import (
    converter_audio, cortar_audio, parse_tempo,
    juntar_audios, ajustar_volume, alterar_velocidade,
    inverter_audio, transcrever_audio, obter_duracao, formatar_duracao,
    FORMATOS_SUPORTADOS, BITRATES_SUPORTADOS, VELOCIDADE_MIN, VELOCIDADE_MAX
)
from core.utils import (
    gerar_nome_unico, formatar_tamanho,
    caminho_upload, caminho_download, erro_seguro,
    registrar_saida_historico,
    UPLOAD_FOLDER, DOWNLOAD_FOLDER
)
from core.storage import storage

log = logging.getLogger(__name__)
audio_bp = Blueprint("audio", __name__)

MAX_ARQUIVO_MB = 200
MAX_ARQUIVO_BYTES = MAX_ARQUIVO_MB * 1024 * 1024


def _salvar_upload(arquivo_flask, prefixo: str = "") -> tuple[str, str, str]:
    """
    Salva arquivo de upload e retorna (caminho, nome_original, extensao).
    Lança ValueError se inválido.
    """
    if not arquivo_flask or not arquivo_flask.filename:
        raise ValueError("Nenhum arquivo enviado.")

    nome_original = secure_filename(arquivo_flask.filename)
    ext = obter_extensao(nome_original)

    if not ext or not validar_extensao_audio(nome_original):
        raise ValueError(
            f"Formato '{ext.upper() or 'desconhecido'}' não suportado. "
            f"Use: {', '.join(f.upper() for f in FORMATOS_SUPORTADOS)}"
        )

    arquivo_flask.seek(0, 2)
    tam = arquivo_flask.tell()
    arquivo_flask.seek(0)
    if tam > MAX_ARQUIVO_BYTES:
        raise ValueError(f"Arquivo muito grande ({formatar_tamanho(tam)}). Limite: {MAX_ARQUIVO_MB} MB.")

    nome_salvo = f"{prefixo}{uuid.uuid4().hex}.{ext}"
    caminho = caminho_upload(nome_salvo)
    arquivo_flask.save(caminho)
    log.info(f"[upload] {nome_original} -> {caminho} ({formatar_tamanho(tam)})")
    return caminho, nome_original, ext


def _resposta_sucesso(caminho_saida: str, nome_download: str, job_id: str = None) -> dict:
    """Monta resposta JSON de sucesso com info do arquivo e job_id."""
    tam = os.path.getsize(caminho_saida) if os.path.exists(caminho_saida) else 0
    resp = {
        "ok": True,
        "nome_download": nome_download,
        "url_download": f"/download/{nome_download}",
        "tamanho": formatar_tamanho(tam),
    }
    if job_id:
        resp["job_id"] = job_id
    return resp


# ─── ROTA: Download ──────────────────────────────────────────────────────────

@audio_bp.route("/download/<nome_arquivo>")
def download_arquivo(nome_arquivo: str):
    """Serve o arquivo processado para download respeitando a política de retenção."""
    nome_seguro = secure_filename(nome_arquivo)
    caminho = caminho_download(nome_seguro)

    if not os.path.exists(caminho):
        caminho_direto = os.path.join(DOWNLOAD_FOLDER, nome_arquivo)
        if os.path.exists(caminho_direto):
            caminho = caminho_direto
        else:
            prefixo = nome_arquivo.split('_')[0] if '_' in nome_arquivo else nome_arquivo
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f == nome_arquivo or f.startswith(prefixo):
                    caminho = os.path.join(DOWNLOAD_FOLDER, f)
                    break

    if not os.path.exists(caminho):
        log.warning(f"[download] Arquivo não encontrado: {nome_arquivo} (caminho: {caminho})")
        return jsonify({"erro": "Arquivo não encontrado ou expirado."}), 404

    caminho_final = caminho

    # Verifica se a política é 'instant' para apagar após o download
    historico = session.get("historico", [])
    item_hist = None
    for h in historico:
        if h.get("nome") == nome_arquivo or (h.get("caminho_saida") and os.path.basename(h["caminho_saida"]) == nome_arquivo):
            item_hist = h
            break

    politica = item_hist.get("autodestruicao") if item_hist else session.get("prisma_retention_policy", "15min")
    if politica == "instant":
        if item_hist:
            item_hist["apagado"] = True
            session.modified = True

        @after_this_request
        def remover_apos_download(response):
            try:
                time.sleep(2)
                storage.remover(caminho_final, modo_seguro=session.get("prisma_secure_wipe", True))
                log.info(f"[download] Removido com Zero-Fill após download único: {caminho_final}")
            except Exception as e:
                log.warning(f"[download] Erro ao remover {caminho_final}: {e}")
            return response

    return send_file(
        caminho_final,
        as_attachment=True,
        download_name=secure_filename(nome_arquivo),
    )


# ─── ROTA: Duração ───────────────────────────────────────────────────────────

@audio_bp.route("/api/duracao", methods=["POST"])
def api_duracao():
    """Retorna duração do áudio enviado (para o Audio Cutter)."""
    try:
        arquivo = request.files.get("arquivo")
        caminho, nome, ext = _salvar_upload(arquivo, "dur_")
        duracao = obter_duracao(caminho)
        try:
            os.remove(caminho)
        except Exception:
            pass
        return jsonify({
            "ok": True,
            "duracao_s": duracao,
            "duracao_fmt": formatar_duracao(duracao)
        })
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[duracao] Erro")
        return jsonify({"erro": erro_seguro(str(e))}), 500


# ─── ROTA 1: Conversor Universal ─────────────────────────────────────────────

@audio_bp.route("/api/converter", methods=["POST"])
@rate_limit_required(20)
def api_converter():
    """Converte áudio entre formatos com escolha de bitrate."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload(arquivo, "conv_")
        sz_orig = os.path.getsize(caminho_in)

        formato_saida = request.form.get("formato", "mp3").strip().lower()
        bitrate = request.form.get("bitrate", "192k").strip().lower()
        canais = request.form.get("canais", "stereo").strip().lower()
        sample_rate = request.form.get("sample_rate", "44100").strip().lower()

        if formato_saida not in FORMATOS_SUPORTADOS:
            formato_saida = "mp3"
        if bitrate not in BITRATES_SUPORTADOS:
            bitrate = "192k"

        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"{nome_base}.{formato_saida}"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = converter_audio(
            caminho_in, caminho_out, formato_saida, bitrate,
            canais=canais, sample_rate=sample_rate
        )

        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro na conversão do áudio."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=formato_saida,
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[converter] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 2: Audio Cutter ───────────────────────────────────────────────────

@audio_bp.route("/api/cortar", methods=["POST"])
@rate_limit_required(20)
def api_cortar():
    """Corta trecho do áudio dado início e fim."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload(arquivo, "cut_")
        sz_orig = os.path.getsize(caminho_in)

        inicio_str = request.form.get("inicio", "0").strip()
        fim_str = request.form.get("fim", "").strip()

        inicio_s = parse_tempo(inicio_str)
        fim_s = parse_tempo(fim_str) if fim_str else None

        if fim_s is not None and fim_s <= inicio_s:
            return jsonify({"erro": "O tempo final deve ser maior que o tempo inicial."}), 400

        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"{nome_base}_cortado.{ext_in}"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = cortar_audio(caminho_in, caminho_out, inicio_s, fim_s)

        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro ao cortar o áudio."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=f"{ext_in} (CORTE)",
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[cortar] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 3: Audio Joiner ───────────────────────────────────────────────────

@audio_bp.route("/api/juntar", methods=["POST"])
@rate_limit_required(15)
def api_juntar():
    """Junta múltiplos arquivos de áudio em um único."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminhos_salvos = []
    try:
        arquivos = request.files.getlist("arquivos")
        if not arquivos or len(arquivos) < 2:
            return jsonify({"erro": "Envie pelo menos 2 arquivos de áudio para juntar."}), 400

        if len(arquivos) > 20:
            return jsonify({"erro": "Máximo de 20 arquivos por operação."}), 400

        for arq in arquivos:
            c, n, e = _salvar_upload(arq, "join_")
            caminhos_salvos.append(c)

        formato_saida = request.form.get("formato", "mp3").strip().lower()
        bitrate = request.form.get("bitrate", "192k").strip().lower()

        if formato_saida not in FORMATOS_SUPORTADOS:
            formato_saida = "mp3"

        nome_dl = f"prisma_juntados_{len(arquivos)}faixas.{formato_saida}"
        nome_disco = f"{uuid.uuid4().hex}_{nome_dl}"
        caminho_out = caminho_download(nome_disco)

        ok, err = juntar_audios(caminhos_salvos, caminho_out, formato_saida, bitrate)

        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro ao juntar os áudios."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=f"{len(arquivos)} FAIXAS",
            destino_fmt=formato_saida
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[juntar] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        for c in caminhos_salvos:
            try:
                if os.path.exists(c):
                    os.remove(c)
            except Exception:
                pass


# ─── ROTA 4: Volume Booster ─────────────────────────────────────────────────

@audio_bp.route("/api/volume", methods=["POST"])
@rate_limit_required(20)
def api_volume():
    """Aumenta/diminui o volume ou normaliza o áudio."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload(arquivo, "vol_")
        sz_orig = os.path.getsize(caminho_in)

        ajuste = request.form.get("ajuste", "+6").strip()

        nome_base = os.path.splitext(nome_orig)[0]
        sufixo = "norm" if ajuste == "normalizar" else ajuste.replace("+", "mais").replace("-", "menos") + "dB"
        nome_dl = f"{nome_base}_{sufixo}.{ext_in}"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = ajustar_volume(caminho_in, caminho_out, ajuste)

        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro ao ajustar o volume."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=f"{ext_in} (VOL)",
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[volume] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 5: Speed Changer ───────────────────────────────────────────────────

@audio_bp.route("/api/velocidade", methods=["POST"])
@rate_limit_required(20)
def api_velocidade():
    """Altera a velocidade do áudio sem mudar o pitch."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload(arquivo, "spd_")
        sz_orig = os.path.getsize(caminho_in)

        try:
            fator = float(request.form.get("fator", "1.5"))
        except ValueError:
            return jsonify({"erro": "Fator de velocidade inválido."}), 400

        if not (VELOCIDADE_MIN <= fator <= VELOCIDADE_MAX):
            return jsonify({"erro": f"Fator deve estar entre {VELOCIDADE_MIN}x e {VELOCIDADE_MAX}x."}), 400

        nome_base = os.path.splitext(nome_orig)[0]
        fator_str = f"{fator:.1f}x".replace(".", "_")
        nome_dl = f"{nome_base}_{fator_str}.{ext_in}"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = alterar_velocidade(caminho_in, caminho_out, fator)

        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro ao alterar a velocidade."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=f"{ext_in} ({fator:.1f}x)",
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[velocidade] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 6: Audio Reverser ─────────────────────────────────────────────────

@audio_bp.route("/api/inverter", methods=["POST"])
@rate_limit_required(20)
def api_inverter():
    """Inverte o áudio (toca de trás para frente)."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload(arquivo, "rev_")
        sz_orig = os.path.getsize(caminho_in)

        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"{nome_base}_reversed.{ext_in}"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = inverter_audio(caminho_in, caminho_out)

        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro ao inverter o áudio."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=f"{ext_in} (REVERSE)",
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[inverter] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 7: Transcritor de Áudio (Speech-to-Text) ──────────────────────────

@audio_bp.route("/api/transcrever", methods=["POST"])
@rate_limit_required(20)
def route_transcrever():
    """Converte o áudio em texto escrito, legendas (.srt) ou JSON (.json)."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload(arquivo, "trns_")
        sz_orig = os.path.getsize(caminho_in)

        idioma = request.form.get("idioma", "auto").strip()
        formato = request.form.get("formato", "txt").strip().lower()
        modelo_ia = request.form.get("modelo", "small").strip().lower()

        if formato not in ["txt", "srt", "json"]:
            formato = "txt"

        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"transcricao_{nome_base}.{formato}"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err, texto = transcrever_audio(caminho_in, caminho_out, idioma, formato, modelo_ia)

        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro ao transcrever o áudio."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=formato.upper(),
            tamanho_orig=sz_orig
        )

        resp = _resposta_sucesso(caminho_out, nome_disco, job_id)
        resp["texto"] = texto
        resp["formato"] = formato
        return jsonify(resp)

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[transcrever] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass
