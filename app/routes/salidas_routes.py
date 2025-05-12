from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Salida, Producto
from app import db
from datetime import datetime



salidas_bp = Blueprint('salidas', __name__, url_prefix='/salidas')
@salidas_bp.route('/dashboard')  # ← usa salidas_bp
@login_required
def dashboard():
    salidas = Salida.query.all()
    return render_template('salidas_dashboard.html', salidas=salidas)


@salidas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_salida():
    productos = Producto.query.all()

    if request.method == 'POST':
        producto_id = request.form['producto_id']
        cantidad = int(request.form['cantidad'])
        responsable = request.form['responsable']
        observaciones = request.form.get('observaciones')

        producto = Producto.query.get_or_404(producto_id)

        # Verificamos si hay stock suficiente
        if producto.stock < cantidad:
            flash('Stock insuficiente para realizar la salida.', 'danger')
            return redirect(url_for('salidas.nueva_salida'))

        # Actualizamos el stock
        producto.stock -= cantidad

        nueva_salida = Salida(
            producto_id=producto_id,
            cantidad=cantidad,
            fecha_salida=datetime.now(),
            responsable=responsable,
            observaciones=observaciones
        )
        db.session.add(nueva_salida)
        db.session.commit()

        flash('Salida registrada correctamente y stock actualizado.', 'success')
        return redirect(url_for('salidas.dashboard'))

    return render_template('nueva_salida.html', productos=productos)
