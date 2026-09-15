"""
routes/views_audio.py — Blueprint para as páginas de interface do Prisma Audio.

Rotas:
  GET /audio  — Página principal de ferramentas de áudio
  GET /video  — Página de ferramentas de vídeo
"""
from flask import Blueprint, render_template
from core.security import gerar_csrf

views_audio_bp = Blueprint("views_audio", __name__)


@views_audio_bp.route("/audio")
@views_audio_bp.route("/ferramentas-audio")
def pagina_audio():
    """Renderiza a interface de ferramentas de áudio."""
    return render_template("audio.html", csrf_token=gerar_csrf())


@views_audio_bp.route("/video")
@views_audio_bp.route("/ferramentas-video")
def pagina_video():
    """Renderiza a interface de ferramentas de vídeo."""
    return render_template("video.html", csrf_token=gerar_csrf())
