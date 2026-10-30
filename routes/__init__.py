"""Blueprints da aplicação."""
from routes.audio import audio_bp
from routes.converter import converter_bp
from routes.file_tools import file_tools_bp
from routes.history import history_bp
from routes.jobs import jobs_bp
from routes.pdf import pdf_bp
from routes.tools import tools_bp
from routes.video import video_bp
from routes.views import views_bp


def registrar_blueprints(app):
    for bp in (views_bp, converter_bp, jobs_bp, pdf_bp, file_tools_bp, tools_bp, history_bp, audio_bp, video_bp):
        app.register_blueprint(bp)
