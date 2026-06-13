from flask import Flask, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from werkzeug.security import generate_password_hash
import os

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"

# ========== НАСТРОЙКА GOOGLE ==========
GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
DATABASE_URL = os.environ['DATABASE_URL']


# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["profile", "email"]
)
app.register_blueprint(google_bp, url_prefix="/login")

# ========== МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ ==========
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    google_id = db.Column(db.String(100), unique=True)

# ========== НАСТРОЙКА FLASK-LOGIN ==========
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "google.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========== СОЗДАНИЕ ТАБЛИЦ ==========
with app.app_context():
    db.create_all()

# ========== ОБРАБОТЧИК УСПЕШНОЙ АВТОРИЗАЦИИ ЧЕРЕЗ GOOGLE ==========
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    """Этот код выполняется после успешной авторизации через Google"""
    
    if not token:
        print("Не удалось получить токен")
        return False
    
    # Получаем информацию о пользователе от Google
    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        print("Не удалось получить данные пользователя")
        return False
    
    user_info = resp.json()
    email = user_info.get("email")
    name = user_info.get("name")
    google_id = user_info.get("id")
    
    if not email:
        print("Не получен email от Google")
        return False
    
    # Ищем пользователя в БД
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Создаём нового пользователя
        user = User(email=email, name=name, google_id=google_id)
        db.session.add(user)
        db.session.commit()
        print(f"[НОВЫЙ ПОЛЬЗОВАТЕЛЬ] {name} ({email})")
    else:
        print(f"[СУЩЕСТВУЮЩИЙ] {name} ({email})")
    
    # Вход в систему через Flask-Login
    login_user(user, remember=True)
    print(f"[АВТОРИЗОВАН] user_id={user.id}")
    
    return True

# ========== МАРШРУТЫ ==========
@app.route("/")
def index():
    if current_user.is_authenticated:
        # После успешной авторизации — приветствие с ID пользователя
        return f"""
        <h2>Hello, {current_user.name}!</h2>
        <p>Email: {current_user.email}</p>
        <p><strong>Ваш client ID (user_id): {current_user.id}</strong></p>
        <hr>
        <a href="/dashboard">Перейти в профиль</a> | <a href="/logout">Выйти</a>
        """
    return '<a href="/login/google">Войти через Google</a>'

@app.route("/dashboard")
@login_required
def dashboard():
    return f"""
    <h2>Профиль пользователя</h2>
    <p><strong>Client ID:</strong> {current_user.id}</p>
    <p><strong>Имя:</strong> {current_user.name}</p>
    <p><strong>Email:</strong> {current_user.email}</p>
    <a href="/">На главную</a> | <a href="/logout">Выйти</a>
    """

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    print("=" * 50)
    print("Запуск сервера с Google OAuth (Flask-Dance)")
    print(f"GOOGLE_CLIENT_ID={GOOGLE_CLIENT_ID}\nGOOGLE_CLIENT_SECRET={GOOGLE_CLIENT_SECRET}\n")
    print("Перейдите на: http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
