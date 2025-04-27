from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from app.models import Usuario
from app import db
import traceback  

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    print("Entrando al login...")  

    try:
        if request.method == 'POST':
            print(" POST recibido")
            print("Formulario recibido:", request.form)

            username = request.form.get('usuario')
            password = request.form.get('password')

            if not username or not password:
                print(" Campos vacíos o no enviados correctamente")
                flash("Todos los campos son obligatorios")
                return render_template('login.html')

            print(f"🧑 Usuario: {username} | 🔒 Password: {password}")

            user = Usuario.query.filter_by(usuario=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                print("✅ Login exitoso")
                return redirect(url_for('productos.dashboard'))
            else:
                print("Credenciales incorrectas")
                flash('Credenciales incorrectas')

        return render_template('login.html')

    except Exception as e:
        print("🚨 ERROR EN LOGIN:", repr(e))
        traceback.print_exc()  # 🧠 Imprime la traza del error en consola
        raise e
