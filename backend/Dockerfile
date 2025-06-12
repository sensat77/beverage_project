# 使用一个官方的、轻量级的Python 3.9镜像作为基础
FROM python:3.9-slim

# 在容器内创建一个工作目录 /app
WORKDIR /app

# 将依赖清单文件复制到容器中
COPY requirements.txt .

# 安装所有Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将您backend目录下的所有其他文件复制到容器中
COPY . .

# 声明容器将对外暴露80端口
EXPOSE 80

# 容器启动时要执行的命令：使用Gunicorn作为生产服务器来运行您的应用
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "2", "run:app"]