from app import create_app

# 调用应用工厂，创建app实例
app = create_app()

# 当直接运行此文件时，启动开发服务器
if __name__ == '__main__':
    app.run()