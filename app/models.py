from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from . import db

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # 'Almacen' o 'UTI'
    nombre_completo = db.Column(db.String(100), nullable=False)

    def get_id(self):
        return str(self.id_usuario)

class Producto(db.Model):
    __tablename__ = 'productos'
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'Tinta' o 'Toner'
    marca = db.Column(db.String(50))
    modelo_impresora = db.Column(db.String(100))
    color = db.Column(db.String(30))
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    unidad = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)

class Ingreso(db.Model):
    __tablename__ = 'ingresos'
    id_ingreso = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    fecha_ingreso = db.Column(db.Date, default=datetime.utcnow)
    responsable = db.Column(db.String(100))
    observaciones = db.Column(db.Text)

    producto = db.relationship('Producto', backref='ingresos')

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

class Log(db.Model):
    __tablename__ = 'logs'
    id_log = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    accion = db.Column(db.String(50), nullable=False)

