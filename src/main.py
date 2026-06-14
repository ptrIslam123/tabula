from flask import Flask, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"

# ========== НАСТРОЙКА GOOGLE ==========
GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
DATABASE_URL = os.environ['DATABASE_URL']


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ========== ПОЛЬЗОВАТЕЛЬ ==========
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    google_id = db.Column(db.String(255), unique=True)
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    products = db.relationship('Product', back_populates='seller', lazy='dynamic')
    
    # Flask-Login требует метод get_id
    def get_id(self):
        return str(self.user_id)

# ========== СТАТУСЫ ТОВАРА (справочник) ==========
class ProductStatus(db.Model):
    __tablename__ = 'product_status'
    
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), unique=True, nullable=False)
    
    # Связи
    products = db.relationship('Product', back_populates='status', lazy='dynamic')

# ========== ТОВАР ==========
class Product(db.Model):
    __tablename__ = 'products'
    
    product_id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('product_status.status_id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    media_dir_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    seller = db.relationship('User', back_populates='products')
    status = db.relationship('ProductStatus', back_populates='products')
    
    # Индексы
    __table_args__ = (
        db.Index('idx_products_seller', 'seller_id'),
        db.Index('idx_products_price', 'price'),
        db.Index('idx_products_status', 'status_id'),
    )


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

    # Добавляем статусы товаров, если их нет
    if ProductStatus.query.count() == 0:
        statuses = ['new', 'used', 'broken', 'inactive', 'out_of_stock']
        for status_name in statuses:
            db.session.add(ProductStatus(status_name=status_name))
        db.session.commit()
        print("✅ Статусы товаров добавлены")


google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["profile", "email"]
)
app.register_blueprint(google_bp, url_prefix="/login")


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
    google_id = user_info.get("id")
    
    if not email:
        print("Не получен email от Google")
        return False
    
    # Ищем пользователя в БД
    user = User.query.filter_by(email=email).first()
    
    if not user:
        user = User(email=email, google_id=google_id)
        db.session.add(user)
        db.session.commit()
        print(f"[НОВЫЙ ПОЛЬЗОВАТЕЛЬ] ({email})")
    else:
        print(f"[СУЩЕСТВУЮЩИЙ] ({email})")

    # Вход в систему через Flask-Login
    login_user(user, remember=True)
    print(f"[АВТОРИЗОВАН] user_id={user.user_id}")

    return True

# ========== МАРШРУТЫ ==========
@app.route("/")
def index():
    if current_user.is_authenticated:
        # После успешной авторизации — приветствие с ID пользователя
        return f"""
        <h2>Hello, {current_user.google_id}!</h2>
        <p>Email: {current_user.email}</p>
        <p><strong>Ваш client ID (user_id): {current_user.user_id}</strong></p>
        <hr>
        <a href="/dashboard">Перейти в профиль</a> | <a href="/logout">Выйти</a>
        """
    return '<a href="/login/google">Войти через Google</a>'

@app.route("/dashboard")
@login_required
def dashboard():
    return f"""
    <h2>Профиль пользователя</h2>
    <p><strong>Client ID:</strong> {current_user.user_id}</p>
    <p><strong>Имя:</strong> {current_user.google_id}</p>
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
