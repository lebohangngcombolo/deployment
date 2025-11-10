from flask import Flask
import os
from .extensions import (
    db, jwt, mail, cloudinary_client, mongo_client,
    migrate, cors, bcrypt, oauth
)
from .models import *
from .routes import auth, admin_routes, candidate_routes, ai_routes
from .services.email_service import EmailService  # <-- import EmailService


def create_app():
    app = Flask(__name__)

    # Pick config dynamically
    config_name = os.getenv("FLASK_ENV", "production").capitalize()
    app.config.from_object(f"app.config.{config_name}Config")

    # ---------------- Initialize Extensions ----------------
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)
    bcrypt.init_app(app)
    cloudinary_client.init_app(app)
    cors.init_app(
        app,
        origins=["*"],  # adjust for production
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        supports_credentials=True,
    )

    # ---------------- Initialize EmailService ----------------
    EmailService.init_app(app)  # <-- this fixes the "EmailService not initialized" error

    # ---------------- Register Blueprints ----------------
    auth.init_auth_routes(app)
    app.register_blueprint(admin_routes.admin_bp, url_prefix="/api/admin")
    app.register_blueprint(candidate_routes.candidate_bp, url_prefix="/api/candidate")
    app.register_blueprint(ai_routes.ai_bp)

    # ---------------- Health Check Route ----------------
    @app.route("/api/health")
    def health():
        return {"status": "ok", "message": "Recruitment backend is running!"}, 200

    return app

