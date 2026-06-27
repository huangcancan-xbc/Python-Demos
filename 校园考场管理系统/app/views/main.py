from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.exam import Exam
from app.models.classroom import Classroom
from app.models.user import User
from app.models.arrangement import Arrangement

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # 统计数据
    stats = {
        'exam_count': Exam.query.count(),
        'pending_count': Exam.query.filter_by(status='pending').count(),
        'arranged_count': Exam.query.filter_by(status='arranged').count(),
        'classroom_count': Classroom.query.filter_by(status='available').count(),
        'teacher_count': User.query.filter_by(role='teacher').count(),
        'student_count': User.query.filter_by(role='student').count(),
        'arrangement_count': Arrangement.query.count(),
    }

    # 最近的考试
    recent_exams = Exam.query.order_by(Exam.exam_date.desc()).limit(5).all()

    return render_template('dashboard.html', stats=stats, recent_exams=recent_exams)
