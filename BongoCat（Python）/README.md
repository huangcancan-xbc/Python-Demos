# BongoCat（Python 版）

一个使用 Python 和 Pygame 制作的 BongoCat 桌面宠物，支持多种乐器演奏。

## 运行效果

https://github.com/user-attachments/assets/68842bb0-60e0-4b03-96e5-cd03762bf3d1

## 功能特性

- **多种乐器**：邦戈鼓、钢琴、铃鼓、喵叫
- **键盘演奏**：A/D 敲鼓，1-0 弹钢琴，B 敲铃鼓，空格喵叫
- **鼠标交互**：点击猫咪左右手
- **暗色模式**：按 R 切换亮色/暗色主题
- **演示曲目**：按 F1 自动播放演示
- **帮助系统**：按 F2 查看操作说明

## 环境要求

- Python 3.8+
- Pygame 2.0+

## 项目结构

```
BongoCat（Python）/
├── main.py           # 主程序
├── config.py         # 配置文件（窗口尺寸、按键映射、主题颜色等）
├── sprites.py        # 精灵图动画管理
├── sound.py          # 音效管理
├── images/           # 精灵图资源
│   ├── cat.png
│   ├── paw-left.png
│   ├── paw-right.png
│   ├── bongo.png
│   ├── keyboard.png
│   ├── tambourine.png
│   └── mouth.png
├── sounds/           # 音效文件
│   ├── bongo0.mp3
│   ├── bongo1.mp3
│   ├── keyboard0-9.mp3
│   ├── tambourine.mp3
│   └── meow.mp3
├── requirements.txt  # Python 依赖
├── run.bat           # Windows 启动脚本
├── run.sh            # Linux/Mac 启动脚本
└── README.md         # 项目说明
```

## 运行

```bash
# 创建虚拟环境（可选）
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

或者直接运行启动脚本：

```bash
# Windows
run.bat

# Linux/Mac
chmod +x run.sh
./run.sh
```

## 操作说明

| 按键 | 功能 |
| --- | --- |
| A / D | 敲击邦戈鼓（左/右） |
| 1-10 | 弹奏钢琴（10 个音符） |
| B | 敲击铃鼓 |
| 空格 | 猫叫 |
| Tab | 切换乐器 |
| R | 切换亮色/暗色模式 |
| F1 | 播放演示曲目 |
| F2 | 显示帮助 |
| Esc | 退出 |

## 致谢

- 灵感来源：[bongo.cat](https://bongo.cat/)
- 使用 [Pygame](https://www.pygame.org/) 开发
