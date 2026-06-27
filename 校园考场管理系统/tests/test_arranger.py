import unittest
from datetime import date

from flask import Flask

from app.models import db, login_manager
from app.models.arrangement import Arrangement, InvigilatorAssignment
from app.models.classroom import Classroom
from app.models.exam import Exam
from app.models.user import User
from app.services.arranger import arrange_all_pending, arrange_exam, auto_assign_invigilators


class ArrangementServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SECRET_KEY='test-secret',
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            TIME_SLOTS={'morning_1': {'name': '上午第一场', 'start': '08:00', 'end': '10:00'}},
        )
        db.init_app(self.app)
        login_manager.init_app(self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def add_room(self, name, rows=2, cols=4, status='available'):
        room = Classroom(
            name=name,
            building='一教',
            room_number=name,
            capacity=rows * cols,
            rows=rows,
            cols=cols,
            status=status,
        )
        db.session.add(room)
        db.session.commit()
        return room

    def add_exam(self, name, student_count, day=date(2026, 6, 20), status='pending'):
        exam = Exam(
            name=name,
            subject=name,
            exam_date=day,
            time_slot='morning_1',
            student_count=student_count,
            status=status,
        )
        db.session.add(exam)
        db.session.commit()
        return exam

    def add_teacher(self, username):
        teacher = User(username=username, real_name=username, role='teacher', employee_id=username)
        teacher.password = '123456'
        db.session.add(teacher)
        db.session.commit()
        return teacher

    def test_arrange_exam_returns_none_when_exam_already_has_arrangements(self):
        room = self.add_room('101')
        exam = self.add_exam('软件工程', 2, status='arranged')
        db.session.add(Arrangement(exam_id=exam.id, classroom_id=room.id, student_count=2))
        db.session.commit()

        result = arrange_exam(exam)

        self.assertIsNone(result)

    def test_arrange_exam_excludes_rooms_occupied_in_same_slot(self):
        occupied_room = self.add_room('101')
        free_room = self.add_room('102')
        existing_exam = self.add_exam('数据结构', 2, status='arranged')
        target_exam = self.add_exam('软件工程', 2)
        db.session.add(Arrangement(exam_id=existing_exam.id, classroom_id=occupied_room.id, student_count=2))
        db.session.commit()

        result = arrange_exam(target_exam)

        self.assertEqual([arr.classroom_id for arr in result], [free_room.id])

    def test_batch_arrange_does_not_reuse_room_for_same_slot(self):
        self.add_room('101', rows=1, cols=4)
        exam_one = self.add_exam('软件工程', 2)
        exam_two = self.add_exam('数据结构', 2)

        results = arrange_all_pending()

        db.session.refresh(exam_one)
        db.session.refresh(exam_two)
        self.assertEqual(results[exam_one.id], True)
        self.assertEqual(results[exam_two.id], False)
        self.assertEqual(Arrangement.query.count(), 1)

    def test_auto_assign_invigilators_returns_empty_when_exam_has_existing_assignments(self):
        room = self.add_room('101')
        exam = self.add_exam('软件工程', 2, status='arranged')
        teacher = self.add_teacher('t01')
        arrangement = Arrangement(exam_id=exam.id, classroom_id=room.id, student_count=2)
        db.session.add(arrangement)
        db.session.commit()
        db.session.add(InvigilatorAssignment(arrangement_id=arrangement.id, teacher_id=teacher.id, role='chief'))
        db.session.commit()

        result = auto_assign_invigilators(exam)

        self.assertEqual(result, [])

    def test_auto_assign_invigilators_does_not_use_busy_teacher_in_same_slot(self):
        room_one = self.add_room('101', rows=1, cols=2)
        room_two = self.add_room('102', rows=1, cols=2)
        busy_teacher = self.add_teacher('t01')
        free_teacher = self.add_teacher('t02')
        existing_exam = self.add_exam('数据结构', 1, status='arranged')
        target_exam = self.add_exam('软件工程', 1, status='arranged')
        existing_arr = Arrangement(exam_id=existing_exam.id, classroom_id=room_one.id, student_count=1)
        target_arr = Arrangement(exam_id=target_exam.id, classroom_id=room_two.id, student_count=1)
        db.session.add_all([existing_arr, target_arr])
        db.session.commit()
        db.session.add(InvigilatorAssignment(arrangement_id=existing_arr.id, teacher_id=busy_teacher.id, role='chief'))
        db.session.commit()

        result = auto_assign_invigilators(target_exam)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].teacher_id, free_teacher.id)


if __name__ == '__main__':
    unittest.main()
