from flask import Blueprint, render_template, send_file, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Producto, Ingreso, Salida
from sqlalchemy import func, and_
from app import db
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
from app.models import Producto


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

    consumo_por_oficina = (
        db.session.query(
            Salida.destino,  
            func.sum(Salida.cantidad).label('total')
        )
        .filter(Salida.destino.isnot(None)) 
        .group_by(Salida.destino)
        .order_by(func.sum(Salida.cantidad).desc())
        .limit(5)
        .all()
    )

    consumo_por_producto = (
        db.session.query(
            Producto.marca,
            Producto.modelo_impresora,
            func.sum(Salida.cantidad).label('total')
        )
        .join(Producto, Producto.id_producto == Salida.id_producto)
        .group_by(Producto.marca, Producto.modelo_impresora)
        .order_by(func.sum(Salida.cantidad).desc())
        .limit(5)
        .all()
    )

    return render_template('reportes_kpis.html',
        total_productos=total_productos,
        productos_alerta=productos_alerta,
        productos_normales=productos_normales,
        stock_total=stock_total,
        consumo_por_oficina=consumo_por_oficina,
        consumo_por_producto=consumo_por_producto
    )



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



def obtener_salidas_filtradas():
    fecha_inicio = request.args.get('fechaInicio')
    fecha_fin = request.args.get('fechaFin')
    query = Salida.query

    try:
        if fecha_inicio:
            fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            query = query.filter(Salida.fecha_salida >= fi)
        if fecha_fin:
            ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            query = query.filter(Salida.fecha_salida <= ff)
    except Exception as e:
        print("⚠️ Error al parsear fechas:", e)

    salidas = query.order_by(Salida.fecha_salida).all()
    return salidas



@reportes_bp.route('/salidas/pdf')
@login_required
def exportar_salidas_pdf():
    salidas = obtener_salidas_filtradas()

    if not salidas:
        flash("No hay datos disponibles para generar el PDF.", "danger")
        return redirect(url_for("salidas.dashboard"))

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font('Arial', 'B', 12)
    titulo = f'DRTC - SALIDAS DE PRODUCTOS | Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    pdf.cell(0, 10, titulo, ln=True, align='C')
    pdf.ln(4)

    headers = ['Producto', 'Cantidad', 'Fecha de Salida', 'Destino', 'Responsable', 'Observaciones']
    col_widths = [55, 18, 28, 46, 46, 87]
    line_height = 5

    pdf.set_fill_color(97, 12, 12)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(0)

    for s in salidas:
        row = [
            s.producto.nombre,
            str(s.cantidad),
            s.fecha_salida.strftime('%Y-%m-%d'),
            s.destino or '',
            s.responsable or '',
            s.observaciones or ''
        ]

        line_data = []
        max_lines = 1

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
    return send_file(output, as_attachment=True, download_name='reporte_salidas.pdf', mimetype='application/pdf')



@reportes_bp.route('/salidas/excel')
@login_required
def exportar_salidas_excel():
    salidas = obtener_salidas_filtradas()

    if not salidas:
        flash("No hay datos disponibles para generar el Excel.", "danger")
        return redirect(url_for("salidas.dashboard"))

    data = []
    for s in salidas:
        data.append({
            'Producto': s.producto.nombre,
            'Cantidad': s.cantidad,
            'Fecha de Salida': s.fecha_salida.strftime('%Y-%m-%d'),
            'Destino': s.destino or '',
            'Responsable': s.responsable or '',
            'Observaciones': s.observaciones or ''
        })

    df = pd.DataFrame(data)
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, startrow=2, sheet_name='Salidas')
        wb = writer.book
        ws = writer.sheets['Salidas']

        titulo = f'DRTC - SALIDAS DE PRODUCTOS | Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        title_format = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'bg_color': '#610c0c', 'font_color': '#ffffff'})
        ws.merge_range('A1:F1', titulo, title_format)

        header_format = wb.add_format({'bold': True, 'bg_color': '#d9d9d9', 'border': 1, 'align': 'center'})
        for col_num, col_name in enumerate(df.columns):
            ws.write(2, col_num, col_name, header_format)

        wrap = wb.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
        for row_num, row_data in enumerate(data, start=3):
            for col_num, key in enumerate(df.columns):
                ws.write(row_num, col_num, row_data[key], wrap)

        col_widths = [30, 10, 15, 25, 25, 50]
        for i, width in enumerate(col_widths):
            ws.set_column(i, i, width)

    output.seek(0)
    return send_file(output,
                     as_attachment=True,
                     download_name='reporte_salidas.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
