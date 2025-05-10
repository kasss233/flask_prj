import os

# 项目根目录 (上一级目录，因为 config.py 在 app/ 文件夹内)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_very_secret_key_please_change_it'
    UPLOAD_FOLDER_NAME = 'managed_files'
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, UPLOAD_FOLDER_NAME)

    # SQLAlchemy 配置
    # 使用 SQLite 作为示例，您可以更改为 PostgreSQL, MySQL 等
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #     'sqlite:///' + os.path.join(PROJECT_ROOT, 'app.db')
    # 确保 PROJECT_ROOT 指向项目根目录，app.db 将在那里创建
    # 如果您想将数据库文件放在 app 文件夹内：
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #     'sqlite:///' + os.path.join(os.path.dirname(__file__), 'app.db')
    # 为了简单起见，我们将其放在项目根目录
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(PROJECT_ROOT, 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

