from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Salida, Producto
from datetime import datetime, date

from flask import send_file
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas





salidas_bp = Blueprint('salidas', __name__, url_prefix='/salidas')

@salidas_bp.route('/dashboard')
@login_required
def dashboard():
    buscar = request.args.get("buscar", "").strip()
    fecha_ini = request.args.get("fechaInicio")
    fecha_fin = request.args.get("fechaFin")

    salidas = Salida.query.join(Producto).order_by(Salida.fecha_salida.desc())

    if buscar:
        salidas = salidas.filter(
            Producto.nombre.ilike(f"%{buscar}%") |
            Salida.destino.ilike(f"%{buscar}%") |
            Salida.responsable.ilike(f"%{buscar}%")
        )
    if fecha_ini:
        try:
            salidas = salidas.filter(Salida.fecha_salida >= datetime.strptime(fecha_ini, "%Y-%m-%d").date())
        except: pass
    if fecha_fin:
        try:
            salidas = salidas.filter(Salida.fecha_salida <= datetime.strptime(fecha_fin, "%Y-%m-%d").date())
        except: pass

    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('salidas_dashboard.html', salidas=salidas.all(), productos=productos, current_date=current_date, tabla_activa='salidas')

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

@salidas_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_salida(id):
    try:
        salida = Salida.query.get_or_404(id)
        producto = Producto.query.get(salida.id_producto)
        if producto:
            producto.stock += salida.cantidad
        db.session.delete(salida)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@salidas_bp.route('/productos/info/<int:id>')
@login_required
def info_producto(id):
    producto = Producto.query.get_or_404(id)
    return jsonify({
        "nombre": producto.nombre,
        "tipo": producto.tipo_producto.nombre_tipo if producto.tipo_producto else "",
        "marca": producto.marca,
        "color": producto.color,
        "unidad": producto.unidad,
        "stock": producto.stock
    })

@salidas_bp.route('/<int:id>/json')
@login_required
def obtener_salida(id):
    salida = Salida.query.get_or_404(id)
    return jsonify({
        "id_salida": salida.id_salida,
        "producto": salida.producto.nombre,
        "cantidad": salida.cantidad,
        "fecha_salida": salida.fecha_salida.strftime('%Y-%m-%d'),
        "destino": salida.destino,
        "responsable": salida.responsable,
        "observaciones": salida.observaciones or ""
    })


@salidas_bp.route('/<int:id>/editar', methods=['POST'])
@login_required
def editar_salida(id):
    try:
        salida = Salida.query.get_or_404(id)
        producto = Producto.query.get_or_404(salida.id_producto)

        nueva_cantidad = int(request.form['cantidad'])
        diferencia = nueva_cantidad - salida.cantidad

        if producto.stock - diferencia < 0:
            return jsonify({'success': False, 'message': 'Stock insuficiente para este cambio.'})

        salida.cantidad = nueva_cantidad
        salida.fecha_salida = datetime.strptime(request.form['fecha_salida'], '%Y-%m-%d')
        salida.destino = request.form['destino']
        salida.responsable = request.form['responsable']
        salida.observaciones = request.form['observaciones']

        producto.stock -= diferencia

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


