from flask import Blueprint

productos_bp = Blueprint('productos', __name__, url_prefix='/productos')

@productos_bp.route('/test')
def test_productos():
    return "Blueprint de productos funcionando"
