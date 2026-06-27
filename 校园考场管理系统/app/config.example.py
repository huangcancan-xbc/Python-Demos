import os

class Config:
    """应用配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

    # MySQL 数据库配置 - 请修改为你的实际配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:your_password@localhost:3306/campus_exam_system?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # 分页配置
    PER_PAGE = 10

    # 考试时间段定义
    TIME_SLOTS = {
        'morning_1': {'name': '上午第一场', 'start': '08:00', 'end': '10:00'},
        'morning_2': {'name': '上午第二场', 'start': '10:30', 'end': '12:30'},
        'afternoon_1': {'name': '下午第一场', 'start': '14:00', 'end': '16:00'},
        'afternoon_2': {'name': '下午第二场', 'start': '16:30', 'end': '18:30'},
    }
