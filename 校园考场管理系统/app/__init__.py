from flask import Flask
from .config import Config
from .models import db, login_manager

def create_app():
    """Flask 应用工厂"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)

    # 注册蓝图
    from .views.auth import auth_bp
    from .views.main import main_bp
    from .views.exam import exam_bp
    from .views.classroom import classroom_bp
    from .views.arrangement import arrangement_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(exam_bp, url_prefix='/exam')
    app.register_blueprint(classroom_bp, url_prefix='/classroom')
    app.register_blueprint(arrangement_bp, url_prefix='/arrangement')

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app
