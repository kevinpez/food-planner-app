"""
Auth0 integration service for authentication and authorization
"""

import json
from functools import wraps
from urllib.parse import urlencode, quote_plus
from authlib.integrations.flask_client import OAuth
from flask import current_app, session, request, redirect, url_for, jsonify, g
from jose import jwt
from models import db, User


def init_auth0(app):
    """Initialize Auth0 OAuth client"""
    oauth = OAuth(app)
    
    auth0 = oauth.register(
        'auth0',
        client_id=app.config['AUTH0_CLIENT_ID'],
        client_secret=app.config['AUTH0_CLIENT_SECRET'],
        server_metadata_url=f'https://{app.config["AUTH0_DOMAIN"]}/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid profile email',
        },
    )
    
    return auth0


def get_auth0_client():
    """Get Auth0 client from current app"""
    if not hasattr(current_app, 'auth0_client'):
        current_app.auth0_client = init_auth0(current_app)
    return current_app.auth0_client


def get_user_from_session():
    """Get user from session and database"""
    if 'user' not in session:
        return None
    
    auth0_user_id = session['user'].get('sub')
    if not auth0_user_id:
        return None
    
    user = User.get_by_auth0_id(auth0_user_id)
    return user


def create_or_update_user(auth0_user_info):
    """Create or update user from Auth0 profile"""
    auth0_user_id = auth0_user_info['sub']
    user = User.get_by_auth0_id(auth0_user_id)
    
    if user:
        # Update existing user profile
        user.email = auth0_user_info['email']
        user.name = auth0_user_info.get('name', auth0_user_info['email'])
        user.picture_url = auth0_user_info.get('picture')
    else:
        # Create new user
        user = User.create_from_auth0(auth0_user_info)
        db.session.add(user)
    
    db.session.commit()
    return user


def requires_auth(f):
    """Auth0 authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_user_from_session()
        if not user:
            return redirect(url_for('auth.login'))
        
        # Set current user in g for access in views
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated


def get_current_user():
    """Get current authenticated user"""
    return getattr(g, 'current_user', None)


def get_auth0_login_url():
    """Generate Auth0 login URL"""
    auth0_client = get_auth0_client()
    redirect_uri = url_for('auth.callback', _external=True)
    return auth0_client.authorize_redirect(redirect_uri=redirect_uri)


def get_auth0_logout_url():
    """Generate Auth0 logout URL"""
    params = {
        'returnTo': url_for('index', _external=True),
        'client_id': current_app.config['AUTH0_CLIENT_ID']
    }
    return f"https://{current_app.config['AUTH0_DOMAIN']}/v2/logout?" + urlencode(params)


def handle_auth0_callback():
    """Handle Auth0 callback and create/update user"""
    auth0_client = get_auth0_client()
    
    try:
        # Get tokens from Auth0
        token = auth0_client.authorize_access_token()
        
        # Get user info from token
        user_info = token.get('userinfo')
        if not user_info:
            # If userinfo is not in token, fetch it
            resp = auth0_client.parse_id_token(token)
            user_info = resp
        
        # Store user info in session
        session['user'] = user_info
        
        # Create or update user in database
        user = create_or_update_user(user_info)
        
        # Check if this is a new user for demo data generation
        is_new_user = user.created_at.timestamp() > (user_info.get('updated_at', 0))
        
        return user, is_new_user
        
    except Exception as e:
        current_app.logger.error(f"Auth0 callback error: {str(e)}")
        return None, False


def clear_session():
    """Clear user session"""
    session.clear()


def validate_jwt_token(token):
    """Validate JWT token from Auth0 (for API endpoints)"""
    try:
        # Get public key from Auth0
        jwks_url = f"https://{current_app.config['AUTH0_DOMAIN']}/.well-known/jwks.json"
        
        # Decode and validate token
        payload = jwt.decode(
            token,
            jwks_url,
            algorithms=['RS256'],
            audience=current_app.config['AUTH0_AUDIENCE'],
            issuer=f"https://{current_app.config['AUTH0_DOMAIN']}/"
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTClaimsError:
        return None
    except Exception:
        return None