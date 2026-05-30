"""音效管理模块

负责预加载所有乐器音效文件到内存，并提供低延迟播放接口。

音效文件为 MP3 格式，存放在项目的 sounds/ 目录中。
使用 pygame.mixer 进行音频播放，配置 32 个声道以支持快速连击
时不丢失音效。简单乐器（铃鼓、喵叫）加载两份副本以支持重叠播放。

音效列表（16 个）：
    - bongo0, bongo1         邦戈鼓左击、右击
    - keyboard0 ~ keyboard9  钢琴 10 个音阶
    - tambourine0, 1         铃鼓（双副本）
    - meow0, 1               喵叫（双副本）
"""

import pygame
from config import SOUND_DIR


class SoundManager:
    """音效管理器，负责音效的加载和播放。

    使用方法：
        mgr = SoundManager()
        mgr.load_all()            # 启动时预加载
        mgr.play("bongo", 0)     # 播放邦戈左击
        mgr.cleanup()             # 退出时释放
    """

    def __init__(self):
        """初始化混音器，分配 32 个声道。"""
        pygame.mixer.set_num_channels(32)
        # 存储已加载音效：键 = "乐器名+索引"，值 = Sound 对象
        self._sounds: dict[str, pygame.mixer.Sound] = {}

    def _load(self, tag: str, filename: str):
        """加载单个音效文件。若文件不存在则静默跳过。"""
        path = SOUND_DIR / filename
        if path.exists():
            self._sounds[tag] = pygame.mixer.Sound(str(path))

    def load_all(self):
        """预加载全部音效（程序启动时调用一次）。"""
        # 邦戈鼓：2 个击打音效
        for i in range(2):
            self._load(f"bongo{i}", f"bongo{i}.mp3")
        # 钢琴：10 个音阶音效
        for i in range(10):
            self._load(f"keyboard{i}", f"keyboard{i}.mp3")
        # 简单乐器：各加载 2 份副本，交替播放以支持快速重叠
        for name in ("tambourine", "meow"):
            self._load(f"{name}0", f"{name}.mp3")
            self._load(f"{name}1", f"{name}.mp3")

    def play(self, instrument: str, key_index: int):
        """播放指定乐器的音效。

        Args:
            instrument: 乐器名（如 "bongo", "meow"）
            key_index:  音效索引（邦戈/钢琴用实际索引，简单乐器用 0/1 交替）
        """
        tag = f"{instrument}{key_index}"
        snd = self._sounds.get(tag)
        if snd:
            snd.play()

    def cleanup(self):
        """释放所有已加载的音效资源。"""
        self._sounds.clear()
