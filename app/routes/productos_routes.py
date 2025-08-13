from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import Producto, TipoProducto
from app import db
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import pandas as pd
from flask import send_file



productos_bp = Blueprint('productos', __name__, url_prefix='/productos')

@productos_bp.route('/dashboard')
@login_required
def dashboard():
    productos = Producto.query.filter_by(activo=True).all()  
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


@productos_bp.route('/desactivar/<int:id_producto>', methods=['POST'])
@login_required
def desactivar_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    producto.activo = False
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success', 'mensaje': 'Producto desactivado correctamente'})

    flash('Producto desactivado correctamente', 'success')
    return redirect(url_for('productos.dashboard'))



@productos_bp.route('/inactivos')
@login_required
def inactivos():
    productos_inactivos = Producto.query.filter_by(activo=False).all()
    return render_template('productos_inactivos.html', productos=productos_inactivos, current_year=datetime.now().year)

@productos_bp.route('/reactivar/<int:id_producto>', methods=['POST'])
@login_required
def reactivar_producto(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    producto.activo = True
    db.session.commit()
    return '', 204  




@productos_bp.route('/inactivos/pdf')
@login_required
def exportar_pdf_inactivos():
    productos = Producto.query.filter_by(activo=False).all()

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font('Arial', 'B', 12)
    titulo = f'DRTC - PRODUCTOS INACTIVOS | Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    pdf.cell(0, 10, titulo, ln=True, align='C')
    pdf.ln(4)

    headers = ['Nombre', 'Tipo', 'Marca', 'Modelo', 'Color', 'Stock', 'Unidad']
    col_widths = [50, 30, 30, 30, 25, 20, 25]
    line_height = 5

    pdf.set_fill_color(97, 12, 12)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(0)

    for p in productos:
        row = [
            p.nombre,
            p.tipo_producto.nombre_tipo if p.tipo_producto else '-',
            p.marca or '-',
            p.modelo_impresora or '-',
            p.color or '-',
            str(p.stock),
            p.unidad or '-'
        ]

        max_lines = 1
        line_data = []
        for i, text in enumerate(row):
            lines = pdf.multi_cell(col_widths[i], line_height, text, border=0, split_only=True)
            line_data.append(lines)
            max_lines = max(max_lines, len(lines))

        row_height = max_lines * line_height
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for i in range(len(headers)):
            pdf.rect(x_start + sum(col_widths[:i]), y_start, col_widths[i], row_height)

        for i, lines in enumerate(line_data):
            x = x_start + sum(col_widths[:i]) + 1
            y = y_start
            for line in lines:
                pdf.set_xy(x, y)
                pdf.cell(col_widths[i] - 2, line_height, line)
                y += line_height

        pdf.set_y(y_start + row_height)

    output = BytesIO()
    output.write(pdf.output(dest='S').encode('latin1'))
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='productos_inactivos.pdf', mimetype='application/pdf')


@productos_bp.route('/inactivos/excel')
@login_required
def exportar_excel_inactivos():
    productos = Producto.query.filter_by(activo=False).all()

    data = []
    for p in productos:
        data.append({
            'Nombre': p.nombre,
            'Tipo': p.tipo_producto.nombre_tipo if p.tipo_producto else '-',
            'Marca': p.marca or '-',
            'Modelo': p.modelo_impresora or '-',
            'Color': p.color or '-',
            'Stock': p.stock,
            'Unidad': p.unidad or '-'
        })

    df = pd.DataFrame(data)
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, startrow=2, sheet_name='Inactivos')
        wb = writer.book
        ws = writer.sheets['Inactivos']

        titulo = f'DRTC - PRODUCTOS INACTIVOS | Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        titulo_style = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'bg_color': '#610c0c', 'font_color': '#ffffff'})
        ws.merge_range('A1:G1', titulo, titulo_style)

        header_style = wb.add_format({'bold': True, 'bg_color': '#d9d9d9', 'border': 1, 'align': 'center'})
        for col_num, col_name in enumerate(df.columns):
            ws.write(2, col_num, col_name, header_style)

        cell_style = wb.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
        for row_num, row_data in enumerate(data, start=3):
            for col_num, key in enumerate(df.columns):
                ws.write(row_num, col_num, row_data[key], cell_style)

        col_widths = [30, 20, 20, 20, 15, 10, 15]
        for i, width in enumerate(col_widths):
            ws.set_column(i, i, width)

    output.seek(0)
    return send_file(output,
                     as_attachment=True,
                     download_name='productos_inactivos.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    
