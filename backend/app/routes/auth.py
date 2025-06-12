import jwt
import os
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, request, jsonify
from app.models.user import User
from app.extensions import db

from .auth_decorator import token_required

# 使用蓝图（Blueprint）来组织路由，url_prefix='/api' 表示该蓝图下所有路由都以/api开头
auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册接口"""
    # 1. 从请求中获取JSON数据
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "message": "请求体不能为空"}), 400
    
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"code": 400, "message": "用户名和密码不能为空"}), 400

    # 2. 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        # 409 Conflict: 表示请求的资源与服务器当前状态冲突
        return jsonify({"code": 409, "message": "用户名已存在"}), 409

    # 3. 创建新用户实例并设置哈希后的密码
    new_user = User(username=username)
    new_user.set_password(password)

    # 4. 将新用户添加到数据库会话并提交
    db.session.add(new_user)
    db.session.commit()

    # 5. 返回成功的响应
    return jsonify({"code": 200, "message": "注册成功"})

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录接口"""
    # 1. 从请求中获取JSON数据
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "message": "请求体不能为空"}), 400

    username = data.get('username')
    password = data.get('password')

    # 2. 根据用户名查询用户
    user = User.query.filter_by(username=username).first()

    # 3. 验证用户是否存在以及密码是否正确
    #    为了安全，无论是用户不存在还是密码错误，都返回相同的错误信息
    if not user or not user.check_password(password):
        # 401 Unauthorized: 表示客户端错误，身份验证失败
        return jsonify({"code": 401, "message": "用户名或密码错误"}), 401

    # 4. 验证成功，生成JWT Token
    #    Token的有效期设置为24小时
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    # 使用我们在.env文件中设置的密钥来签名
    token = jwt.encode(payload, os.getenv('JWT_SECRET_KEY'), algorithm="HS256")

    # 5. 返回成功的响应，并带上Token
    return jsonify({
        "code": 200,
        "message": "登录成功",
        "token": token
    })
# 我们稍后会在这里继续添加 /login 登录接口
@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """
    获取用户个人信息接口。
    @token_required 会确保只有携带有效Token的请求才能进入这个函数。
    装饰器会自动将查询到的用户信息 `current_user` 传递进来。
    """
    if not current_user:
        return jsonify({"message": "找不到用户"}), 404
        
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "created_at": current_user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })

# === 在 auth.py 中，用这个正确的版本替换旧的 change_password 函数 ===
@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({"code": 400, "message": "新旧密码均不能为空"}), 400

    # 【关键修正点】使用我们 User 模型自带的 check_password 方法
    if not current_user.check_password(old_password):
        return jsonify({"code": 401, "message": "旧密码错误"}), 401

    # 【关键修正点】使用我们 User 模型自带的 set_password 方法来更新密码
    current_user.set_password(new_password)
    db.session.commit()

    return jsonify({"code": 200, "message": "密码修改成功"})