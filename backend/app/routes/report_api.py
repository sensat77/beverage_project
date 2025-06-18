# /backend/app/routes/report_api.py (功能完整版)

from flask import Blueprint, request, jsonify
from sqlalchemy import func, extract, distinct
from datetime import datetime
from app.extensions import db
from app.models.order import Order, OrderItem
from .auth_decorator import token_required

report_bp = Blueprint('report', __name__, url_prefix='/api/reports')

# API 1: 获取指定月份每日的业绩分解
@report_bp.route('/daily_breakdown', methods=['GET'])
@token_required
def get_daily_breakdown(current_user):
    month_str = request.args.get('month')
    if not month_str:
        return jsonify([])
    try:
        year, month = map(int, month_str.split('-'))
    except (ValueError, TypeError):
        return jsonify([])

    daily_summaries = db.session.query(
        extract('day', Order.order_date).label('day'),
        func.count(db.distinct(Order.id)).label('order_count'),
        func.sum(OrderItem.quantity).label('item_count')
    ).join(OrderItem, Order.id == OrderItem.order_id)\
     .filter(Order.user_id == current_user.id, extract('year', Order.order_date) == year, extract('month', Order.order_date) == month)\
     .group_by(extract('day', Order.order_date))\
     .order_by(extract('day', Order.order_date).desc())\
     .all()
    
    return jsonify([{'day': s.day, 'order_count': s.order_count, 'item_count': int(s.item_count or 0)} for s in daily_summaries])

# API 2: 获取指定日期的订单列表
@report_bp.route('/orders_by_date', methods=['GET'])
@token_required
def get_orders_by_date(current_user):
    date_str = request.args.get('date')
    if not date_str:
        return jsonify([])
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify([])

    orders = Order.query.filter_by(user_id=current_user.id, order_date=target_date).order_by(Order.id.desc()).all()
    order_list = []
    for order in orders:
        total_item_count = sum(item.quantity for item in order.items)
        order_list.append({
            'id': order.id,
            'customer_name': order.customer_name,
            'order_date': order.order_date.strftime('%Y-%m-%d'),
            'total_item_count': total_item_count,
            'total_commission': float(order.total_commission)
        })
    return jsonify(order_list)

# --- 【缺失的功能】请确保您的文件中有下面这个删除订单的函数 ---
# API 3: 删除一个订单
@report_bp.route('/order/<int:order_id>', methods=['DELETE'])
@token_required
def delete_order(current_user, order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': '订单删除成功'})

# API 4: 获取指定日期重点产品售卖件数和家数 (用于首页展示)
@report_bp.route('/top_product_sales', methods=['GET'])
@token_required
def get_top_product_sales(current_user):
    date_str = request.args.get('date')
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
    except ValueError:
        return jsonify([]) # 日期格式错误返回空列表

    # 查询逻辑：按产品名称分组，统计总件数和涉及的客户家数
    top_products = db.session.query(
        OrderItem.product_name,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.count(distinct(Order.customer_name)).label('customer_count') # 统计去重后的客户名称数量
    ).join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.user_id == current_user.id, Order.order_date == target_date)\
     .group_by(OrderItem.product_name)\
     .order_by(func.sum(OrderItem.quantity).desc())\
     .limit(5)\
     .all()
    
    # 转换为字典列表
    result_list = []
    for p in top_products:
        result_list.append({
            'product_name': p.product_name,
            'total_quantity': int(p.total_quantity or 0), # 确保是整数
            'customer_count': int(p.customer_count or 0) # 确保是整数
        })
    
    return jsonify(result_list)