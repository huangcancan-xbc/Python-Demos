from urllib.parse import urlparse

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

VALID_ROLES = {'admin', 'teacher', 'student'}
REGISTRATION_ALLOWED_ROLES = {'student'}


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')

        user = User.query.filter_by(username=username).first()

        if user and user.verify_password(password):
            if role and user.role != role:
                flash('角色选择错误', 'danger')
                return render_template('login.html')

            login_user(user, remember=True)
            flash(f'欢迎回来, {user.real_name}!', 'success')
            next_page = request.args.get('next')
            if next_page and urlparse(next_page).netloc:
                next_page = None
            return redirect(next_page or url_for('main.dashboard'))

        flash('用户名或密码错误', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        real_name = request.form.get('real_name', '').strip()
        role = request.form.get('role', 'student')
        student_id = request.form.get('student_id', '').strip()
        employee_id = request.form.get('employee_id', '').strip()
        department = request.form.get('department', '').strip()

        if not username:
            flash('用户名不能为空', 'danger')
            return render_template('register.html')
        if not password:
            flash('密码不能为空', 'danger')
            return render_template('register.html')
        if not real_name:
            flash('真实姓名不能为空', 'danger')
            return render_template('register.html')
        if role not in REGISTRATION_ALLOWED_ROLES:
            flash('用户角色无效', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('register.html')

        user = User(
            username=username,
            real_name=real_name,
            role=role,
            student_id=student_id if role == 'student' else None,
            employee_id=employee_id if role != 'student' else None,
            department=department,
        )
        user.password = password

        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('注册失败，请稍后重试', 'danger')
            return render_template('register.html')

        flash('注册成功, 请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')
