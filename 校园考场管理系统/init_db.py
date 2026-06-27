"""
数据库初始化脚本
- 创建数据库 (如不存在)
- 创建所有表
- 插入示例数据 (管理员账号 + 教室 + 教师)
"""
import os
import pymysql
from datetime import date
from app import create_app
from app.models import db
from app.models.user import User
from app.models.classroom import Classroom
from app.models.exam import Exam

def create_database():
    """创建MySQL数据库"""
    # 从环境变量或配置文件读取数据库连接信息
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_port = int(os.environ.get('DB_PORT', 3306))

    conn = pymysql.connect(host=db_host, user=db_user, password=db_password, port=db_port)
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS campus_exam_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    conn.close()
    print('[OK] 数据库 campus_exam_system 已就绪')

def init_tables(app):
    """创建所有数据表"""
    with app.app_context():
        db.create_all()
        print('[OK] 数据表创建完成')

def seed_data(app):
    """插入示例数据"""
    with app.app_context():
        # 检查是否已有数据
        if User.query.first():
            print('[SKIP] 数据库已有数据, 跳过初始化')
            return

        # ========== 管理员 ==========
        admin = User(username='admin', real_name='系统管理员', role='admin', employee_id='A001', department='教务处')
        admin.password = '123456'

        # ========== 教师 ==========
        teachers = []
        teacher_data = [
            ('t01', '王建国', 'T001', '计算机学院'),
            ('t02', '李晓明', 'T002', '计算机学院'),
            ('t03', '张华', 'T003', '数学学院'),
            ('t04', '刘芳', 'T004', '物理学院'),
            ('t05', '陈伟', 'T005', '计算机学院'),
            ('t06', '赵敏', 'T006', '外语学院'),
            ('t07', '孙丽', 'T007', '电子信息学院'),
            ('t08', '周强', 'T008', '机械学院'),
        ]
        for uname, name, eid, dept in teacher_data:
            t = User(username=uname, real_name=name, role='teacher', employee_id=eid, department=dept)
            t.password = '123456'
            teachers.append(t)

        # ========== 学生 ==========
        students = []
        for i in range(1, 51):
            s = User(
                username=f's{i:03d}',
                real_name=f'学生{i:03d}',
                role='student',
                student_id=f'202400{i:03d}',
                department='计算机学院'
            )
            s.password = '123456'
            students.append(s)

        # ========== 教室 ==========
        rooms = [
            Classroom(name='第一教学楼101', building='第一教学楼', room_number='101',
                      capacity=60, rows=6, cols=10, equipment='多媒体, 空调'),
            Classroom(name='第一教学楼102', building='第一教学楼', room_number='102',
                      capacity=60, rows=6, cols=10, equipment='多媒体, 空调'),
            Classroom(name='第一教学楼201', building='第一教学楼', room_number='201',
                      capacity=90, rows=9, cols=10, equipment='多媒体, 空调, 投影仪'),
            Classroom(name='第一教学楼202', building='第一教学楼', room_number='202',
                      capacity=90, rows=9, cols=10, equipment='多媒体, 空调'),
            Classroom(name='第二教学楼301', building='第二教学楼', room_number='301',
                      capacity=120, rows=10, cols=12, equipment='多媒体, 空调, 投影仪, 音响'),
            Classroom(name='第二教学楼302', building='第二教学楼', room_number='302',
                      capacity=120, rows=10, cols=12, equipment='多媒体, 空调, 投影仪'),
            Classroom(name='第二教学楼401', building='第二教学楼', room_number='401',
                      capacity=50, rows=5, cols=10, equipment='多媒体'),
            Classroom(name='第二教学楼402', building='第二教学楼', room_number='402',
                      capacity=50, rows=5, cols=10, equipment='多媒体, 空调'),
            Classroom(name='第三教学楼101', building='第三教学楼', room_number='101',
                      capacity=200, rows=10, cols=20, equipment='多媒体, 空调, 投影仪, 音响, 录播'),
            Classroom(name='第三教学楼102', building='第三教学楼', room_number='102',
                      capacity=80, rows=8, cols=10, equipment='多媒体, 空调'),
        ]

        # ========== 考试 ==========
        exams = [
            Exam(name='2026春季《软件工程》期末考试', subject='软件工程',
                 exam_date=date(2026, 6, 20), time_slot='morning_1',
                 student_count=120, created_by=1),
            Exam(name='2026春季《数据结构》期末考试', subject='数据结构',
                 exam_date=date(2026, 6, 20), time_slot='afternoon_1',
                 student_count=150, created_by=1),
            Exam(name='2026春季《高等数学》期末考试', subject='高等数学',
                 exam_date=date(2026, 6, 21), time_slot='morning_1',
                 student_count=200, created_by=1),
            Exam(name='2026春季《大学英语》期末考试', subject='大学英语',
                 exam_date=date(2026, 6, 21), time_slot='afternoon_1',
                 student_count=80, created_by=1),
            Exam(name='2026春季《计算机网络》期末考试', subject='计算机网络',
                 exam_date=date(2026, 6, 22), time_slot='morning_1',
                 student_count=90, created_by=1),
        ]

        # 插入数据
        db.session.add(admin)
        db.session.add_all(teachers)
        db.session.add_all(students)
        db.session.add_all(rooms)
        db.session.add_all(exams)
        db.session.commit()

        print(f'[OK] 示例数据插入完成:')
        print(f'     管理员: 1人 (admin/123456)')
        print(f'     教师: {len(teachers)}人 (t01~t08 / 123456)')
        print(f'     学生: {len(students)}人 (s001~s050 / 123456)')
        print(f'     教室: {len(rooms)}间')
        print(f'     考试: {len(exams)}场')


if __name__ == '__main__':
    print('='*50)
    print('  校园考场管理系统 - 数据库初始化')
    print('='*50)

    create_database()

    app = create_app()
    init_tables(app)
    seed_data(app)

    print('='*50)
    print('  初始化完成! 运行 python run.py 启动系统')
    print('='*50)
