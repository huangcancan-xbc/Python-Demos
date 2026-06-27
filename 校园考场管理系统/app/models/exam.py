from datetime import datetime
from . import db

class Exam(db.Model):
    """考试模型"""
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, comment='考试名称')
    subject = db.Column(db.String(100), nullable=False, comment='科目')
    exam_date = db.Column(db.Date, nullable=False, comment='考试日期')
    time_slot = db.Column(db.String(20), nullable=False, comment='时间段代码')
    student_count = db.Column(db.Integer, nullable=False, comment='考生人数')
    status = db.Column(db.Enum('pending', 'arranged', 'ongoing', 'finished'), default='pending', comment='状态')
    description = db.Column(db.Text, comment='考试说明')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建者ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关系
    arrangements = db.relationship('Arrangement', backref='exam', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def time_slot_name(self):
        from flask import current_app
        slots = current_app.config.get('TIME_SLOTS', {})
        slot = slots.get(self.time_slot, {})
        return slot.get('name', self.time_slot)

    @property
    def time_info(self):
        from flask import current_app
        slots = current_app.config.get('TIME_SLOTS', {})
        slot = slots.get(self.time_slot, {})
        return f"{slot.get('start', '')} - {slot.get('end', '')}"

    @property
    def status_name(self):
        names = {'pending': '待编排', 'arranged': '已编排', 'ongoing': '进行中', 'finished': '已结束'}
        return names.get(self.status, '未知')

    @property
    def arranged_count(self):
        """已分配的考生总人数"""
        total = 0
        for arr in self.arrangements:
            total += arr.student_count
        return total

    def __repr__(self):
        return f'<Exam {self.name}>'
