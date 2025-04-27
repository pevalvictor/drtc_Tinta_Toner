from flask import Blueprint

ingresos_bp = Blueprint('ingresos', __name__, url_prefix='/ingresos')

# Ruta temporal para validar el blueprint
@ingresos_bp.route('/test')
def test_ingresos():
    return "Blueprint de ingresos funcionando"
