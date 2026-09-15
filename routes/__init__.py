"""
Pacote de rotas da aplicação Prisma Converter (organização por Flask Blueprints).
"""

from routes.views import views_bp
from routes.converter import converter_bp
from routes.pdf import pdf_bp
from routes.file_tools import file_tools_bp
from routes.tools import tools_bp
from routes.history import history_bp
from routes.audio import audio_bp
from routes.video import video_bp
from routes.views_audio import views_audio_bp


def registrar_blueprints(app):
    """Registra todos os Blueprints no aplicativo Flask principal."""
    app.register_blueprint(views_bp)
    app.register_blueprint(converter_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(file_tools_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(views_audio_bp)
