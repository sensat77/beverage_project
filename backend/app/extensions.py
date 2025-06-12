from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 创建扩展的实例
db = SQLAlchemy()
migrate = Migrate()