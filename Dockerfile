FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件到容器
COPY . .

# 设置环境变量
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV SECRET_KEY=your_production_secret_key_change_me

# 创建managed_files目录
RUN mkdir -p managed_files

# 暴露端口
EXPOSE 8085

# 启动应用
CMD ["python", "run.py"]