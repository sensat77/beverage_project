from flask import Flask
from flask_cors import CORS
from config import Config
from .extensions import db, migrate
# 导入模型，确保SQLAlchemy能找到它们
from .models import user, product, order, user_setting  # <--- 修改这一行

def create_app(config_class=Config):
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 从配置对象中加载配置
    app.config.from_object(config_class)

    CORS(app)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    # 导入模型，确保SQLAlchemy能找到它们
    #from .models import user

    # 注册蓝图（我们后面会在这里添加API路由）
    # 从我们刚创建的文件中导入auth_bp蓝图
    from .routes.auth import auth_bp
    # 在app上注册这个蓝图
    app.register_blueprint(auth_bp)

    # 导入并注册 product 蓝图
    from .routes.product_api import product_bp
    app.register_blueprint(product_bp)

    from .routes.order_api import order_bp
    app.register_blueprint(order_bp)

    # 导入并注册 report_bp 蓝图
    from .routes.report_api import report_bp
    app.register_blueprint(report_bp)

    return app

