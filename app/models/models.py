class Producto(db.Model):
    __tablename__ = 'productos'

    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    marca = db.Column(db.String(50))
    modelo_impresora = db.Column(db.String(100))
    color = db.Column(db.String(30))
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=0)
    unidad = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Producto {self.nombre}>'
