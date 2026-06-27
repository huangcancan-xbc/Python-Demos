from datetime import datetime
from . import db

class Arrangement(db.Model):
    """考场编排记录 - 核心表: 一个考试在一个教室的编排"""
    __tablename__ = 'arrangements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False, comment='考试ID')
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False, comment='教室ID')
    seat_start = db.Column(db.Integer, default=1, comment='起始座位号')
    seat_end = db.Column(db.Integer, comment='结束座位号')
    student_count = db.Column(db.Integer, nullable=False, comment='分配考生数')
    notes = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关系
    seat_assignments = db.relationship('SeatAssignment', backref='arrangement', lazy='dynamic', cascade='all, delete-orphan')
    invigilators = db.relationship('InvigilatorAssignment', backref='arrangement', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def effective_capacity(self):
        """该编排实际容纳人数"""
        return self.student_count

    def get_seat_map(self):
        """生成座位占用图: 返回二维矩阵
        1=已分配学生  0=隔位留空  -1=超出范围
        """
        classroom = self.classroom
        matrix = []
        seat_idx = 0
        for r in range(classroom.rows):
            row = []
            for c in range(classroom.cols):
                if (r + c) % 2 == 0:  # 可坐位置
                    if seat_idx < self.student_count:
                        row.append(1)  # 已分配
                    else:
                        row.append(0)  # 空闲可坐位
                    seat_idx += 1
                else:
                    row.append(-1)  # 隔位留空
            matrix.append(row)
        return matrix

    def __repr__(self):
        return f'<Arrangement exam={self.exam_id} room={self.classroom_id}>'


class SeatAssignment(db.Model):
    """学生座位分配"""
    __tablename__ = 'seat_assignments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    arrangement_id = db.Column(db.Integer, db.ForeignKey('arrangements.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    row = db.Column(db.Integer, nullable=False, comment='行号(从0开始)')
    col = db.Column(db.Integer, nullable=False, comment='列号(从0开始)')
    seat_number = db.Column(db.String(10), nullable=False, comment='座位编号')

    # 关系
    student = db.relationship('User', backref='exam_seats', foreign_keys=[student_id])

    def __repr__(self):
        return f'<Seat {self.seat_number} student={self.student_id}>'


class InvigilatorAssignment(db.Model):
    """监考教师分配"""
    __tablename__ = 'invigilator_assignments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    arrangement_id = db.Column(db.Integer, db.ForeignKey('arrangements.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum('chief', 'assistant'), default='assistant', comment='主监考/副监考')
    checked_in = db.Column(db.Boolean, default=False, comment='是否签到')
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def role_name(self):
        return '主监考' if self.role == 'chief' else '副监考'

    def __repr__(self):
        return f'<Invigilator teacher={self.teacher_id} role={self.role}>'
