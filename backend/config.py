import os
from dotenv import load_dotenv

# 定位.env文件的路径
basedir = os.path.abspath(os.path.dirname(__file__))
# 加载.env文件中的环境变量
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """
    配置类，用于存储应用的配置信息。
    """
    # 从环境变量中加载JWT密钥
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # 从环境变量中加载数据库连接字符串
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # 关闭SQLAlchemy的事件通知系统，以节省资源
    SQLALCHEMY_TRACK_MODIFICATIONS = False