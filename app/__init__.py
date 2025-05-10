import os
from flask import Flask
from flask_login import LoginManager
from .config import Config

login_manager = LoginManager()
login_manager.login_view = 'auth.login' # 指向登录路由的蓝图名称.函数名
login_manager.login_message = "请登录以访问此页面。"
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    login_manager.init_app(app)

    # 确保上传文件夹存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'])
        except OSError as e:
            app.logger.error(f"错误：无法创建上传目录 {app.config['UPLOAD_FOLDER']}: {e}")
            # 根据需要，您可能希望在此处引发异常或退出

    # 注册蓝图
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .routes import bp as main_bp
    app.register_blueprint(main_bp) # 主蓝图可以没有前缀

    # 确保 models 被导入，以便 user_loader 被注册
    from . import models 

    return app

