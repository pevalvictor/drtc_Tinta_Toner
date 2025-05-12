from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Ingreso, Producto, TipoProducto
from app import db
from datetime import datetime

ingresos_bp = Blueprint('ingresos', __name__, url_prefix='/ingresos')

@ingresos_bp.route('/dashboard')
@login_required
def dashboard():
    ingresos = Ingreso.query.order_by(Ingreso.fecha_ingreso.desc()).all()
    tipos_productos = TipoProducto.query.all()
    return render_template('ingresos_dashboard.html', ingresos=ingresos, tipos_productos=tipos_productos)

@ingresos_bp.route('/registrar_ajax', methods=['POST'])
@login_required
def nuevo_ingreso_ajax():
    try:
        data = request.form
        id_tipo = data.get('id_tipo')
        id_producto = data.get('id_producto')
        cantidad = data.get('cantidad')
        responsable = data.get('responsable')
        observaciones = data.get('observaciones')

        ingreso = Ingreso(
            id_tipo=id_tipo,
            id_producto=id_producto,
            cantidad=cantidad,
            responsable=responsable,
            observaciones=observaciones,
            id_usuario=current_user.id_usuario
        )
        db.session.add(ingreso)

        producto = Producto.query.get(id_producto)
        if producto:
            producto.stock += int(cantidad)

        db.session.commit()

        return jsonify({
            'status': 'success',
            'mensaje': 'Ingreso registrado correctamente',
            'nuevo': {
                'id_ingreso': ingreso.id_ingreso,
                'producto': producto.nombre,
                'cantidad': ingreso.cantidad,
                'fecha_ingreso': ingreso.fecha_ingreso.strftime('%d/%m/%Y'),
                'responsable': ingreso.responsable or '-',
                'observaciones': ingreso.observaciones or '-'
            }
        })

    except Exception as e:
        db.session.rollback()
        print("Error en nuevo_ingreso_ajax:", e)
        return jsonify({'status': 'error', 'mensaje': 'Error al registrar ingreso'}), 500


@ingresos_bp.route('/api/productos_por_tipo/<int:id_tipo>')
@login_required
def productos_por_tipo(id_tipo):
    productos = Producto.query.filter_by(id_tipo=id_tipo).all()
    data = [{"id_producto": p.id_producto, "nombre": p.nombre} for p in productos]
    return jsonify(data)
