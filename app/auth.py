from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, current_user
from .models import User
from . import db

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.manage_files'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember_me'))
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.manage_files'))
        else:
            flash('无效的用户名或密码。', 'error')
            
    return render_template('login.html', title='登录')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.manage_files'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if not username or not password or not password2:
            flash('所有字段均为必填项。', 'error')
            return render_template('register.html', title='注册')

        if password != password2:
            flash('两次输入的密码不一致。', 'error')
            return render_template('register.html', title='注册')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('该用户名已被注册，请选择其他用户名。', 'error')
            return render_template('register.html', title='注册')

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        try:
            db.session.commit()
            flash('恭喜，您已成功注册！现在可以登录了。', 'success')
            login_user(new_user)
            return redirect(url_for('main.manage_files'))
        except Exception as e:
            db.session.rollback()
            flash(f'注册过程中发生错误: {e}', 'error')
            current_app.logger.error(f"Error during registration: {e}")


    return render_template('register.html', title='注册')

@bp.route('/logout')
def logout():
    logout_user()
    flash('您已成功登出。', 'info')
    return redirect(url_for('auth.login'))

