from datetime import date
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.extensions import db
import calendar
from sqlalchemy import func
from datetime import datetime, date

from flask import Blueprint, request, jsonify
from .auth_decorator import token_required
from app.services.parser_service import parse_order_text

order_bp = Blueprint('order', __name__, url_prefix='/api')

@order_bp.route('/parse_order', methods=['POST'])
@token_required
def parse_order_endpoint(current_user):
    # 从请求体中直接获取原始文本
    text_content = request.get_data(as_text=True)
    if not text_content:
        return jsonify({"message": "请求体不能为空"}), 400

    # 调用我们的“大脑”函数进行解析
    parsed_data = parse_order_text(text_content)

    return jsonify(parsed_data)


@order_bp.route('/save_order', methods=['POST'])
@token_required
def save_order_endpoint(current_user):
    data = request.get_json()
    # 【后端验证】如果请求数据为空，或者产品列表为空
    if not data or not data.get('order_items'):
        return jsonify({"code": 400, "message": "无效订单，必须包含产品项"}), 400


    # 为了保证数据一致性，使用数据库事务
    # === 请用这个版本替换掉 order_api.py 中原有的 try...except 代码块 ===
    try:
        # --- 1. 进行最终计算 ---
        total_order_amount = sum(float(item['item_amount']) for item in data['order_items'])
        total_gifting_cost = sum(float(item['item_gifting_cost']) for item in data['order_items'])

        total_commission = 0.0 # 初始化为浮点数
        for item in data['order_items']:
            product = Product.query.filter_by(name=item['product_name']).first()
            if product:
                # 【修改点】在这里，我们将Decimal类型的提成强制转换为float类型
                total_commission += float(product.commission_per_item) * int(item['quantity'])

        # 净收入预估 = 总提成 + 陈列费 - 旧货处理费 - 搭赠费用
        net_income_estimate = (total_commission + 
                                float(data.get('display_fee', 0)) - 
                                float(data.get('old_goods_disposal_fee', 0)) - 
                                total_gifting_cost)

        # --- 2. 创建Order主记录 ---
        new_order = Order(
            user_id=current_user.id,
            order_date=date.today(),
            customer_name=data['customer_name'],
            original_text=data.get('original_text', ''),
            total_order_amount=total_order_amount,
            total_commission=total_commission,
            display_fee=data.get('display_fee', 0),
            old_goods_disposal_fee=data.get('old_goods_disposal_fee', 0),
            gifting_cost=total_gifting_cost,
            net_income_estimate=net_income_estimate
        )
        db.session.add(new_order)
        db.session.flush()

        # --- 3. 创建所有OrderItem子记录 ---
        for item_data in data['order_items']:
            product = Product.query.filter_by(name=item_data['product_name']).first()
            if product:
                new_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    product_name=item_data['product_name'],
                    quantity=item_data['quantity'],
                    actual_unit_price=item_data['actual_unit_price'],
                    item_amount=item_data['item_amount'],
                    item_gifting_cost=item_data['item_gifting_cost']
                )
                db.session.add(new_item)

        # --- 4. 提交事务，将所有数据写入数据库 ---
        db.session.commit()

        return jsonify({'message': '订单保存成功', 'order_id': new_order.id}), 201

    except Exception as e:
        db.session.rollback()
        # 打印详细错误到控制台，方便调试
        print(f"Error occurred: {e}") 
        return jsonify({'message': '保存失败，服务器内部错误', 'error': str(e)}), 500
    


# === 请用这个新版本替换旧的 get_daily_summary 函数 ===
@order_bp.route('/daily_summary', methods=['GET'])
@token_required
def get_daily_summary(current_user):
    request_date_str = request.args.get('date')
    try:
        target_date = datetime.strptime(request_date_str, '%Y-%m-%d').date() if request_date_str else date.today()
    except (ValueError, TypeError):
        target_date = date.today()
    summary_orders = db.session.query(
        func.count(Order.id).label('total_order_count'), func.sum(Order.total_commission).label('total_commission'),
        func.sum(Order.display_fee).label('total_display_fee'), func.sum(Order.old_goods_disposal_fee).label('total_old_goods_disposal_fee'),
        func.sum(Order.gifting_cost).label('total_gifting_cost')
    ).filter(Order.user_id == current_user.id, Order.order_date == target_date).first()
    total_items_query = db.session.query(func.sum(OrderItem.quantity)).join(Order).filter(
        Order.user_id == current_user.id, Order.order_date == target_date
    ).scalar()
    summary_data = {
        'total_order_count': summary_orders.total_order_count or 0,
        'total_commission': float(summary_orders.total_commission or 0.0),
        'total_display_fee': float(summary_orders.total_display_fee or 0.0),
        'total_old_goods_disposal_fee': float(summary_orders.total_old_goods_disposal_fee or 0.0),
        'total_gifting_cost': float(summary_orders.total_gifting_cost or 0.0),
        'total_item_count': int(total_items_query or 0)
    }
    return jsonify(summary_data)


@order_bp.route('/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(20).all()
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


# --- 【新增】获取单个订单详情的API，用于详情页 ---
@order_bp.route('/order/<int:order_id>', methods=['GET'])
@token_required
def get_order_detail(current_user, order_id):

    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    total_item_count = sum(item.quantity for item in order.items)
    order_detail = {
        'id': order.id, 'customer_name': order.customer_name, 'order_date': order.order_date.strftime('%Y-%m-%d'),
        'original_text': order.original_text, 'total_commission': float(order.total_commission),
        'display_fee': float(order.display_fee), 'old_goods_disposal_fee': float(order.old_goods_disposal_fee),
        'gifting_cost': float(order.gifting_cost), 'total_item_count': total_item_count,
        'items': []
    }
    for item in order.items:
        product = Product.query.get(item.product_id)
        item_commission = float(product.commission_per_item) * item.quantity if product else 0
        order_detail['items'].append({
            'product_name': item.product_name, 'quantity': item.quantity,
            'actual_unit_price': float(item.actual_unit_price),
            'item_commission': item_commission
        })
    return jsonify(order_detail)
# === 请用这个修正后的版本，完整替换旧的 get_monthly_summary 函数 ===

# === 在 order_api.py 中，用这个正确的版本替换旧的 get_monthly_summary 函数 ===
@order_bp.route('/monthly_summary', methods=['GET'])
@token_required
def get_monthly_summary(current_user):
    # 1. 解析前端传来的 "YYYY-MM" 格式的月份参数
    month_str = request.args.get('month')
    if not month_str:
        return jsonify({"code": 400, "message": "必须提供月份参数"}), 400

    try:
        year, month = map(int, month_str.split('-'))
        # 2. 计算出该月的第一天和最后一天
        _, last_day_of_month = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day_of_month)
    except (ValueError, TypeError):
        return jsonify({"code": 400, "message": "月份参数格式不正确，应为YYYY-MM"}), 400

    # 3. 聚合查询订单主表
    summary_orders = db.session.query(
        func.count(Order.id).label('total_order_count'),
        func.sum(Order.total_commission).label('total_commission'),
        func.sum(Order.display_fee).label('total_display_fee'),
        func.sum(Order.old_goods_disposal_fee).label('total_old_goods_disposal_fee'),
        func.sum(Order.gifting_cost).label('total_gifting_cost')
    ).filter(
        Order.user_id == current_user.id,
        Order.order_date.between(start_date, end_date)
    ).first()

    # 4. 单独查询总件数
    total_items_query = db.session.query(func.sum(OrderItem.quantity)).join(Order).filter(
        Order.user_id == current_user.id,
        Order.order_date.between(start_date, end_date)
    ).scalar()

    # 5. 处理查询结果为空的情况
    if not summary_orders or summary_orders.total_order_count == 0:
        summary_data = {
            'total_order_count': 0, 'total_commission': 0.0, 'total_display_fee': 0.0,
            'total_old_goods_disposal_fee': 0.0, 'total_gifting_cost': 0.0, 'total_item_count': 0
        }
    else:
        summary_data = {
            'total_order_count': summary_orders.total_order_count,
            'total_commission': float(summary_orders.total_commission or 0.0),
            'total_display_fee': float(summary_orders.total_display_fee or 0.0),
            'total_old_goods_disposal_fee': float(summary_orders.total_old_goods_disposal_fee or 0.0),
            'total_gifting_cost': float(summary_orders.total_gifting_cost or 0.0),
            'total_item_count': int(total_items_query or 0)
        }

    return jsonify(summary_data)