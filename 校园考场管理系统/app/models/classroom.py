from . import db

class Classroom(db.Model):
    """教室/考场模型"""
    __tablename__ = 'classrooms'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='教室名称')
    building = db.Column(db.String(100), nullable=False, comment='教学楼')
    room_number = db.Column(db.String(20), nullable=False, comment='房间号')
    capacity = db.Column(db.Integer, nullable=False, comment='总座位数')
    rows = db.Column(db.Integer, nullable=False, default=6, comment='座位行数')
    cols = db.Column(db.Integer, nullable=False, default=10, comment='座位列数')
    equipment = db.Column(db.String(200), comment='设备信息(多媒体/空调等)')
    status = db.Column(db.Enum('available', 'maintenance'), default='available', comment='状态')

    # 关系
    arrangements = db.relationship('Arrangement', backref='classroom', lazy='dynamic')

    @property
    def effective_capacity(self):
        """隔位就坐后的有效容量
        策略: (row+col)为偶数的座位可用 → 约为总容量的一半
        """
        count = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if (r + c) % 2 == 0:
                    count += 1
        return count

    @property
    def location(self):
        return f'{self.building} {self.room_number}'

    @property
    def status_name(self):
        return '可用' if self.status == 'available' else '维护中'

    def get_seat_matrix(self):
        """生成座位矩阵, 0=不可用 1=可用 2=隔位留空"""
        matrix = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                if (r + c) % 2 == 0:
                    row.append(1)  # 可坐
                else:
                    row.append(2)  # 隔位留空
            matrix.append(row)
        return matrix

    def __repr__(self):
        return f'<Classroom {self.name}>'
