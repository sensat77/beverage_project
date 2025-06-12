from flask import Blueprint, request, jsonify
from app.models.product import Product
from app.extensions import db
from .auth_decorator import token_required

product_bp = Blueprint('product', __name__, url_prefix='/api/products')

# 获取所有产品
@product_bp.route('/', methods=['GET'])
@token_required
def get_products(current_user):
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'unit_price': str(p.unit_price), # Decimal类型需要转为字符串
        'commission_per_item': str(p.commission_per_item)
    } for p in products])

# 创建一个新产品
@product_bp.route('/', methods=['POST'])
@token_required
def create_product(current_user):
    data = request.get_json()
    new_product = Product(
        name=data['name'],
        unit_price=data['unit_price'],
        commission_per_item=data['commission_per_item']
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': '产品创建成功'}), 201

# (我们暂时先实现这两个最重要的接口)