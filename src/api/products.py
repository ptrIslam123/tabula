from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Product, ProductStatus
from datetime import datetime

products_bp = Blueprint('products', __name__, url_prefix='/api')


# ====================================================================
# 1. ПОЛУЧЕНИЕ ВСЕХ ТОВАРОВ
# ====================================================================
@products_bp.route('/products', methods=['GET'])
def get_all_products():
    """
    Получение списка всех товаров.
    Доступно без авторизации.
    
    ЗАПРОС (браузер):
        http://localhost:5000/api/products
    
    ЗАПРОС (curl):
        curl -X GET http://localhost:5000/api/products
    
    ОТВЕТ (200 OK):
        {
            "products": [
                {
                    "product_id": 1,
                    "name": "iPhone 15 Pro",
                    "price": 999.99,
                    "quantity": 10,
                    "seller_id": 1,
                    "status_id": 1,
                    "created_at": "2026-06-14T10:00:00"
                }
            ],
            "count": 1
        }
    """
    products = Product.query.all()
    return jsonify({
        "products": [{
            "product_id": p.product_id,
            "name": p.name,
            "price": float(p.price),
            "quantity": p.quantity,
            "seller_id": p.seller_id,
            "status_id": p.status_id,
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in products],
        "count": len(products)
    })


# ====================================================================
# 2. ПОЛУЧЕНИЕ ТОВАРА ПО ID
# ====================================================================
@products_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    """
    Получение детальной информации о конкретном товаре.
    Доступно без авторизации.
    
    ЗАПРОС (браузер):
        GET http://localhost:5000/api/products/1
    
    ЗАПРОС (curl):
        curl -X GET http://localhost:5000/api/products/1
    
    ОТВЕТ (200 OK):
        {
            "product_id": 1,
            "name": "iPhone 15 Pro",
            "description": "Отличный телефон",
            "price": 999.99,
            "quantity": 10,
            "seller_id": 1,
            "status_id": 1,
            "media_dir_url": "/uploads/products/1/",
            "created_at": "2026-06-14T10:00:00",
            "updated_at": "2026-06-14T10:00:00"
        }
    
    ОТВЕТ (404 Not Found):
        {"error": "Товар не найден"}
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Товар не найден"}), 404
    
    return jsonify({
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "quantity": product.quantity,
        "seller_id": product.seller_id,
        "status_id": product.status_id,
        "media_dir_url": product.media_dir_url,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None
    })


# ====================================================================
# 3. СОЗДАНИЕ НОВОГО ТОВАРА (ТОЛЬКО ДЛЯ АВТОРИЗОВАННЫХ)
# ====================================================================
@products_bp.route('/products', methods=['POST'])
@login_required
def create_product():
    """
    Создание нового товара. Требует авторизации.
    Товар привязывается к текущему авторизованному пользователю.
    
    ЗАПРОС (curl с cookie):
        curl -X POST http://localhost:5000/api/products \
          -H "Content-Type: application/json" \
          -H "Cookie: session=eyJsb2dnZWRfaW4iOnRydWV9.xxxxx" \
          -d '{
            "name": "iPhone 15 Pro",
            "description": "Отличный телефон",
            "price": 999.99,
            "quantity": 10,
            "status_id": 1,
            "media_dir_url": "/uploads/products/1/"
          }'
    
    ОБЯЗАТЕЛЬНЫЕ ПОЛЯ:
        - name (string) - название товара
        - price (number) - цена (должна быть > 0)
    
    ОПЦИОНАЛЬНЫЕ ПОЛЯ:
        - description (string) - описание
        - quantity (integer) - количество (по умолчанию 0)
        - status_id (integer) - статус (по умолчанию 1 = 'new')
        - media_dir_url (string) - путь к папке с медиа
    
    ОТВЕТ (201 Created):
        {
            "message": "Товар успешно создан",
            "product": {
                "product_id": 1,
                "name": "iPhone 15 Pro",
                "price": 999.99
            }
        }
    
    ОТВЕТ (400 Bad Request):
        {"error": "Поле 'name' обязательно"}
        {"error": "Цена должна быть больше 0"}
        {"error": "Цена должна быть числом"}
    """
    data = request.get_json()
    
    # Валидация обязательных полей
    required_fields = ['name', 'price']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Поле '{field}' обязательно"}), 400
    
    # Валидация цены
    try:
        price = float(data['price'])
        if price <= 0:
            return jsonify({"error": "Цена должна быть больше 0"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Цена должна быть числом"}), 400
    
    # Создаём товар
    product = Product(
        seller_id=current_user.user_id,
        status_id=data.get('status_id', 1),
        name=data['name'],
        description=data.get('description', ''),
        price=price,
        quantity=data.get('quantity', 0),
        media_dir_url=data.get('media_dir_url')
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({
        "message": "Товар успешно создан",
        "product": {
            "product_id": product.product_id,
            "name": product.name,
            "price": float(product.price)
        }
    }), 201


# ====================================================================
# 4. ПОЛУЧЕНИЕ ТОВАРОВ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ
# ====================================================================
@products_bp.route('/my/products', methods=['GET'])
@login_required
def get_my_products():
    """
    Получение всех товаров, которые добавил текущий авторизованный пользователь.
    
    ЗАПРОС (браузер):
        http://localhost:5000/api/my/products
    
    ЗАПРОС (curl):
        curl -X GET http://localhost:5000/api/my/products \
          -H "Cookie: session=eyJsb2dnZWRfaW4iOnRydWV9.xxxxx"
    
    ОТВЕТ (200 OK):
        {
            "products": [
                {
                    "product_id": 1,
                    "name": "iPhone 15 Pro",
                    "price": 999.99,
                    "quantity": 10,
                    "status_id": 1,
                    "created_at": "2026-06-14T10:00:00"
                }
            ],
            "count": 1
        }
    """
    products = current_user.products.all()
    return jsonify({
        "products": [{
            "product_id": p.product_id,
            "name": p.name,
            "price": float(p.price),
            "quantity": p.quantity,
            "status_id": p.status_id,
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in products],
        "count": len(products)
    })


# ====================================================================
# 5. ОБНОВЛЕНИЕ ТОВАРА (ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА)
# ====================================================================
@products_bp.route('/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    """
    Обновление товара. Только владелец товара может его редактировать.
    
    ЗАПРОС (curl):
        curl -X PUT http://localhost:5000/api/products/1 \
          -H "Content-Type: application/json" \
          -H "Cookie: session=eyJsb2dnZWRfaW4iOnRydWV9.xxxxx" \
          -d '{
            "name": "iPhone 15 Pro Max",
            "price": 1199.99,
            "quantity": 5
          }'
    
    ЗАПРОС (браузер через fetch):
        fetch('/api/products/1', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({
                name: 'iPhone 15 Pro Max',
                price: 1199.99,
                quantity: 5
            })
        })
    
    ДОПУСТИМЫЕ ПОЛЯ ДЛЯ ОБНОВЛЕНИЯ:
        - name (string)
        - description (string)
        - price (number, >0)
        - quantity (integer, >=0)
        - status_id (integer)
        - media_dir_url (string)
    
    ОТВЕТ (200 OK):
        {
            "message": "Товар успешно обновлён",
            "product": {
                "product_id": 1,
                "name": "iPhone 15 Pro Max",
                "price": 1199.99,
                "quantity": 5,
                "status_id": 1,
                "updated_at": "2026-06-14T11:00:00"
            }
        }
    
    ОТВЕТ (403 Forbidden):
        {"error": "Вы не можете редактировать чужой товар"}
    
    ОТВЕТ (404 Not Found):
        {"error": "Товар не найден"}
    """
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({"error": "Товар не найден"}), 404
    
    # Проверка прав: только владелец
    if product.seller_id != current_user.user_id:
        return jsonify({"error": "Вы не можете редактировать чужой товар"}), 403
    
    data = request.get_json()
    
    # Обновляем поля
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        try:
            price = float(data['price'])
            if price <= 0:
                return jsonify({"error": "Цена должна быть больше 0"}), 400
            product.price = price
        except (ValueError, TypeError):
            return jsonify({"error": "Цена должна быть числом"}), 400
    if 'quantity' in data:
        try:
            quantity = int(data['quantity'])
            if quantity < 0:
                return jsonify({"error": "Количество не может быть отрицательным"}), 400
            product.quantity = quantity
        except (ValueError, TypeError):
            return jsonify({"error": "Количество должно быть целым числом"}), 400
    if 'status_id' in data:
        status = ProductStatus.query.get(data['status_id'])
        if not status:
            return jsonify({"error": f"Статус с id={data['status_id']} не найден"}), 400
        product.status_id = data['status_id']
    if 'media_dir_url' in data:
        product.media_dir_url = data['media_dir_url']
    
    product.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "message": "Товар успешно обновлён",
        "product": {
            "product_id": product.product_id,
            "name": product.name,
            "price": float(product.price),
            "quantity": product.quantity,
            "status_id": product.status_id,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None
        }
    }), 200


# ====================================================================
# 6. УДАЛЕНИЕ ТОВАРА (ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА)
# ====================================================================
@products_bp.route('/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """
    Удаление товара. Только владелец товара может его удалить.
    
    ЗАПРОС (curl):
        curl -X DELETE http://localhost:5000/api/products/1 \
          -H "Cookie: session=eyJsb2dnZWRfaW4iOnRydWV9.xxxxx"
    
    ЗАПРОС (браузер через fetch):
        fetch('/api/products/1', {
            method: 'DELETE',
            credentials: 'include'
        })
    
    ОТВЕТ (200 OK):
        {"message": "Товар успешно удалён"}
    
    ОТВЕТ (403 Forbidden):
        {"error": "Вы не можете удалить чужой товар"}
    
    ОТВЕТ (404 Not Found):
        {"error": "Товар не найден"}
    """
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({"error": "Товар не найден"}), 404
    
    # Проверка прав: только владелец
    if product.seller_id != current_user.user_id:
        return jsonify({"error": "Вы не можете удалить чужой товар"}), 403
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({"message": "Товар успешно удалён"}), 200