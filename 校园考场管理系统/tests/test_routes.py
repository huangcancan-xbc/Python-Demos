from pathlib import Path
import unittest
from datetime import date

from flask import Flask

from app.models import db, login_manager
from app.models.arrangement import Arrangement
from app.models.classroom import Classroom
from app.models.exam import Exam
from app.models.user import User
from app.views.arrangement import arrangement_bp
from app.views.auth import auth_bp
from app.views.classroom import classroom_bp
from app.views.exam import exam_bp
from app.views.main import main_bp

ROOT = Path(__file__).resolve().parents[1]


class RouteValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(
            __name__,
            template_folder=str(ROOT / 'app/templates'),
            static_folder=str(ROOT / 'app/static'),
        )
        self.app.config.update(
            TESTING=True,
            SECRET_KEY='test-secret',
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            TIME_SLOTS={'morning_1': {'name': '上午第一场', 'start': '08:00', 'end': '10:00'}},
        )
        db.init_app(self.app)
        login_manager.init_app(self.app)
        self.app.register_blueprint(auth_bp)
        self.app.register_blueprint(main_bp)
        self.app.register_blueprint(exam_bp, url_prefix='/exam')
        self.app.register_blueprint(classroom_bp, url_prefix='/classroom')
        self.app.register_blueprint(arrangement_bp, url_prefix='/arrangement')
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def add_admin(self):
        admin = User(username='admin', real_name='管理员', role='admin', employee_id='A001')
        admin.password = '123456'
        db.session.add(admin)
        db.session.commit()
        return admin

    def login_as(self, user):
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user.id)
            session['_fresh'] = True

    def test_register_rejects_invalid_role(self):
        response = self.client.post('/register', data={
            'username': 'badrole',
            'password': '123456',
            'real_name': '错误角色',
            'role': 'hacker',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(User.query.filter_by(username='badrole').first())

    def test_add_exam_rejects_non_positive_student_count(self):
        self.login_as(self.add_admin())

        response = self.client.post('/exam/add', data={
            'name': '软件工程考试',
            'subject': '软件工程',
            'exam_date': '2026-06-20',
            'time_slot': 'morning_1',
            'student_count': '0',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Exam.query.count(), 0)

    def test_delete_classroom_with_arrangement_is_rejected(self):
        admin = self.add_admin()
        room = Classroom(name='第一教学楼101', building='第一教学楼', room_number='101', capacity=4, rows=1, cols=4)
        exam = Exam(
            name='软件工程考试',
            subject='软件工程',
            exam_date=date(2026, 6, 20),
            time_slot='morning_1',
            student_count=2,
            status='arranged',
        )
        db.session.add_all([room, exam])
        db.session.commit()
        db.session.add(Arrangement(exam_id=exam.id, classroom_id=room.id, student_count=2))
        db.session.commit()
        self.login_as(admin)

        response = self.client.post(f'/classroom/delete/{room.id}')

        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(db.session.get(Classroom, room.id))


if __name__ == '__main__':
    unittest.main()
