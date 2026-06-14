from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import User

users_bp = Blueprint('users', __name__, url_prefix='/api')

@users_bp.route('/me')
@login_required
def get_current_user():
    return jsonify({
        "user_id": current_user.user_id,
        "email": current_user.email,
        "google_id": current_user.google_id,
        "location": current_user.location,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    })


@users_bp.route('/user/<string:email>')
@login_required
def get_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Пользователь не найден", "email": email}), 404
    
    return jsonify({
        "user_id": user.user_id,
        "email": user.email,
        "google_id": user.google_id,
        "location": user.location,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "products_count": user.products.count()
    })