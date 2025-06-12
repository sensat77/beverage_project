from functools import wraps
from flask import request, jsonify
import jwt
import os
from app.models.user import User

def token_required(f):
    """
    一个用于验证JWT Token的装饰器。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # 1. 检查请求头中是否包含 'Authorization'
        if 'Authorization' in request.headers:
            # 格式通常为 'Bearer <token>'
            auth_header = request.headers['Authorization']
            try:
                # 提取 'Bearer ' 后面的token部分
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token格式不正确!'}), 401

        if not token:
            return jsonify({'message': 'Token缺失!'}), 401

        try:
            # 2. 使用密钥解码Token，验证其有效性
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
            # 3. 从解码后的数据中获取user_id，并查询数据库找到当前用户
            current_user = User.query.get(data['user_id'])
            if not current_user:
                 return jsonify({'message': 'Token无效!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token已过期!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token无效!'}), 401

        # 4. 将查询到的用户信息作为参数传递给被装饰的函数
        return f(current_user, *args, **kwargs)

    return decorated