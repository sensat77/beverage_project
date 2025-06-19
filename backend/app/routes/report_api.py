# backend/app/routes/report_api.py

from flask import Blueprint, request, jsonify
from sqlalchemy import func, extract, distinct
from datetime import datetime, timedelta # 新增导入 timedelta
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

# API 3: 删除一个订单 (保持不变)
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
        # 如果提供了日期，使用该日期；否则使用今天的日期
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
    except ValueError:
        return jsonify({"code": 400, "message": "日期格式不正确"}), 400 # 日期格式错误返回错误信息

    yesterday = target_date - timedelta(days=1) # 计算昨日日期

    # 查询今日重点产品销售数据
    today_top_products_query = db.session.query(
        OrderItem.product_name,
        func.sum(OrderItem.quantity).label('sales_count'),
        func.count(distinct(Order.customer_name)).label('customer_count') # 统计去重后的客户名称数量
    ).join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.user_id == current_user.id, Order.order_date == target_date)\
     .group_by(OrderItem.product_name)\
     .order_by(func.sum(OrderItem.quantity).desc())\
     .limit(5)\
     .all()
    
    # 将今日数据转换为字典，方便查找
    today_products_map = {}
    for p in today_top_products_query:
        today_products_map[p.product_name] = {
            'sales_count': int(p.sales_count or 0),
            'customer_count': int(p.customer_count or 0)
        }

    # 查询昨日重点产品销售数据 (只查询今日重点产品中包含的产品，减少查询量)
    yesterday_sales_map = {}
    if today_products_map: # 如果今日有重点产品
        yesterday_top_products_query = db.session.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label('sales_count')
        ).join(Order, Order.id == OrderItem.order_id)\
         .filter(
            Order.user_id == current_user.id,
            Order.order_date == yesterday,
            OrderItem.product_name.in_(list(today_products_map.keys())) # 只查询今日重点产品中包含的产品
         ).group_by(OrderItem.product_name).all()

        for item in yesterday_top_products_query:
            yesterday_sales_map[item.product_name] = int(item.sales_count or 0)

    result_list = []
    # 遍历今日重点产品，加入昨日销量和日环比
    for product_name, data in today_products_map.items():
        sales_count = data['sales_count']
        customer_count = data['customer_count']
        
        last_day_sales_count = yesterday_sales_map.get(product_name, 0)
        
        sales_change_percentage = 0.0
        if last_day_sales_count > 0:
            sales_change_percentage = ((sales_count - last_day_sales_count) / last_day_sales_count) * 100
        elif sales_count > 0: # 今日有销售但昨日无销售，视为大幅增长
            sales_change_percentage = 100.0 # 可以根据实际业务定义
        else: # 今日昨日都无销售
            sales_change_percentage = 0.0

        result_list.append({
            'product_name': product_name,
            'total_quantity': sales_count, # 保持 total_quantity 字段名与前端现有使用一致
            'customer_count': customer_count,
            'last_day_total_quantity': last_day_sales_count, # 新增字段：昨日总件数
            'daily_change_percentage': round(sales_change_percentage, 2) # 新增字段：日环比百分比
        })
    
    # 返回统一的 success/data/message 格式
    return jsonify({"code": 200, "message": "重点产品数据获取成功", "data": result_list})