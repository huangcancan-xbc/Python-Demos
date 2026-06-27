from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.models import db
from app.models.classroom import Classroom
from app.utils import role_required

classroom_bp = Blueprint('classroom', __name__)

VALID_STATUSES = {'available', 'maintenance'}


def _positive_int(value, field_name):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name}必须是正整数')
    if number <= 0:
        raise ValueError(f'{field_name}必须是正整数')
    return number


def _parse_classroom_form():
    name = request.form.get('name', '').strip()
    building = request.form.get('building', '').strip()
    room_number = request.form.get('room_number', '').strip()
    capacity = _positive_int(request.form.get('capacity'), '座位容量')
    rows = _positive_int(request.form.get('rows'), '座位行数')
    cols = _positive_int(request.form.get('cols'), '座位列数')
    status = request.form.get('status', 'available').strip()

    if not name:
        raise ValueError('教室名称不能为空')
    if not building:
        raise ValueError('教学楼不能为空')
    if not room_number:
        raise ValueError('房间号不能为空')
    if status not in VALID_STATUSES:
        raise ValueError('教室状态无效')

    return {
        'name': name,
        'building': building,
        'room_number': room_number,
        'capacity': capacity,
        'rows': rows,
        'cols': cols,
        'equipment': request.form.get('equipment', '').strip(),
        'status': status,
    }


@classroom_bp.route('/')
@login_required
def list_classrooms():
    """教室列表"""
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '').strip()

    query = Classroom.query
    if keyword:
        query = query.filter(
            Classroom.name.contains(keyword) |
            Classroom.building.contains(keyword)
        )

    pagination = query.order_by(Classroom.building, Classroom.room_number).paginate(
        page=page, per_page=current_app.config.get('PER_PAGE', 10), error_out=False
    )
    return render_template('classroom/list.html', pagination=pagination, classrooms=pagination.items)


@classroom_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_classroom():
    """添加教室"""
    if request.method == 'POST':
        try:
            room = Classroom(**_parse_classroom_form())
            db.session.add(room)
            db.session.commit()
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template('classroom/form.html', room=None)
        except Exception:
            db.session.rollback()
            current_app.logger.exception('添加教室失败')
            flash('教室保存失败，请稍后重试', 'danger')
            return render_template('classroom/form.html', room=None)

        flash('教室添加成功', 'success')
        return redirect(url_for('classroom.list_classrooms'))

    return render_template('classroom/form.html', room=None)


@classroom_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_classroom(id):
    """编辑教室"""
    room = Classroom.query.get_or_404(id)

    if request.method == 'POST':
        try:
            data = _parse_classroom_form()
            for key, value in data.items():
                setattr(room, key, value)
            db.session.commit()
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template('classroom/form.html', room=room)
        except Exception:
            db.session.rollback()
            current_app.logger.exception('更新教室失败')
            flash('教室更新失败，请稍后重试', 'danger')
            return render_template('classroom/form.html', room=room)

        flash('教室更新成功', 'success')
        return redirect(url_for('classroom.list_classrooms'))

    return render_template('classroom/form.html', room=room)


@classroom_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_classroom(id):
    """删除教室"""
    room = Classroom.query.get_or_404(id)
    if room.arrangements.count() > 0:
        flash('该教室已有编排记录，不能删除', 'warning')
        return redirect(url_for('classroom.list_classrooms'))

    try:
        db.session.delete(room)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('删除教室失败')
        flash('教室删除失败，请稍后重试', 'danger')
        return redirect(url_for('classroom.list_classrooms'))

    flash('教室已删除', 'success')
    return redirect(url_for('classroom.list_classrooms'))


@classroom_bp.route('/detail/<int:id>')
@login_required
def detail_classroom(id):
    """教室详情 - 含座位图"""
    room = Classroom.query.get_or_404(id)
    seat_matrix = room.get_seat_matrix()
    return render_template('classroom/detail.html', room=room, seat_matrix=seat_matrix)
