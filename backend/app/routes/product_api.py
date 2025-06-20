# backend/app/routes/product_api.py
from flask import Blueprint, request, jsonify
from app.models.product import Product
from app.extensions import db
from sqlalchemy import or_ # 新增导入 or_
from .auth_decorator import token_required

product_bp = Blueprint('product', __name__, url_prefix='/api/products')

# 获取所有产品 (包括当前用户自己的产品和公共产品)
@product_bp.route('/', methods=['GET'])
@token_required
def get_products(current_user):
    # 查询当前用户自己的产品 或 user_id 为空的公共产品
    products = Product.query.filter(
        (Product.user_id == current_user.id) | (Product.user_id.is_(None))
    ).all()
    return jsonify([p.to_dict() for p in products])

# 创建一个新产品 (仍然为当前用户创建)
@product_bp.route('/', methods=['POST'])
@token_required
def create_product(current_user):
    data = request.get_json()
    
    # 检查产品名称是否已存在于当前用户下 或 作为公共产品已存在
    # 如果 name 字段是 unique=True，那么所有产品名称都不能重复，无论是私有还是公共
    if Product.query.filter_by(name=data['name']).first():
        return jsonify({"code": 409, "message": "该产品名称已存在"}), 409

    new_product = Product(
        user_id=current_user.id, # 默认创建为当前用户的私有产品
        name=data['name'],
        unit_price=data['unit_price'],
        commission_per_item=data['commission_per_item']
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"code": 201, "message": "产品创建成功", "data": new_product.to_dict()}), 201


# 获取所有产品名称列表 (仅名称，包括当前用户自己的产品和公共产品)
@product_bp.route('/names', methods=['GET'])
@token_required
def get_all_product_names(current_user):
    # 查询当前用户自己的产品名称 或 user_id 为空的公共产品名称
    products = db.session.query(Product.name).filter(
        (Product.user_id == current_user.id) | (Product.user_id.is_(None))
    ).order_by(Product.name).all()
    product_names = [p.name for p in products]
    return jsonify({"code": 200, "message": "所有产品名称获取成功", "data": product_names})