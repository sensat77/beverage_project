# backend/app/routes/report_api.py

from flask import Blueprint, request, jsonify
from sqlalchemy import func, extract, distinct
from datetime import datetime, timedelta
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user_setting import UserSetting
from .auth_decorator import token_required

report_bp = Blueprint('report', __name__, url_prefix='/api/reports')

# API 1: 获取指定月份每日的业绩分解 (保持不变)
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

# API 2: 获取指定日期的订单列表 (保持不变)
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

# API 4: 获取用户选择的重点产品售卖件数和家数
@report_bp.route('/top_product_sales', methods=['GET'])
@token_required
def get_top_product_sales(current_user):
    date_str = request.args.get('date')
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
    except ValueError:
        return jsonify({"code": 400, "message": "日期格式不正确"}), 400

    yesterday = target_date - timedelta(days=1)

    # 获取用户自定义的重点产品列表
    user_setting = UserSetting.query.filter_by(user_id=current_user.id).first()
    selected_product_names = []
    if user_setting and user_setting.selected_top_products:
        selected_product_names = [name.strip() for name in user_setting.selected_top_products.split(',') if name.strip()]

    # 如果用户未设置或设置为空，则默认返回销量前5的产品
    if not selected_product_names:
        # 查询今日销量前5的产品作为默认
        default_top_products_query = db.session.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label('sales_count')
        ).join(Order, Order.id == OrderItem.order_id)\
        .filter(Order.user_id == current_user.id, Order.order_date == target_date)\
        .group_by(OrderItem.product_name)\
        .order_by(func.sum(OrderItem.quantity).desc())\
        .limit(5)\
        .all()
        selected_product_names = [p.product_name for p in default_top_products_query]
        # 如果依然为空，直接返回空列表
        if not selected_product_names:
            return jsonify({"code": 200, "message": "暂无重点产品数据", "data": []})


    # 查询今日选定重点产品销售数据
    today_products_query = db.session.query(
        OrderItem.product_name,
        func.sum(OrderItem.quantity).label('sales_count'),
        func.count(distinct(Order.customer_name)).label('customer_count')
    ).join(Order, Order.id == OrderItem.order_id)\
     .filter(
        Order.user_id == current_user.id,
        Order.order_date == target_date,
        OrderItem.product_name.in_(selected_product_names) # 根据用户选择的产品名称筛选
     ).group_by(OrderItem.product_name).all()

    today_products_map = {p.product_name: {'sales_count': int(p.sales_count or 0), 'customer_count': int(p.customer_count or 0)} for p in today_products_query}

    # 查询昨日选定重点产品销售数据
    yesterday_sales_map = {}
    if selected_product_names:
        yesterday_top_products_query = db.session.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label('sales_count')
        ).join(Order, Order.id == OrderItem.order_id)\
         .filter(
            Order.user_id == current_user.id,
            Order.order_date == yesterday,
            # 仅查询用户选择的产品，提高效率
            OrderItem.product_name.in_(selected_product_names) 
         ).group_by(OrderItem.product_name).all()

        for item in yesterday_top_products_query:
            yesterday_sales_map[item.product_name] = int(item.sales_count or 0)

    result_list = []
    # 遍历用户选择的产品名称，确保即使今日无销量也显示，并保持用户选择的顺序（如果需要）
    # 这里我们按用户选择的顺序进行遍历，而不是按今日销量排序
    for product_name in selected_product_names:
        sales_count = today_products_map.get(product_name, {}).get('sales_count', 0)
        customer_count = today_products_map.get(product_name, {}).get('customer_count', 0)
        last_day_sales_count = yesterday_sales_map.get(product_name, 0)
        
        sales_change_percentage = 0.0
        if last_day_sales_count > 0:
            sales_change_percentage = ((sales_count - last_day_sales_count) / last_day_sales_count) * 100
        elif sales_count > 0:
            sales_change_percentage = 100.0 # 今日有销售，昨日无，视为100%增长
        # else: 今日昨日都无销售，默认为0.0%

        result_list.append({
            'product_name': product_name,
            'total_quantity': sales_count,
            'customer_count': customer_count,
            'last_day_total_quantity': last_day_sales_count,
            'daily_change_percentage': round(sales_change_percentage, 2)
        })
    
    return jsonify({"code": 200, "message": "重点产品销售数据获取成功", "data": result_list})


# 新增 API：保存用户选择的重点产品 (保持不变)
@report_bp.route('/save_selected_products', methods=['POST'])
@token_required
def save_selected_products(current_user):
    data = request.get_json()
    if not data or 'product_names' not in data:
        return jsonify({"code": 400, "message": "请求参数缺失: product_names"}), 400
    
    product_names = data['product_names']
    
    # 将列表转换为逗号分隔的字符串存储
    # 排序是为了保持一致性，但前端传过来的顺序可能更重要，可根据需求调整sorted
    selected_products_str = ",".join(sorted([name.strip() for name in product_names if name.strip()]))

    user_setting = UserSetting.query.filter_by(user_id=current_user.id).first()
    if user_setting:
        user_setting.selected_top_products = selected_products_str
    else:
        user_setting = UserSetting(user_id=current_user.id, selected_top_products=selected_products_str)
        db.session.add(user_setting)
    
    try:
        db.session.commit()
        return jsonify({"code": 200, "message": "用户选择的重点产品保存成功"})
    except Exception as e:
        db.session.rollback()
        # 记录详细错误以便调试
        print(f"Error saving user settings: {e}") 
        return jsonify({"code": 500, "message": f"保存失败: {str(e)}"}), 500