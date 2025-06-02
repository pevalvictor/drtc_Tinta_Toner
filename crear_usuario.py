from app import db
from app.models import Usuario
from werkzeug.security import generate_password_hash
from app import create_app  

app = create_app()  

with app.app_context():
    usuario_existente = Usuario.query.filter_by(usuario='admin').first()
    if not usuario_existente:
        nuevo_usuario = Usuario(
            usuario="admin",
            password_hash=generate_password_hash("123456"),
            rol="admin",
            nombre_completo="Administrador General"
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        print(" Usuario creado correctamente")
    else:
        print(" El usuario 'admin' ya existe")
