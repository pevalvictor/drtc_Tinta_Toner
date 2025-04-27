from flask import Blueprint

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

# Ruta temporal para validar el blueprint
@reportes_bp.route('/test')
def test_reportes():
    return "Blueprint de reportes funcionando"
