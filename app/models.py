from flask_login import UserMixin
from . import login_manager # 从 app/__init__.py 导入 login_manager
from .config import Config # 导入配置以获取用户凭据

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# 硬编码用户数据 (仅用于演示)
# 在实际应用中，这应该从数据库加载
users_db = {
    "1": User("1", Config.APP_USER)
}

@login_manager.user_loader
def load_user(user_id):
    return users_db.get(user_id)

def get_user_by_username(username):
    for user_id, user_obj in users_db.items():
        if user_obj.username == username:
            return user_obj
    return None
