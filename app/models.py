from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager # 从 app/__init__.py 导入 login_manager 和 db
import datetime
import uuid

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # 增加密码哈希长度
    shares = db.relationship('Share', backref='owner', lazy='dynamic', foreign_keys='Share.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_path = db.Column(db.String(512), nullable=False)  # Path relative to user's upload root
    share_token = db.Column(db.String(32), unique=True, nullable=False, index=True)
    is_file = db.Column(db.Boolean, nullable=False) # True for file, False for directory
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Share {self.share_token} for item {self.item_path}>'

    @staticmethod
    def generate_token():
        return uuid.uuid4().hex # 32-character hex string
