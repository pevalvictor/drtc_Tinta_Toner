from flask import Blueprint, render_template, send_file
from flask_login import login_required
from app.models import Producto, Ingreso, Salida
from sqlalchemy import func, and_
from app import db
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

@reportes_bp.route('/general')
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
            'tipo': producto.tipo_producto.nombre_tipo if producto.tipo_producto else '-',
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


#  REPORTES DE SALIDAS DE PRODUCTOS

@reportes_bp.route('/salidas/pdf')
@login_required
def exportar_salidas_pdf():
    salidas = Salida.query.all()

    pdf = FPDF(orientation='L', unit='mm', format='A4')  
    pdf.add_page()

    pdf.set_font('Arial', 'B', 12)
    titulo = f'DRTC - SALIDAS DE PRODUCTOS | Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    pdf.cell(0, 10, titulo, ln=True, align='C')
    pdf.ln(4)

    
    headers = ['Producto', 'Cant.', 'Fecha', 'Destino', 'Responsable', 'Observaciones']
    col_widths = [55, 15, 25, 35, 45, 102]

    
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(97, 12, 12)
    pdf.set_text_color(255)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, fill=True)
    pdf.ln()

  
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(0)
    for s in salidas:
        row = [
            s.producto.nombre,
            str(s.cantidad),
            s.fecha_salida.strftime('%Y-%m-%d'),
            s.destino,
            s.responsable,
            s.observaciones or ''
        ]
        for i, value in enumerate(row):
            pdf.cell(col_widths[i], 7, str(value)[:80], border=1)
        pdf.ln()

    output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    output.write(pdf_bytes)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='reporte_salidas.pdf', mimetype='application/pdf')




#EMITIR REPORTE EN EXCEL
@reportes_bp.route('/salidas/excel')
@login_required
def exportar_salidas_excel():
    salidas = Salida.query.all()

    data = []
    for s in salidas:
        data.append({
            'Producto': s.producto.nombre,
            'Cantidad': s.cantidad,
            'Fecha de Salida': s.fecha_salida.strftime('%Y-%m-%d'),
            'Destino': s.destino,
            'Responsable': s.responsable,
            'Observaciones': s.observaciones or ''
        })

    df = pd.DataFrame(data)
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, startrow=2, sheet_name='Salidas')
        workbook = writer.book
        sheet = writer.sheets['Salidas']

        header_text = 'DRTC - SALIDAS DE PRODUCTOS | Generado: ' + datetime.now().strftime('%Y-%m-%d %H:%M')
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#610c0c',
            'font_color': '#FFFFFF'
        })
        sheet.merge_range('A1:F1', header_text, header_format)

        header_style = workbook.add_format({'bold': True, 'bg_color': '#d9d9d9', 'border': 1})
        for col_num, column in enumerate(df.columns):
            sheet.write(2, col_num, column, header_style)

        widths = [30, 12, 18, 25, 25, 40]
        for i, w in enumerate(widths):
            sheet.set_column(i, i, w)

    output.seek(0)
    return send_file(output, as_attachment=True, download_name='reporte_salidas.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


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
    headers = ['ID', 'Nombre', 'Tipo', 'Marca', 'Modelo', 'Color', 'Stock', 'Unidad']
    col_widths = [12, 50, 30, 30, 30, 25, 20, 20]
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
        fila = [
            str(p.id_producto),
            p.nombre,
            p.tipo_producto.nombre_tipo if p.tipo_producto else '-',
            p.marca or '-',
            p.modelo_impresora or '-',
            p.color or '-',
            str(p.stock),
            p.unidad or '-'
        ]

        max_lines = max(len(pdf.multi_cell(col_widths[i], line_height, text, border=0, split_only=True)) for i, text in enumerate(fila))
        row_height = max_lines * line_height
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for i in range(len(headers)):
            pdf.rect(x_start + sum(col_widths[:i]), y_start, col_widths[i], row_height)

        for i, text in enumerate(fila):
            lines = pdf.multi_cell(col_widths[i], line_height, text, border=0, split_only=True)
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
            'ID': p.id_producto,
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
        estilo_titulo = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'bg_color': '#610c0c', 'font_color': '#ffffff'})
        ws.merge_range('A1:H1', titulo, estilo_titulo)

        estilo_cabecera = wb.add_format({'bold': True, 'bg_color': '#d9d9d9', 'border': 1, 'align': 'center'})
        for col_num, col_name in enumerate(df.columns):
            ws.write(2, col_num, col_name, estilo_cabecera)

        estilo_dato = wb.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
        for row_num, row in enumerate(data, start=3):
            for col_num, key in enumerate(df.columns):
                ws.write(row_num, col_num, row[key], estilo_dato)

        ws.set_column('A:A', 8)
        ws.set_column('B:B', 30)
        ws.set_column('C:H', 18)

    output.seek(0)
    return send_file(output,
                     as_attachment=True,
                     download_name='productos_inactivos.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    
    
    
    
    