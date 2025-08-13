from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from . import db

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)

    def get_id(self):
        return str(self.id_usuario)


class Producto(db.Model):
    __tablename__ = 'productos'
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    id_tipo = db.Column(db.Integer, db.ForeignKey('tipos_productos.id_tipo'), nullable=False)
    marca = db.Column(db.String(50))
    modelo_impresora = db.Column(db.String(100))
    color = db.Column(db.String(30))
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    unidad = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)


class TipoProducto(db.Model):
    __tablename__ = 'tipos_productos'
    id_tipo = db.Column(db.Integer, primary_key=True)
    nombre_tipo = db.Column(db.String(50), unique=True, nullable=False)

    productos = db.relationship('Producto', backref='tipo_producto', lazy=True)


class Ingreso(db.Model):
    __tablename__ = 'ingresos'
    id_ingreso = db.Column(db.Integer, primary_key=True)

    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=True)
    producto = db.relationship('Producto', backref='ingresos')

    tipo_producto = db.Column(db.String(50), nullable=False)  

    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(100))
    color = db.Column(db.String(30))
    cantidad = db.Column(db.Integer, nullable=False)
    unidad = db.Column(db.String(20))
    precio = db.Column(db.Float, nullable=False, default=0)
    total = db.Column(db.Float, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=0)
    fecha_ingreso = db.Column(db.Date, default=datetime.utcnow)
    responsable = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    usuario = db.relationship('Usuario', backref='ingresos')


class Salida(db.Model):
    __tablename__ = 'salidas'
    id_salida = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    fecha_salida = db.Column(db.Date, default=datetime.utcnow)
    destino = db.Column(db.String(100))
    responsable = db.Column(db.String(100))
    observaciones = db.Column(db.Text)

    producto = db.relationship('Producto', backref='salidas')
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    usuario = db.relationship('Usuario', backref='salidas')


class DetalleSalida(db.Model):
    __tablename__ = 'detalles_salida'
    id_detalle = db.Column(db.Integer, primary_key=True)
    id_salida = db.Column(db.Integer, db.ForeignKey('salidas.id_salida'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)

    salida = db.relationship('Salida', backref='detalles')
    producto = db.relationship('Producto', backref='detalles_salida')


class Log(db.Model):
    __tablename__ = 'logs'
    id_log = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    accion = db.Column(db.String(50), nullable=False)
