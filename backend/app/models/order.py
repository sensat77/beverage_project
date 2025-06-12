from app.extensions import db

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    customer_name = db.Column(db.String(255), nullable=False)
    original_text = db.Column(db.Text, nullable=False)
    total_order_amount = db.Column(db.Numeric(10, 2), nullable=False)
    total_commission = db.Column(db.Numeric(10, 2), nullable=False)
    display_fee = db.Column(db.Numeric(10, 2), default=0.00)
    old_goods_disposal_fee = db.Column(db.Numeric(10, 2), default=0.00)
    gifting_cost = db.Column(db.Numeric(10, 2), nullable=False)
    other_expenses = db.Column(db.Numeric(10, 2), default=0.00)
    net_income_estimate = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # 建立与OrderItem的一对多关系
    items = db.relationship('OrderItem', backref='order', cascade="all, delete-orphan")

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    actual_unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    item_amount = db.Column(db.Numeric(10, 2), nullable=False)
    item_gifting_cost = db.Column(db.Numeric(10, 2), nullable=False)