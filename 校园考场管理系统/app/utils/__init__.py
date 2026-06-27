from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def role_required(*roles):
    """角色权限装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('权限不足', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """管理员权限装饰器"""
    return role_required('admin')(f)

def teacher_required(f):
    """教师权限装饰器(教师+管理员)"""
    return role_required('admin', 'teacher')(f)
