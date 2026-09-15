"""
routes/video.py — Blueprint com todos os endpoints de processamento e download de vídeo.

Ferramentas:
  POST /api/video/mp4-para-mp3  — Conversor de MP4 para MP3
  POST /api/video/mp4-para-gif  — Conversor de MP4 para GIF
  POST /api/video/converter     — Conversor de Formatos de Vídeo
  POST /api/video/compressor    — Compressor de Vídeo
  POST /api/video/remover-audio — Silenciar Vídeo
  POST /api/video/capturar-foto — Snapshot de Vídeo
  POST /api/video/baixar-link   — Downloader de vídeos por link (YouTube, Twitter, Instagram)
  POST /api/video/duracao       — Duração de vídeo para preview
"""
import os
import uuid
import time
import logging

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from core.security import (
    validar_csrf, validar_extensao_video, obter_extensao, rate_limit_required
)
from core.video_processor import (
    converter_mp4_para_mp3, converter_mp4_para_gif, obter_duracao_video,
    converter_formato_video, compressor_video, remover_audio_video, capturar_foto_video,
    FORMATOS_VIDEO_SUPORTADOS, BITRATES_MP3
)
from core.video_downloader import baixar_video_por_link, obter_progresso_download
from core.utils import (
    caminho_upload, caminho_download, formatar_tamanho, erro_seguro,
    registrar_saida_historico
)

log = logging.getLogger(__name__)
video_bp = Blueprint("video", __name__)

MAX_VIDEO_MB = 200
MAX_VIDEO_BYTES = MAX_VIDEO_MB * 1024 * 1024


def _salvar_upload_video(arquivo_flask, prefixo: str = "vid_") -> tuple[str, str, str]:
    """Salva upload de vídeo e valida a extensão e o tamanho."""
    if not arquivo_flask or not arquivo_flask.filename:
        raise ValueError("Nenhum arquivo enviado.")

    nome_original = secure_filename(arquivo_flask.filename)
    ext = obter_extensao(nome_original)

    if not ext or not validar_extensao_video(nome_original):
        raise ValueError(
            f"Formato '{ext.upper() or 'desconhecido'}' não suportado. "
            f"Use: {', '.join(f.upper() for f in FORMATOS_VIDEO_SUPORTADOS)}"
        )

    arquivo_flask.seek(0, 2)
    tam = arquivo_flask.tell()
    arquivo_flask.seek(0)

    if tam > MAX_VIDEO_BYTES:
        raise ValueError(f"Arquivo muito grande ({formatar_tamanho(tam)}). Limite: {MAX_VIDEO_MB} MB.")

    nome_salvo = f"{prefixo}{uuid.uuid4().hex}.{ext}"
    caminho = caminho_upload(nome_salvo)
    arquivo_flask.save(caminho)
    log.info(f"[upload_video] {nome_original} -> {caminho} ({formatar_tamanho(tam)})")
    return caminho, nome_original, ext


def _resposta_sucesso(caminho_saida: str, nome_download: str, job_id: str = None) -> dict:
    """Monta a resposta padrão do Prisma com link de download."""
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


# ─── ROTA: Duração do Vídeo ──────────────────────────────────────────────────

@video_bp.route("/api/video/duracao", methods=["POST"])
def api_video_duracao():
    """Retorna a duração do vídeo enviado."""
    caminho = None
    try:
        arquivo = request.files.get("arquivo")
        caminho, nome, ext = _salvar_upload_video(arquivo, "vdur_")
        duracao = obter_duracao_video(caminho)
        return jsonify({
            "ok": True,
            "duracao_s": duracao,
        })
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[video_duracao] Erro")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho and os.path.exists(caminho):
            try:
                os.remove(caminho)
            except Exception:
                pass


# ─── ROTA 1: MP4 para MP3 ────────────────────────────────────────────────────

@video_bp.route("/api/video/mp4-para-mp3", methods=["POST"])
@rate_limit_required(20)
def api_mp4_para_mp3():
    """Extrai áudio MP3 de um arquivo de vídeo."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload_video(arquivo, "v2a_")
        sz_orig = os.path.getsize(caminho_in)

        bitrate = request.form.get("bitrate", "192k").strip().lower()
        if bitrate not in BITRATES_MP3:
            bitrate = "192k"

        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"{nome_base}.mp3"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = converter_mp4_para_mp3(caminho_in, caminho_out, bitrate)
        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro na extração do áudio."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt="MP3",
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[mp4_para_mp3] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 2: MP4 para GIF ────────────────────────────────────────────────────

@video_bp.route("/api/video/mp4-para-gif", methods=["POST"])
@rate_limit_required(15)
def api_mp4_para_gif():
    """Gera animação GIF a partir de um vídeo."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload_video(arquivo, "v2g_")
        sz_orig = os.path.getsize(caminho_in)

        try:
            inicio = float(request.form.get("inicio", "0"))
            duracao = float(request.form.get("duracao", "5"))
            fps = int(request.form.get("fps", "10"))
            largura = int(request.form.get("largura", "480"))
        except ValueError:
            return jsonify({"erro": "Parâmetros de GIF inválidos."}), 400

        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"{nome_base}.gif"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = converter_mp4_para_gif(caminho_in, caminho_out, inicio, duracao, fps, largura)
        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro na geração do GIF."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt="GIF",
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[mp4_para_gif] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 3: Conversor de Formatos de Vídeo ──────────────────────────────────

@video_bp.route("/api/video/converter", methods=["POST"])
@rate_limit_required(15)
def api_converter_formato_video():
    """Converte entre formatos de vídeo (MP4, MKV, WebM, AVI, MOV)."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload_video(arquivo, "vconv_")
        sz_orig = os.path.getsize(caminho_in)

        formato_saida = request.form.get("formato", "mp4").strip().lower()
        if formato_saida not in FORMATOS_VIDEO_SUPORTADOS:
            formato_saida = "mp4"

        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"{nome_base}_converted.{formato_saida}"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = converter_formato_video(caminho_in, caminho_out, formato_saida)
        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro na conversão de formato."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=formato_saida.upper(),
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[converter_formato] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 4: Compressor de Vídeo ─────────────────────────────────────────────

@video_bp.route("/api/video/compressor", methods=["POST"])
@rate_limit_required(20)
def api_compressor_video():
    """Reduz o tamanho de arquivos de vídeo."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload_video(arquivo, "vcomp_")
        sz_orig = os.path.getsize(caminho_in)

        nivel = request.form.get("nivel", "medio").strip().lower()
        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"{nome_base}_compressed.mp4"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = compressor_video(caminho_in, caminho_out, nivel)
        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro na compressão de vídeo."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=f"MP4 ({nivel.upper()})",
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[compressor_video] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 5: Remover Áudio do Vídeo ──────────────────────────────────────────

@video_bp.route("/api/video/remover-audio", methods=["POST"])
@rate_limit_required(20)
def api_remover_audio():
    """Silencia o vídeo removendo a trilha de áudio."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload_video(arquivo, "vmute_")
        sz_orig = os.path.getsize(caminho_in)

        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"{nome_base}_muted.{ext_in}"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = remover_audio_video(caminho_in, caminho_out)
        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro ao silenciar vídeo."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=f"{ext_in} (MUTE)",
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[remover_audio] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA 6: Capturar Foto do Vídeo ──────────────────────────────────────────

@video_bp.route("/api/video/capturar-foto", methods=["POST"])
@rate_limit_required(25)
def api_capturar_foto():
    """Extrai uma imagem PNG/JPG do vídeo em um determinado segundo."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    caminho_in = None
    try:
        arquivo = request.files.get("arquivo")
        caminho_in, nome_orig, ext_in = _salvar_upload_video(arquivo, "vsnap_")
        sz_orig = os.path.getsize(caminho_in)

        tempo = float(request.form.get("tempo", "1.0"))
        formato_img = request.form.get("formato", "png").strip().lower()
        if formato_img not in ["png", "jpg", "jpeg"]:
            formato_img = "png"

        nome_base = os.path.splitext(nome_orig)[0]
        nome_dl = f"{nome_base}_snapshot.{formato_img}"
        nome_disco = f"{uuid.uuid4().hex}_{secure_filename(nome_dl)}"
        caminho_out = caminho_download(nome_disco)

        ok, err = capturar_foto_video(caminho_in, caminho_out, tempo)
        if not ok:
            return jsonify({"erro": erro_seguro(err) or "Erro ao capturar imagem do vídeo."}), 500

        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_disco,
            origem_fmt=ext_in,
            destino_fmt=formato_img.upper(),
            tamanho_orig=sz_orig
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_disco, job_id))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        log.exception("[capturar_foto] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
    finally:
        if caminho_in and os.path.exists(caminho_in):
            try:
                os.remove(caminho_in)
            except Exception:
                pass


# ─── ROTA: Progresso do Download em Tempo Real ───────────────────────────────

@video_bp.route("/api/video/progresso/<task_id>", methods=["GET"])
def api_video_progresso(task_id: str):
    """Retorna o progresso em porcentagem real de um download em andamento."""
    return jsonify(obter_progresso_download(task_id))


# ─── ROTA 7: Baixar Vídeos por Link ──────────────────────────────────────────

@video_bp.route("/api/video/baixar-link", methods=["POST"])
@rate_limit_required(10)
def api_baixar_link():
    """Baixa vídeo de plataformas como YouTube, Twitter/X, Instagram por URL."""
    if not validar_csrf():
        return jsonify({"erro": "Token de segurança inválido."}), 403

    try:
        url = request.form.get("url", "").strip()
        formato = request.form.get("formato", "mp4").strip().lower()
        qualidade = request.form.get("qualidade", "best").strip().lower()
        task_id = request.form.get("task_id", "").strip()

        if not url:
            return jsonify({"erro": "Insira a URL do vídeo."}), 400

        ok, err, caminho_out, titulo = baixar_video_por_link(url, formato, qualidade, task_id=task_id)

        if not ok:
            return jsonify({"erro": err or "Não foi possível baixar o vídeo."}), 400

        nome_download = os.path.basename(caminho_out)
        job_id = registrar_saida_historico(
            saida_path=caminho_out,
            nome_download=nome_download,
            origem_fmt="URL",
            destino_fmt=formato.upper()
        )

        return jsonify(_resposta_sucesso(caminho_out, nome_download, job_id))

    except Exception as e:
        log.exception("[baixar_link] Erro inesperado")
        return jsonify({"erro": erro_seguro(str(e))}), 500
