import os
from flask import Flask, jsonify

from app.config import config_by_name
from app.extensions import db, jwt, bcrypt, cors, limiter


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    limiter.init_app(app)

    from app.auth import auth_bp
    from app.routes import apps_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(apps_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error."}), 500

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"error": "Too many requests. Please slow down."}), 429
