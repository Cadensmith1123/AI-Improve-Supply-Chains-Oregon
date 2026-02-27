import os
from dotenv import load_dotenv

from .blueprint import auth_bp
from .middleware import install_auth_middleware


def init_auth(app):
    load_dotenv()

    # JWT config
    app.config["JWT_SECRET"] = os.environ.get("JWT_SECRET") or app.config.get("JWT_SECRET")
    app.config.setdefault("JWT_ISSUER", os.environ.get("JWT_ISSUER", "local-food-app"))
    app.config.setdefault("JWT_AUDIENCE", os.environ.get("JWT_AUDIENCE", "local-food-api"))
    app.config.setdefault("JWT_ACCESS_TTL_SECONDS", int(os.environ.get("JWT_ACCESS_TTL_SECONDS", "3600")))

    if not app.config.get("JWT_SECRET"):
        raise RuntimeError("JWT_SECRET is not set. Add it to .env or app.config['JWT_SECRET'].")

    # Register blueprint
    # /auth/login will be available after this
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Install auth middleware
    install_auth_middleware(app)