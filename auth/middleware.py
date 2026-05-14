from flask import request, redirect, url_for, g
import jwt
from .tokens import verify_access_token, verify_recovery_cookie, mint_access_token, sign_recovery_cookie
from .user_management import get_user_totp, update_user_activity


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
        if request.endpoint in ['static', 'auth.login', 'auth.register',
                                'health', 'logout', 'auth.reset_password_form',
                                'auth.reset_password_verify',
                                'auth.reset_password_complete', 'auth.try_anonymous']:
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
        # check if the expired JWT is from anon account or from logged in account
        except jwt.ExpiredSignatureError:
            try:
                stale = jwt.decode(
                    token, app.config['JWT_SECRET'], 
                    algorithms=['HS256'],
                    issuer=app.config['JWT_ISSUER'],
                    audience=app.config['JWT_AUDIENCE'],
                    options={"verify_exp": False, "require":["sub"]}
                )
            except jwt.InvalidTokenError:
                return redirect(url_for('logout'))
            if not stale.get('anon'):
                # real account don't swap to annon validation
                return redirect(url_for('logout'))
            
            # is anon account so recover from recovery cookie
            recovery = request.cookies.get('anon_recovery')
            if recovery:
                result = verify_recovery_cookie(recovery)
                if result:
                    user_id, tenant_id = result
                    g.user_id = user_id
                    g.tenant_id = tenant_id
                    g.is_anonymous = True
                    g.username = None
                    g._refresh_session = True
                    return
            return redirect(url_for('logout'))
        except jwt.InvalidTokenError:
            return redirect(url_for('logout'))

        
    @app.after_request
    def refresh_anonymous_session(response):
        if not getattr(g, '_refresh_session', False):
            return response
        
        token = mint_access_token(user_id=g.user_id, tenant_id=g.tenant_id, is_anon = True)
        response.set_cookie("token", token, httponly=True, samesite="Lax", max_age = app.config["JWT_ACCESS_TTL_SECONDS"])
        recovery = sign_recovery_cookie(g.user_id, g.tenant_id)
        response.set_cookie("anon_recovery", recovery, httponly=True, samesite="Lax", max_age = app.config["ANON_RECOVERY_TTL_SECONDS"])
        update_user_activity(g.user_id)
        return response

