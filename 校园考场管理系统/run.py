"""
校园考场管理系统 - 启动入口
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
