from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Producto, Ingreso, Salida, DetalleSalida
from sqlalchemy import func, desc
from app import db

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
@login_required
def dashboard():
    productos_total = Producto.query.count()
    stock_total = db.session.query(func.sum(Producto.stock)).scalar() or 0
    productos_bajo_stock = Producto.query.filter(Producto.stock <= Producto.stock_minimo).count()
    productos_sin_stock = Producto.query.filter_by(stock=0).count()
    ultimo_ingreso = db.session.query(func.max(Ingreso.fecha_ingreso)).scalar()

    # Activos vs inactivos
    activos = Producto.query.filter_by(activo=True).count()
    inactivos = Producto.query.filter_by(activo=False).count()

    # Top 5 productos más usados (por salidas registradas en detalle_salida)
    top_usados = (
        db.session.query(
            Producto.nombre,
            func.sum(DetalleSalida.cantidad).label("total_usado")
        )
        .join(DetalleSalida.producto)
        .group_by(Producto.id_producto)
        .order_by(desc("total_usado"))
        .limit(5)
        .all()
    )

    return render_template(
        'home.html',
        productos_total=productos_total,
        stock_total=stock_total,
        productos_bajo_stock=productos_bajo_stock,
        productos_sin_stock=productos_sin_stock,
        ultimo_ingreso=ultimo_ingreso.strftime('%d/%m/%Y') if ultimo_ingreso else "Sin registros",
        activos=activos,
        inactivos=inactivos,
        top_usados=top_usados
    )
