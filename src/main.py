from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from models import db, User, ProductStatus
from config import Config
from auth import init_google_auth, setup_auth_handlers
from api.users import users_bp
from api.products import products_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Инициализация БД
    db.init_app(app)
    
    # Инициализация Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "google.login"
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Регистрация API Blueprints
    app.register_blueprint(users_bp)
    app.register_blueprint(products_bp)
    
    # Инициализация Google OAuth
    google_bp = init_google_auth(app)
    setup_auth_handlers(google_bp)
    
    # Создание таблиц и добавление статусов
    with app.app_context():
        db.create_all()
        if ProductStatus.query.count() == 0:
            statuses = ['new', 'used', 'broken', 'inactive', 'out_of_stock']
            for status_name in statuses:
                db.session.add(ProductStatus(status_name=status_name))
            db.session.commit()
            print("✅ Статусы товаров добавлены")
    
    # Маршруты
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return f"""
            <h2>Hello, {current_user.google_id}!</h2>
            <p>Email: {current_user.email}</p>
            <p><strong>Ваш ID: {current_user.user_id}</strong></p>
            <hr>
            <a href="/logout">Выйти</a>
            """
        return '<a href="/login/google">Войти через Google</a>'
    
    @app.route("/logout")
    def logout():
        from flask_login import logout_user
        logout_user()
        return redirect(url_for('index'))
    
    return app


if __name__ == "__main__":
    import time
    time.sleep(3)
    app = create_app()
    print("=" * 50)
    print("Запуск сервера с Google OAuth (Flask-Dance)")
    print("Перейдите на: http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)