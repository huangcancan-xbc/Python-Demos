from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required
from app.models import db
from app.models.exam import Exam
from app.models.classroom import Classroom
from app.models.arrangement import Arrangement
from app.services.arranger import (
    arrange_exam, arrange_all_pending, auto_assign_invigilators, get_arrangement_summary,
    get_available_rooms_for_exam
)
from app.utils import role_required

arrangement_bp = Blueprint('arrangement', __name__)


@arrangement_bp.route('/')
@login_required
def list_arrangements():
    """编排列表 - 按考试分组"""
    exams_with_arr = db.session.query(Exam).filter(
        Exam.status.in_(['arranged', 'ongoing', 'finished'])
    ).order_by(Exam.exam_date.desc()).all()

    summaries = []
    for exam in exams_with_arr:
        summaries.append(get_arrangement_summary(exam))

    return render_template('arrangement/list.html', summaries=summaries)


@arrangement_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def create_arrangement():
    """创建编排 - 选择考试进行自动编排"""
    pending_exams = Exam.query.filter_by(status='pending').order_by(Exam.exam_date).all()
    available_rooms = Classroom.query.filter_by(status='available').all()
    available_rooms = sorted(available_rooms, key=lambda room: room.effective_capacity, reverse=True)

    if request.method == 'POST':
        try:
            exam_id = int(request.form.get('exam_id', ''))
        except ValueError:
            flash('请选择有效考试', 'danger')
            return render_template('arrangement/create.html', pending_exams=pending_exams, rooms=available_rooms)

        exam = Exam.query.get_or_404(exam_id)
        if exam.status != 'pending' or exam.arrangements.count() > 0:
            flash('该考试已编排，不能重复编排', 'warning')
            return redirect(url_for('arrangement.detail_arrangement', exam_id=exam.id))

        actual_rooms = get_available_rooms_for_exam(exam)
        total_effective = sum(r.effective_capacity for r in actual_rooms)
        if exam.student_count > total_effective:
            flash(f'教室不足! 需要{exam.student_count}个座位, 当前时段可用仅{total_effective}个(隔位就坐)', 'danger')
            return render_template('arrangement/create.html', pending_exams=pending_exams, rooms=available_rooms)

        arrangements = arrange_exam(exam)
        if arrangements is None:
            flash('编排失败: 可用教室不足或考试状态不允许编排', 'danger')
            return render_template('arrangement/create.html', pending_exams=pending_exams, rooms=available_rooms)

        try:
            for arr in arrangements:
                db.session.add(arr)
            exam.status = 'arranged'
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception('创建编排失败')
            flash('编排保存失败，请稍后重试', 'danger')
            return render_template('arrangement/create.html', pending_exams=pending_exams, rooms=available_rooms)

        flash(f'考试"{exam.name}"编排成功, 共分配{len(arrangements)}个考场', 'success')
        return redirect(url_for('arrangement.detail_arrangement', exam_id=exam.id))

    return render_template('arrangement/create.html', pending_exams=pending_exams, rooms=available_rooms)


@arrangement_bp.route('/batch', methods=['POST'])
@login_required
@role_required('admin')
def batch_arrange():
    """一键批量编排所有待编排考试"""
    results = arrange_all_pending()
    success = sum(1 for v in results.values() if v)
    fail = sum(1 for v in results.values() if not v)
    flash(f'批量编排完成: 成功{success}场, 失败{fail}场', 'info')
    return redirect(url_for('arrangement.list_arrangements'))


@arrangement_bp.route('/detail/<int:exam_id>')
@login_required
def detail_arrangement(exam_id):
    """编排详情 - 含座位图"""
    exam = Exam.query.get_or_404(exam_id)
    summary = get_arrangement_summary(exam)
    return render_template('arrangement/detail.html', summary=summary)


@arrangement_bp.route('/assign_invigilator/<int:exam_id>', methods=['POST'])
@login_required
@role_required('admin')
def assign_invigilator(exam_id):
    """自动分配监考教师"""
    exam = Exam.query.get_or_404(exam_id)
    if exam.arrangements.count() == 0:
        flash('请先完成考场编排，再分配监考', 'warning')
        return redirect(url_for('arrangement.detail_arrangement', exam_id=exam_id))
    if any(arr.invigilators.first() for arr in exam.arrangements):
        flash('该考试已分配监考，不能重复分配', 'warning')
        return redirect(url_for('arrangement.detail_arrangement', exam_id=exam_id))

    assignments = auto_assign_invigilators(exam)
    if not assignments:
        flash('监考分配失败：教师数量不足或存在时间冲突', 'danger')
        return redirect(url_for('arrangement.detail_arrangement', exam_id=exam_id))

    try:
        for inv in assignments:
            db.session.add(inv)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('监考分配保存失败')
        flash('监考分配保存失败，请稍后重试', 'danger')
        return redirect(url_for('arrangement.detail_arrangement', exam_id=exam_id))

    flash(f'监考分配完成, 共分配{len(assignments)}人次', 'success')
    return redirect(url_for('arrangement.detail_arrangement', exam_id=exam_id))


@arrangement_bp.route('/delete/<int:exam_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_arrangement(exam_id):
    """删除考试的编排"""
    exam = Exam.query.get_or_404(exam_id)
    try:
        for arr in Arrangement.query.filter_by(exam_id=exam_id).all():
            db.session.delete(arr)
        exam.status = 'pending'
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('编排删除失败')
        flash('编排删除失败，请稍后重试', 'danger')
        return redirect(url_for('arrangement.list_arrangements'))

    flash('编排已删除', 'success')
    return redirect(url_for('arrangement.list_arrangements'))


@arrangement_bp.route('/seat_data/<int:arr_id>')
@login_required
def seat_data(arr_id):
    """API: 获取座位图数据(JSON)"""
    arr = Arrangement.query.get_or_404(arr_id)
    return jsonify({
        'rows': arr.classroom.rows,
        'cols': arr.classroom.cols,
        'seat_map': arr.get_seat_map(),
        'student_count': arr.student_count,
        'classroom': arr.classroom.name,
    })
