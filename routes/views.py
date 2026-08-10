import os
import time
from flask import Blueprint, render_template, redirect, url_for, send_file, jsonify

views_bp = Blueprint("views", __name__)


@views_bp.route("/health")
@views_bp.route("/ping")
def health_check():
    """Endpoint leve para o Render verificar se o serviço está respondendo."""
    return jsonify({"status": "ok", "service": "prisma-converter", "timestamp": time.time()}), 200


@views_bp.route('/favicon.ico')
def favicon():
    return "", 204


@views_bp.route("/")
def home():
    return render_template("home.html")


@views_bp.route("/conversor")
def conversor_page():
    return render_template("index.html")


@views_bp.route("/ferramentas-pdf")
def redirect_ferramentas():
    return redirect(url_for("views.ferramentas_pdf_page"))


@views_bp.route("/ferramentas-avancadas")
def ferramentas_pdf_page():
    return render_template("pdf_tools.html")


@views_bp.route("/historico")
def historico_page():
    return render_template("historico.html")


@views_bp.route("/modificar-arquivos")
def modificar_arquivos_page():
    return redirect(url_for("views.ferramentas_pdf_page") + "#modificar")


@views_bp.route("/manifest.json")
def serve_manifest():
    return send_file("static/manifest.json", mimetype="application/manifest+json")


@views_bp.route("/sw.js")
def serve_sw():
    return send_file("static/sw.js", mimetype="application/javascript")


@views_bp.route("/download-apk")
def download_apk():
    possiveis_apk = [
        os.path.join("dist", "Prisma.apk"),
        os.path.join("static", "Prisma.apk"),
        "Prisma.apk"
    ]
    for apk_path in possiveis_apk:
        if os.path.exists(apk_path):
            return send_file(
                apk_path,
                as_attachment=True,
                download_name="Prisma.apk",
                mimetype="application/vnd.android.package-archive"
            )

    github_apk_url = os.environ.get(
        "GITHUB_APK_URL",
        "https://github.com/GuGoulart/Prisma-Converter/releases/latest/download/Prisma.apk"
    )
    return redirect(github_apk_url)
