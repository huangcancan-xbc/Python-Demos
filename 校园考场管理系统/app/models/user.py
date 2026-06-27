from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    real_name = db.Column(db.String(50), nullable=False, comment='真实姓名')
    role = db.Column(db.Enum('admin', 'teacher', 'student'), nullable=False, default='student', comment='角色')
    employee_id = db.Column(db.String(20), comment='工号(教师/管理员)')
    student_id = db.Column(db.String(20), comment='学号(学生)')
    department = db.Column(db.String(100), comment='院系')
    phone = db.Column(db.String(20), comment='电话')
    email = db.Column(db.String(100), comment='邮箱')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关系
    created_exams = db.relationship('Exam', backref='creator', lazy='dynamic', foreign_keys='Exam.created_by')
    invigilated = db.relationship('InvigilatorAssignment', backref='teacher', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('密码不可读')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_name(self):
        names = {'admin': '管理员', 'teacher': '教师', 'student': '学生'}
        return names.get(self.role, '未知')

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None
