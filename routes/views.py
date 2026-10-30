"""routes/views.py — Páginas do aplicativo."""
from flask import Blueprint, jsonify, redirect, render_template, url_for

from core import settings
from core.jobs import jobs
from core.security import gerar_csrf

views_bp = Blueprint("views", __name__)


@views_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "prisma-converter"})


@views_bp.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="favicon.svg"))


@views_bp.route("/")
def home():
    return render_template("home.html")


@views_bp.route("/conversor")
def conversor_page():
    return render_template("index.html")


@views_bp.route("/ferramentas-pdf")
@views_bp.route("/modificar-arquivos")
def redirect_ferramentas():
    return redirect(url_for("views.ferramentas_page"))


@views_bp.route("/ferramentas-avancadas")
def ferramentas_page():
    return render_template("pdf_tools.html")


@views_bp.route("/audio")
@views_bp.route("/ferramentas-audio")
def audio_page():
    return render_template("audio.html")


@views_bp.route("/video")
@views_bp.route("/ferramentas-video")
def video_page():
    return render_template("video.html")


@views_bp.route("/historico")
def historico_page():
    return render_template("historico.html", historico=jobs.historico(), retencao_padrao=settings.politica_retencao())


def injetar_globais() -> dict:
    return {"csrf_token": gerar_csrf(), "retencao_padrao": settings.politica_retencao()}
