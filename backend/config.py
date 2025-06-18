import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'

    # === 修改这里，使用云托管提供的独立MySQL环境变量构建连接字符串 ===
    MYSQL_HOST = os.environ.get('MYSQL_ADDRESS', '10.11.108.194:3306')
    MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '7uxSMRDG') # 注意：本地测试时使用默认值，生产环境会取环境变量
    # 从 MYSQL_ADDRESS 中分离出端口，如果它包含了端口
    if ':' in MYSQL_HOST:
        MYSQL_HOST_PARSED, MYSQL_PORT = MYSQL_HOST.split(':')
    else:
        MYSQL_HOST_PARSED = MYSQL_HOST
        MYSQL_PORT = '3306' # MySQL默认端口

    # 云托管的数据库名通常是固定的 'tencentdb' 或您创建时指定的
    # 请在云托管数据库详情页确认数据库名，或者如果未指定，通常是自动创建的默认库
    # 这里我假设默认库名为 'beverage_db'，如果不是请替换
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'beverage_db') # 假设您的数据库名仍为 beverage_db

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST_PARSED}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    # ================================================================

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))