from flask import request, redirect, url_for, g
import jwt
from .tokens import verify_access_token

"""
installs middleware to verify JWT for each request.
"""

def install_auth_middleware(app):
    """
    Installs a before_request hook to handle JWT authentication.
    """
    @app.before_request
    def load_user_from_token():
        # Allow public endpoints
        if request.endpoint in ['static', 'auth.login', 'auth.register', 'health', 'logout']:
            return

        # Get Token from Cookie
        token = request.cookies.get('token')

        # Verify Token
        try:
            payload = verify_access_token(token)
            g.user_id = payload.get('sub')
            g.tenant_id = payload.get('tid')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return redirect(url_for('logout'))
