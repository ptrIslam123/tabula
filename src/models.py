
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
    media_url = db.Column(db.String(255))
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
