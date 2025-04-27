from flask import Blueprint

salidas_bp = Blueprint('salidas', __name__, url_prefix='/salidas')

# Ruta temporal para validar el blueprint
@salidas_bp.route('/test')
def test_salidas():
    return "Blueprint de salidas funcionando"
