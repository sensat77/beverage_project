from app.extensions import db
import bcrypt

class User(db.Model):
    # 定义表名
    __tablename__ = 'users'

    # 定义列（字段）
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def set_password(self, password):
        """设置密码，将明文密码哈希后存储。"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """校验密码是否正确。"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))