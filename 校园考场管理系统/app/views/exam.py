from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import db
from app.models.exam import Exam
from app.utils import role_required

exam_bp = Blueprint('exam', __name__)


def _positive_int(value, field_name):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name}必须是正整数')
    if number <= 0:
        raise ValueError(f'{field_name}必须是正整数')
    return number


def _parse_exam_form(time_slots):
    name = request.form.get('name', '').strip()
    subject = request.form.get('subject', '').strip()
    exam_date_raw = request.form.get('exam_date', '').strip()
    time_slot = request.form.get('time_slot', '').strip()
    student_count = _positive_int(request.form.get('student_count'), '考生人数')

    if not name:
        raise ValueError('考试名称不能为空')
    if not subject:
        raise ValueError('考试科目不能为空')
    if time_slot not in time_slots:
        raise ValueError('考试时间段无效')
    try:
        exam_date = datetime.strptime(exam_date_raw, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError('考试日期无效')

    return {
        'name': name,
        'subject': subject,
        'exam_date': exam_date,
        'time_slot': time_slot,
        'student_count': student_count,
        'description': request.form.get('description', '').strip(),
    }


@exam_bp.route('/')
@login_required
def list_exams():
    """考试列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    keyword = request.args.get('keyword', '').strip()

    query = Exam.query
    if status:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            Exam.name.contains(keyword) | Exam.subject.contains(keyword)
        )

    pagination = query.order_by(Exam.exam_date.desc()).paginate(
        page=page, per_page=current_app.config.get('PER_PAGE', 10), error_out=False
    )
    return render_template('exam/list.html', pagination=pagination, exams=pagination.items)


@exam_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def add_exam():
    """添加考试"""
    time_slots = current_app.config['TIME_SLOTS']

    if request.method == 'POST':
        try:
            data = _parse_exam_form(time_slots)
            exam = Exam(**data, created_by=current_user.id)
            db.session.add(exam)
            db.session.commit()
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template('exam/form.html', exam=None, time_slots=time_slots)
        except Exception:
            db.session.rollback()
            current_app.logger.exception('添加考试失败')
            flash('考试保存失败，请稍后重试', 'danger')
            return render_template('exam/form.html', exam=None, time_slots=time_slots)

        flash('考试添加成功', 'success')
        return redirect(url_for('exam.list_exams'))

    return render_template('exam/form.html', exam=None, time_slots=time_slots)


@exam_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def edit_exam(id):
    """编辑考试"""
    time_slots = current_app.config['TIME_SLOTS']
    exam = Exam.query.get_or_404(id)

    if request.method == 'POST':
        try:
            if exam.status != 'pending':
                raise ValueError('已编排或进行中的考试不能直接修改，请先删除编排')
            data = _parse_exam_form(time_slots)
            for key, value in data.items():
                setattr(exam, key, value)
            db.session.commit()
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template('exam/form.html', exam=exam, time_slots=time_slots)
        except Exception:
            db.session.rollback()
            current_app.logger.exception('更新考试失败')
            flash('考试更新失败，请稍后重试', 'danger')
            return render_template('exam/form.html', exam=exam, time_slots=time_slots)

        flash('考试更新成功', 'success')
        return redirect(url_for('exam.list_exams'))

    return render_template('exam/form.html', exam=exam, time_slots=time_slots)


@exam_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_exam(id):
    """删除考试"""
    exam = Exam.query.get_or_404(id)
    try:
        db.session.delete(exam)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('删除考试失败')
        flash('考试删除失败，请稍后重试', 'danger')
        return redirect(url_for('exam.list_exams'))

    flash('考试已删除', 'success')
    return redirect(url_for('exam.list_exams'))


@exam_bp.route('/detail/<int:id>')
@login_required
def detail_exam(id):
    """考试详情"""
    exam = Exam.query.get_or_404(id)
    return render_template('exam/detail.html', exam=exam)
