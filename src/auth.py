from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized
from flask_login import login_user
from models import db, User
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

def init_google_auth(app):
    google_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        scope=["profile", "email"]
    )
    app.register_blueprint(google_bp, url_prefix="/login")
    return google_bp

def setup_auth_handlers(google_bp):
    @oauth_authorized.connect_via(google_bp)
    def google_logged_in(blueprint, token):
        if not token:
            print("Не удалось получить токен")
            return False
        
        resp = blueprint.session.get("/oauth2/v2/userinfo")
        if not resp.ok:
            print("Не удалось получить данные пользователя")
            return False
        
        user_info = resp.json()
        email = user_info.get("email")
        google_id = user_info.get("id")
        
        if not email:
            print("Не получен email от Google")
            return False
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            user = User(email=email, google_id=google_id)
            db.session.add(user)
            db.session.commit()
            print(f"[НОВЫЙ ПОЛЬЗОВАТЕЛЬ] ({email})")
        else:
            print(f"[СУЩЕСТВУЮЩИЙ] ({email})")
        
        login_user(user, remember=True)
        print(f"[АВТОРИЗОВАН] user_id={user.user_id}")
        
        return True