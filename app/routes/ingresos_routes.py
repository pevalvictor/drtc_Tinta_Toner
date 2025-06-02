from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Ingreso, Producto, TipoProducto
from app import db
from datetime import datetime

ingresos_bp = Blueprint('ingresos', __name__, url_prefix='/ingresos')


def get_safe_int(value, default=0):
    try:
        return int(value)
    except:
        return default

def get_safe_float(value, default=0.0):
    try:
        return float(value)
    except:
        return default


@ingresos_bp.route('/dashboard')
@login_required
def dashboard():
    ingresos = Ingreso.query.order_by(Ingreso.fecha_ingreso.desc()).all()
    tipos_productos = TipoProducto.query.all()
    return render_template('ingresos_dashboard.html', ingresos=ingresos, tipos_productos=tipos_productos)


@ingresos_bp.route('/obtener/<int:id_ingreso>')
@login_required
def obtener_ingreso(id_ingreso):
    ingreso = Ingreso.query.get_or_404(id_ingreso)
    return jsonify({
        'tipo_producto': ingreso.tipo_producto,
        'marca': ingreso.marca,
        'modelo': ingreso.modelo,
        'color': ingreso.color,
        'cantidad': ingreso.cantidad,
        'unidad': ingreso.unidad,
        'precio': ingreso.precio,
        'fecha_ingreso': ingreso.fecha_ingreso.strftime('%Y-%m-%d'),
        'stock': ingreso.stock,
        'stock_minimo': ingreso.stock_minimo,
        'responsable': ingreso.responsable,
        'observaciones': ingreso.observaciones
    })


@ingresos_bp.route('/editar/<int:id_ingreso>', methods=['POST'])
@login_required
def editar_ingreso(id_ingreso):
    ingreso = Ingreso.query.get_or_404(id_ingreso)
    try:
        data = request.form
        ingreso.tipo_producto = data.get('tipo_producto')
        ingreso.marca = data.get('marca')
        ingreso.modelo = data.get('modelo')
        ingreso.color = data.get('color')
        ingreso.cantidad = get_safe_int(data.get('cantidad'))
        ingreso.unidad = data.get('unidad')
        ingreso.precio = get_safe_float(data.get('precio'))
        ingreso.total = ingreso.cantidad * ingreso.precio
        ingreso.fecha_ingreso = datetime.strptime(data.get('fecha_ingreso'), '%Y-%m-%d')
        ingreso.stock = get_safe_int(data.get('stock'))
        ingreso.stock_minimo = get_safe_int(data.get('stock_minimo'))
        ingreso.responsable = data.get('responsable')
        ingreso.observaciones = data.get('observaciones')
        db.session.commit()
        flash('Modificación exitosa', 'success')
        return redirect(url_for('ingresos.dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar ingreso: {str(e)}', 'danger')
        return redirect(url_for('ingresos.dashboard'))


@ingresos_bp.route('/eliminar/<int:id_ingreso>', methods=['POST'])
@login_required
def eliminar_ingreso(id_ingreso):
    ingreso = Ingreso.query.get_or_404(id_ingreso)
    db.session.delete(ingreso)
    db.session.commit()
    flash('Ingreso eliminado correctamente.', 'success')
    return redirect(url_for('ingresos.dashboard'))


@ingresos_bp.route('/registrar_ajax', methods=['POST'])
@login_required
def nuevo_ingreso_ajax():
    try:
        data = request.form
        tipo_nombre = data.get('tipo_producto')
        marca = data.get('marca')
        modelo = data.get('modelo')
        color = data.get('color')
        unidad = data.get('unidad')
        cantidad = get_safe_int(data.get('cantidad'))
        precio = get_safe_float(data.get('precio'))
        total = cantidad * precio
        stock = get_safe_int(data.get('stock'))
        stock_minimo = get_safe_int(data.get('stock_minimo'))

        # Verifica si el tipo ya existe o crearlo
        tipo = TipoProducto.query.filter_by(nombre_tipo=tipo_nombre).first()
        if not tipo:
            tipo = TipoProducto(nombre_tipo=tipo_nombre)
            db.session.add(tipo)
            db.session.commit()

        # Busca si el producto ya existe por marca, modelo y color
        producto = Producto.query.filter_by(marca=marca, modelo_impresora=modelo, color=color).first()

        if producto:
            producto.stock += stock
            producto.stock_minimo = stock_minimo
            producto.unidad = unidad
        else:
            producto = Producto(
                nombre=f"{tipo_nombre} {marca} {modelo}".upper(),
                id_tipo=tipo.id_tipo,
                marca=marca,
                modelo_impresora=modelo,
                color=color,
                unidad=unidad,
                stock=stock,
                stock_minimo=stock_minimo,
                activo=True
            )
            db.session.add(producto)
            db.session.commit()

        ingreso = Ingreso(
            tipo_producto=tipo_nombre,
            marca=marca,
            modelo=modelo,
            color=color,
            cantidad=cantidad,
            unidad=unidad,
            precio=precio,
            total=total,
            stock=stock,
            stock_minimo=stock_minimo,
            responsable=data.get('responsable'),
            observaciones=data.get('observaciones'),
            id_usuario=current_user.id_usuario,
            fecha_ingreso=datetime.strptime(data.get('fecha_ingreso'), '%Y-%m-%d'),
            fecha_registro=datetime.utcnow(),
            id_producto=producto.id_producto
        )

        db.session.add(ingreso)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Ingreso registrado correctamente.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
