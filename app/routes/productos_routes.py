from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import Producto, TipoProducto
from app import db
from datetime import datetime

productos_bp = Blueprint('productos', __name__, url_prefix='/productos')

@productos_bp.route('/dashboard')
@login_required
def dashboard():
    productos = Producto.query.all()
    tipos_productos = TipoProducto.query.all()
    return render_template('productos.html', productos=productos, tipos_productos=tipos_productos, current_year=datetime.now().year)

@productos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        id_tipo = int(request.form['id_tipo'])
        marca = request.form.get('marca')
        modelo_impresora = request.form.get('modelo_impresora')
        color = request.form.get('color')
        stock = int(request.form['stock'])
        stock_minimo = int(request.form['stock_minimo'])
        unidad = request.form.get('unidad')

        if not nombre or not id_tipo or not stock_minimo:
            flash('Nombre, Tipo y Stock mínimo son obligatorios.', 'danger')
            return redirect(url_for('productos.dashboard'))

        nuevo_producto = Producto(
            nombre=nombre,
            id_tipo=id_tipo,
            marca=marca,
            modelo_impresora=modelo_impresora,
            color=color,
            stock=stock,
            stock_minimo=stock_minimo,
            unidad=unidad,
            activo=True
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        flash('Producto registrado exitosamente.', 'success')
        return redirect(url_for('productos.dashboard'))

    tipos_productos = TipoProducto.query.all()
    return render_template('nuevo_producto.html', tipos_productos=tipos_productos)

@productos_bp.route('/editar/<int:id_producto>', methods=['GET', 'POST'])
@login_required
def editar_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)

    if request.method == 'POST':
        try:
            producto.nombre = request.form['nombre']
            producto.id_tipo = int(request.form['id_tipo'])
            producto.marca = request.form.get('marca')
            producto.modelo_impresora = request.form.get('modelo_impresora')
            producto.color = request.form.get('color')
            producto.stock = int(request.form.get('stock'))
            producto.stock_minimo = int(request.form.get('stock_minimo'))
            producto.unidad = request.form.get('unidad')
            producto.activo = 'activo' in request.form

            db.session.commit()
            return jsonify({"status": "success", "mensaje": "Producto actualizado correctamente."})
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "mensaje": f"Error al actualizar: {str(e)}"})

    tipos_productos = TipoProducto.query.all()
    return render_template('editar_producto.html', producto=producto, tipos_productos=tipos_productos)

@productos_bp.route('/eliminar/<int:id_producto>', methods=['POST'])
@login_required
def eliminar_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado correctamente.', 'success')
    return redirect(url_for('productos.dashboard'))

@productos_bp.route('/api/productos_por_tipo/<int:id_tipo>', methods=['GET'])
def productos_por_tipo(id_tipo):
    productos = Producto.query.filter_by(id_tipo=id_tipo, activo=True).all()
    resultado = [
        {
            "id_producto": p.id_producto,
            "nombre": p.nombre
        } for p in productos
    ]
    return jsonify(resultado)

@productos_bp.route('/info/<int:id_producto>')
@login_required
def info_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    return jsonify({
        'tipo': producto.tipo_producto.nombre_tipo,  
        'marca': producto.marca,
        'color': producto.color,
        'unidad': producto.unidad
    })

@productos_bp.route('/lista')
@login_required
def productos_lista():
    productos = Producto.query.join(TipoProducto).with_entities(
        Producto.id_producto.label('id'),
        Producto.marca,
        Producto.modelo_impresora.label('modelo'),
        Producto.color,
        Producto.unidad,
        TipoProducto.nombre_tipo.label('tipo')
    ).all()

    return jsonify([p._asdict() for p in productos])
