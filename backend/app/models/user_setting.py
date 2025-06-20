# backend/app/models/user_setting.py
from app.extensions import db
from datetime import datetime

class UserSetting(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    # 存储用户选择的重点产品名称列表，以逗号分隔的字符串形式
    selected_top_products = db.Column(db.Text, default="")
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 建立与User的一对一关系
    user = db.relationship('User', backref=db.backref('setting', uselist=False))

    def __repr__(self):
        return f"<UserSetting user_id={self.user_id}, products={self.selected_top_products}>"