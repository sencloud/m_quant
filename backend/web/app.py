from flask import Flask
from flask_cors import CORS
from .routes import bp

def create_app():
    """Create Flask application"""
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    app.register_blueprint(bp)
    return app