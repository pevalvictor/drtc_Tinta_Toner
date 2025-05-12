from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Producto, Ingreso, Salida
from sqlalchemy import func, and_
from app import db

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

@reportes_bp.route('/general')  # ← usa reportes_bp
@login_required
def dashboard():
    productos = Producto.query.all()
    return render_template('reportes_dashboard.html', productos=productos)

@reportes_bp.route('/alertas')
@login_required
def alertas_stock():
    productos_alerta = Producto.query.filter(
        and_(
            Producto.stock.isnot(None),
            Producto.stock_minimo.isnot(None),
            Producto.stock <= Producto.stock_minimo
        )
    ).all()

    return render_template('reportes_alertas.html', productos=productos_alerta)

@reportes_bp.route('/kpis')
@login_required
def kpis():
    productos = Producto.query.all()

    total_productos = len(productos)
    productos_alerta = sum(
        1 for p in productos
        if p.stock is not None and p.stock_minimo is not None and p.stock <= p.stock_minimo
    )
    productos_normales = total_productos - productos_alerta
    stock_total = sum(p.stock for p in productos if p.stock is not None)

    return render_template('reportes_kpis.html', 
                           total_productos=total_productos,
                           productos_alerta=productos_alerta,
                           productos_normales=productos_normales,
                           stock_total=stock_total)

@reportes_bp.route('/consolidado')
@login_required
def consolidado():
    productos = Producto.query.all()

    consolidado_data = []

    for producto in productos:
        total_ingresos = db.session.query(func.sum(Ingreso.cantidad)).filter_by(id_producto=producto.id_producto).scalar() or 0
        total_salidas = db.session.query(func.sum(Salida.cantidad)).filter_by(id_producto=producto.id_producto).scalar() or 0
        stock_inicial = (producto.stock or 0) + total_salidas - total_ingresos

        consolidado_data.append({
            'id_producto': producto.id_producto,
            'nombre': producto.nombre,
            'tipo': producto.tipo,
            'marca': producto.marca,
            'modelo_impresora': producto.modelo_impresora,
            'color': producto.color,
            'unidad': producto.unidad,
            'stock_inicial': stock_inicial,
            'total_ingresos': total_ingresos,
            'total_salidas': total_salidas,
            'stock_actual': producto.stock or 0
        })

    return render_template('reportes_consolidado.html', consolidado=consolidado_data)
