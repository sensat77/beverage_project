# backend/app/models/product.py
from app.extensions import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, default=None) 
    name = db.Column(db.String(100), unique=True, nullable=False) # 注意：unique=True 可能导致不同用户无法拥有同名产品，如需允许多个用户有同名产品，需改为 unique=False, 并在 name 上加联合唯一索引 (user_id, name)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    commission_per_item = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # 建立与User的关联（可选，但通常有助于ORM操作）
    user = db.relationship('User', backref=db.backref('products', lazy=True))

    def __repr__(self):
        return f"<Product {self.name} (User: {self.user_id})>"

    # 转换为字典，方便JSON序列化
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'unit_price': str(self.unit_price), # Decimal类型需要转为字符串
            'commission_per_item': str(self.commission_per_item),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }