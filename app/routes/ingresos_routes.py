from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Ingreso, Producto, TipoProducto
from app import db
from datetime import datetime

from io import BytesIO
import pandas as pd
from flask import send_file
from xhtml2pdf import pisa
from flask import make_response


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

        return jsonify(success=True, message="Ingreso actualizado correctamente")
    
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Error al actualizar ingreso: {str(e)}")


@ingresos_bp.route('/eliminar/<int:id_ingreso>', methods=['POST'])
@login_required
def eliminar_ingreso(id_ingreso):
    ingreso = Ingreso.query.get_or_404(id_ingreso)
    try:
        db.session.delete(ingreso)
        db.session.commit()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=True, message="Ingreso eliminado correctamente")
        flash("Ingreso eliminado correctamente", "success")
    except Exception as e:
        db.session.rollback()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Error al eliminar")
        flash("Error al eliminar ingreso", "danger")
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

        tipo = TipoProducto.query.filter_by(nombre_tipo=tipo_nombre).first()
        if not tipo:
            tipo = TipoProducto(nombre_tipo=tipo_nombre)
            db.session.add(tipo)
            db.session.commit()

   
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
    
@ingresos_bp.route('/reporte/pdf')
@login_required
def exportar_ingresos_pdf():
    from fpdf import FPDF
    ingresos = Ingreso.query.order_by(Ingreso.fecha_ingreso.desc()).all()

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font('Arial', 'B', 12)
    titulo = f'DRTC - REPORTE DE INGRESOS | Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    pdf.cell(0, 10, titulo, ln=True, align='C')
    pdf.ln(4)

    headers = ['Fecha', 'Tipo', 'Marca', 'Modelo', 'Color', 'Cantidad', 'Unidad', 'Precio', 'Total', 'Responsable']
    col_widths = [25, 20, 25, 25, 20, 20, 18, 20, 22, 40]
    line_height = 5

    pdf.set_fill_color(97, 12, 12)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(0)

    for i in ingresos:
        row = [
            i.fecha_ingreso.strftime('%Y-%m-%d'),
            i.tipo_producto or '-',
            i.marca or '-',
            i.modelo or '-',
            i.color or '-',
            str(i.cantidad),
            i.unidad or '-',
            f"S/. {i.precio:.2f}",
            f"S/. {i.total:.2f}",
            i.responsable or '-'
        ]

        max_lines = 1
        line_data = []
        for j, text in enumerate(row):
            lines = pdf.multi_cell(col_widths[j], line_height, text, border=0, split_only=True)
            line_data.append(lines)
            max_lines = max(max_lines, len(lines))

        row_height = max_lines * line_height
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for j in range(len(headers)):
            pdf.rect(x_start + sum(col_widths[:j]), y_start, col_widths[j], row_height)

        for j, lines in enumerate(line_data):
            x = x_start + sum(col_widths[:j]) + 1
            y = y_start
            for line in lines:
                pdf.set_xy(x, y)
                pdf.cell(col_widths[j] - 2, line_height, line)
                y += line_height

        pdf.set_y(y_start + row_height)

    output = BytesIO()
    output.write(pdf.output(dest='S').encode('latin1'))
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='reporte_ingresos.pdf', mimetype='application/pdf')



@ingresos_bp.route('/reporte/excel')
@login_required
def exportar_ingresos_excel():
    ingresos = Ingreso.query.order_by(Ingreso.fecha_ingreso.desc()).all()

    data = []
    for i in ingresos:
        data.append({
            'Fecha': i.fecha_ingreso.strftime('%Y-%m-%d'),
            'Tipo': i.tipo_producto,
            'Marca': i.marca,
            'Modelo': i.modelo,
            'Color': i.color,
            'Cantidad': i.cantidad,
            'Unidad': i.unidad,
            'Precio': f"S/. {i.precio:.2f}",
            'Total': f"S/. {i.total:.2f}",
            'Responsable': i.responsable,
            'Observaciones': i.observaciones or ''
        })

    df = pd.DataFrame(data)
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, startrow=2, sheet_name='Ingresos')
        wb = writer.book
        ws = writer.sheets['Ingresos']

        titulo = f'DRTC - REPORTE DE INGRESOS | Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        titulo_style = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'bg_color': '#610c0c', 'font_color': '#ffffff'})
        ws.merge_range('A1:K1', titulo, titulo_style)

    
        header_style = wb.add_format({'bold': True, 'bg_color': '#d9d9d9', 'border': 1, 'align': 'center'})
        for col_num, col_name in enumerate(df.columns):
            ws.write(2, col_num, col_name, header_style)

        cell_style = wb.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
        for row_num, row_data in enumerate(data, start=3):
            for col_num, key in enumerate(df.columns):
                ws.write(row_num, col_num, row_data[key], cell_style)

        col_widths = [15, 15, 15, 18, 12, 10, 10, 12, 12, 25, 30]
        for i, width in enumerate(col_widths):
            ws.set_column(i, i, width)

    output.seek(0)
    return send_file(output,
                     as_attachment=True,
                     download_name='reporte_ingresos.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

