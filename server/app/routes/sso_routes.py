# sso_routes.py
from flask import Blueprint, current_app, jsonify, url_for
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db, oauth
from app.models import User, OAuthConnection
from app.services.audit2 import AuditService

import secrets

sso_bp = Blueprint("sso_bp", __name__)

# ------------------- SSO Provider Registration -------------------
def register_sso_provider(app):
    if not hasattr(app, "oauth_initialized"):
        oauth.init_app(app)
        app.oauth_initialized = True

    oauth.register(
        name="auth0",
        client_id=app.config["SSO_CLIENT_ID"],
        client_secret=app.config["SSO_CLIENT_SECRET"],
        server_metadata_url=app.config["SSO_METADATA_URL"],
        client_kwargs={"scope": "openid profile email"},
        userinfo_endpoint=app.config.get("SSO_USERINFO_URL") or "https://YOUR_DOMAIN/userinfo"
    )

# ------------------- SSO Login -------------------
@sso_bp.route("/api/auth/sso")
def sso_login():
    try:
        redirect_uri = url_for("sso_bp.sso_callback", _external=True)
        return oauth.auth0.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.error(f"SSO login initiation error: {str(e)}", exc_info=True)
        return jsonify({"error": "SSO login failed"}), 500

# ------------------- SSO Callback -------------------
@sso_bp.route("/api/auth/sso/callback")
def sso_callback():
    try:
        token = oauth.auth0.authorize_access_token()
        user_info = token.get("userinfo")
        if not user_info or "email" not in user_info:
            return jsonify({"error": "Failed to fetch SSO user info"}), 400

        email = user_info["email"].strip().lower()
        sso_id = user_info.get("sub") or user_info.get("id")

        # ------------------- Only allow existing users -------------------
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if not user:
            current_app.logger.warning(f"SSO login attempt for non-existing user: {email}")
            return jsonify({"error": "User does not exist"}), 403

        # ------------------- Check/create OAuthConnection -------------------
        oauth_conn = OAuthConnection.query.filter_by(user_id=user.id, provider="sso").first()
        if not oauth_conn:
            oauth_conn = OAuthConnection(
                user_id=user.id,
                provider="sso",
                provider_user_id=sso_id,
                access_token=secrets.token_urlsafe(32)
            )
            db.session.add(oauth_conn)
            db.session.commit()

        # ------------------- Create JWT tokens -------------------
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)

        # ------------------- Determine dashboard -------------------
        from app.routes.auth_routes import ROLE_DASHBOARD_MAP  # reuse your existing map
        dashboard_path = (
            "/enrollment" if user.role == "candidate" and not getattr(user, "enrollment_completed", False)
            else ROLE_DASHBOARD_MAP.get(user.role, "/dashboard")
        )
        if dashboard_path.startswith("/api/"):
            dashboard_path = dashboard_path.replace("/api", "", 1)

        # ------------------- Audit log -------------------
        AuditService.log(user_id=user.id, action="sso_login")

        # ------------------- Return JSON instead of redirect -------------------
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "enrollment_completed": getattr(user, "enrollment_completed", False)
            },
            "dashboard": dashboard_path
        }), 200

    except Exception as e:
        current_app.logger.error(f"SSO callback error: {str(e)}", exc_info=True)
        return jsonify({"error": "SSO authentication failed"}), 500
