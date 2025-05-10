from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash # 虽然我们硬编码，但这是正确做法的占位符
from .models import User, get_user_by_username # 导入 User 类和辅助函数
from .config import Config # 导入配置以获取用户凭据

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.manage_files')) # 'main' 是文件管理蓝图的名称
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 演示用：直接比较硬编码的用户名和密码
        # 在实际应用中，您应该从数据库获取用户并使用 check_password_hash
        user_obj = get_user_by_username(username)

        if user_obj and username == Config.APP_USER and password == Config.APP_PASSWORD:
            login_user(user_obj, remember=request.form.get('remember_me'))
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.manage_files'))
        else:
            flash('无效的用户名或密码。', 'error')
            
    return render_template('login.html', title='登录')

@bp.route('/logout')
def logout():
    logout_user()
    flash('您已成功登出。', 'info')
    return redirect(url_for('auth.login'))

