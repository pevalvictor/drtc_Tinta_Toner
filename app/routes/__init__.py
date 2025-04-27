def register_routes(app):
    from .auth_routes import auth_bp
    from .productos_routes import productos_bp
    from .ingresos_routes import ingresos_bp
    from .salidas_routes import salidas_bp
    from .logs_routes import logs_bp
    from .reportes_routes import reportes_bp
    


    app.register_blueprint(auth_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(ingresos_bp)
    app.register_blueprint(salidas_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(reportes_bp)
    
