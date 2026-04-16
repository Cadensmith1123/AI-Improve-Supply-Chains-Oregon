from flask import request, redirect, url_for, g
import jwt
from .tokens import verify_access_token
from .user_management import get_user_totp

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
        if request.endpoint in ['static', 'auth.login', 'auth.register', 'health', 'logout', 'auth.reset_password_form', 'auth.reset_password_verify', 'auth.reset_password_complete']:
            return

        # Get Token from Cookie
        token = request.cookies.get('token')

        # Verify Token
        try:
            payload = verify_access_token(token)
            g.user_id = payload.get('sub')
            g.tenant_id = payload.get('tid')
            g.username = payload.get('username') 
            g.is_anonymous = payload.get('anon', False)

            if not g.is_anonymous and request.endpoint not in ['auth.totp_setup', 'auth.totp_confirm', 'static', 'logout']:
                totp_data = get_user_totp(g.user_id)
                if not totp_data or not totp_data.get('totp_confirmed'):
                    return redirect(url_for('auth.totp_setup'))
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return redirect(url_for('logout'))
