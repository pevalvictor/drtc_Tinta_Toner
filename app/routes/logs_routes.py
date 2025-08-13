from flask import Blueprint

logs_bp = Blueprint('logs', __name__, url_prefix='/logs')

@logs_bp.route('/registrar')  
def test_reportes():
    return "Blueprint de logs funcionando"
