"""
考场编排核心算法模块
=========================
功能:
1. 考场自动编排 - 根据考试科目+可用教室+考生人数, 自动分配教室
2. 隔位就坐 - 座位坐标矩阵, (row+col)%2==0 的位置可坐
3. 监考教师分配 - 负载均衡, 避免冲突

硬约束:
- 同时段不同科目不共享教室
- 每场考试分配的座位数 <= 教室有效容量(隔位就坐)

软约束:
- 优先使用大教室匹配大考试
- 监考教师工作量尽量均衡
"""

from sqlalchemy import select

from app.models import db
from app.models.classroom import Classroom
from app.models.arrangement import Arrangement, InvigilatorAssignment
from app.models.user import User
from app.models.exam import Exam


def get_available_rooms_for_exam(exam):
    """获取考试当前时段未被占用的可用教室"""
    occupied_room_ids = select(Arrangement.classroom_id).join(
        Exam, Arrangement.exam_id == Exam.id
    ).where(
        Exam.exam_date == exam.exam_date,
        Exam.time_slot == exam.time_slot,
        Exam.id != exam.id
    )

    rooms = Classroom.query.filter(
        Classroom.status == 'available',
        ~Classroom.id.in_(occupied_room_ids)
    ).all()
    return sorted(rooms, key=lambda room: room.effective_capacity, reverse=True)


def arrange_exam(exam):
    """
    为单个考试自动编排考场

    算法流程:
    1. 获取同时间段已占用的教室ID集合
    2. 从可用教室中按容量降序排列
    3. 贪心分配: 依次取教室, 直到容纳所有考生
    4. 返回编排结果列表

    :param exam: Exam 对象
    :return: list[Arrangement] 或 None(不可编排/教室不足)
    """
    if exam.status != 'pending':
        return None
    if Arrangement.query.filter_by(exam_id=exam.id).first():
        return None
    if exam.student_count <= 0:
        return None

    available_rooms = get_available_rooms_for_exam(exam)

    remaining = exam.student_count
    arrangements = []

    next_seat_start = 1
    for room in available_rooms:
        if remaining <= 0:
            break
        eff_cap = room.effective_capacity
        assign_count = min(remaining, eff_cap)

        arr = Arrangement(
            exam_id=exam.id,
            classroom_id=room.id,
            student_count=assign_count,
            seat_start=next_seat_start,
            seat_end=next_seat_start + assign_count - 1,
        )
        arrangements.append(arr)
        remaining -= assign_count
        next_seat_start += assign_count

    if remaining > 0:
        return None

    return arrangements


def arrange_all_pending():
    """
    批量编排所有待编排考试

    :return: dict {exam_id: True/False, ...}
    """
    results = {}
    pending_exams = Exam.query.filter_by(status='pending').order_by(
        Exam.exam_date, Exam.time_slot
    ).all()

    for exam in pending_exams:
        try:
            arrs = arrange_exam(exam)
            if arrs:
                for arr in arrs:
                    db.session.add(arr)
                exam.status = 'arranged'
                db.session.commit()
                results[exam.id] = True
            else:
                results[exam.id] = False
        except Exception:
            db.session.rollback()
            results[exam.id] = False

    return results


def _busy_teacher_ids_for_exam(exam):
    """获取同日期同时间段已经有监考任务的教师ID集合"""
    arrangement_ids = select(Arrangement.id).join(
        Exam, Arrangement.exam_id == Exam.id
    ).where(
        Exam.exam_date == exam.exam_date,
        Exam.time_slot == exam.time_slot,
        Exam.id != exam.id
    )
    teacher_ids = db.session.execute(
        select(InvigilatorAssignment.teacher_id).where(
            InvigilatorAssignment.arrangement_id.in_(arrangement_ids)
        )
    ).all()
    return {teacher_id for (teacher_id,) in teacher_ids}


def auto_assign_invigilators(exam):
    """
    为考试自动分配监考教师

    算法:
    1. 查询该考试的所有编排记录
    2. 每个考场分配1名主监考, 容量>40则加1名副监考
    3. 优先选择监考次数少的教师, 且避免同时间段冲突

    :param exam: Exam 对象
    :return: list[InvigilatorAssignment]
    """
    arrangements = Arrangement.query.filter_by(exam_id=exam.id).all()
    if not arrangements:
        return []
    if any(arr.invigilators.first() for arr in arrangements):
        return []

    teachers = User.query.filter_by(role='teacher').all()
    if not teachers:
        return []

    # 统计每位教师监考次数
    teach_count = {}
    for t in teachers:
        cnt = InvigilatorAssignment.query.filter_by(teacher_id=t.id).count()
        teach_count[t.id] = cnt

    busy_teacher_ids = _busy_teacher_ids_for_exam(exam)
    assignments = []
    used_in_this_exam = set()

    for arr in arrangements:
        needed_count = 2 if arr.classroom.capacity > 40 else 1
        available = sorted(
            [t for t in teachers if t.id not in busy_teacher_ids and t.id not in used_in_this_exam],
            key=lambda t: teach_count.get(t.id, 0)
        )

        if len(available) < needed_count:
            return []

        chief = available[0]
        chief_inv = InvigilatorAssignment(
            arrangement_id=arr.id,
            teacher_id=chief.id,
            role='chief'
        )
        assignments.append(chief_inv)
        used_in_this_exam.add(chief.id)
        teach_count[chief.id] = teach_count.get(chief.id, 0) + 1

        if needed_count == 2:
            assistant = available[1]
            asst_inv = InvigilatorAssignment(
                arrangement_id=arr.id,
                teacher_id=assistant.id,
                role='assistant'
            )
            assignments.append(asst_inv)
            used_in_this_exam.add(assistant.id)
            teach_count[assistant.id] = teach_count.get(assistant.id, 0) + 1

    return assignments


def get_arrangement_summary(exam):
    """
    获取考试编排摘要

    :return: dict 包含教室映射表和统计信息
    """
    arrangements = Arrangement.query.filter_by(exam_id=exam.id).all()

    rooms = []
    for arr in arrangements:
        invs = InvigilatorAssignment.query.filter_by(arrangement_id=arr.id).all()
        inv_names = [f"{inv.teacher.real_name}({inv.role_name})" for inv in invs]
        rooms.append({
            'classroom': arr.classroom,
            'student_count': arr.student_count,
            'seat_map': arr.get_seat_map(),
            'invigilators': inv_names,
        })

    return {
        'exam': exam,
        'rooms': rooms,
        'total_arranged': sum(r['student_count'] for r in rooms),
        'room_count': len(rooms),
    }
