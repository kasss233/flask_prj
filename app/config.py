import os

# 项目根目录 (上一级目录，因为 config.py 在 app/ 文件夹内)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_very_secret_key_please_change_it'
    UPLOAD_FOLDER_NAME = 'managed_files'
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, UPLOAD_FOLDER_NAME)

    # 硬编码的用户凭据 (仅用于演示)
    # 在生产环境中，请使用数据库和密码哈希
    APP_USER = "admin"
    APP_PASSWORD = "password123"

