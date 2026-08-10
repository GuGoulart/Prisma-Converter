"""
Pacote de rotas da aplicação Prisma Converter (organização por Flask Blueprints).
"""

from routes.views import views_bp
from routes.converter import converter_bp
from routes.pdf import pdf_bp
from routes.file_tools import file_tools_bp
from routes.tools import tools_bp
from routes.history import history_bp


def registrar_blueprints(app):
    """Registra todos os Blueprints no aplicativo Flask principal."""
    app.register_blueprint(views_bp)
    app.register_blueprint(converter_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(file_tools_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(history_bp)
