from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Salida, Producto
from datetime import datetime

salidas_bp = Blueprint('salidas', __name__, url_prefix='/salidas')

@salidas_bp.route('/dashboard')
@login_required
def dashboard():
    salidas = Salida.query.order_by(Salida.fecha_salida.desc()).all()
    productos = Producto.query.filter_by(activo=True).all()
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('salidas_dashboard.html', salidas=salidas, productos=productos, current_date=current_date)

@salidas_bp.route('/registrar_ajax', methods=['POST'])
@login_required
def registrar_salida():
    try:
        data = request.form
        id_producto = int(data.get('id_producto'))
        cantidad = int(data.get('cantidad'))
        producto = Producto.query.get_or_404(id_producto)

        if cantidad > producto.stock:
            return jsonify({'success': False, 'message': 'Stock insuficiente para realizar la salida.'})

        salida = Salida(
            id_producto=id_producto,
            cantidad=cantidad,
            fecha_salida=datetime.strptime(data.get('fecha_salida'), '%Y-%m-%d'),
            destino=data.get('destino'),
            responsable=data.get('responsable'),
            observaciones=data.get('observaciones'),
            id_usuario=current_user.id_usuario
        )

        producto.stock -= cantidad
        db.session.add(salida)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
