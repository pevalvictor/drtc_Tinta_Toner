from flask import Blueprint

logs_bp = Blueprint('logs', __name__, url_prefix='/logs')

# Ruta temporal para validar el blueprint
@logs_bp.route('/test')
def test_reportes():
    return "Blueprint de logos funcionando"
