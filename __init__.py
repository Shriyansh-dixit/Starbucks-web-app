from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../config.py', silent=True)
    
    from .routes import bp
    app.register_blueprint(bp)
    
    return app