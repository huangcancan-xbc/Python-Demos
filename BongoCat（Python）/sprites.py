"""精灵图加载模块

负责从 images/ 目录加载所有精灵图（sprite sheet），
并按帧提取为独立的 Surface 对象供主程序渲染使用。

精灵图布局说明：
    每张精灵图尺寸为 1600 x 900 像素，包含 4 帧：
    - 左上 (0, 0)     : 亮色主题 - 静止状态
    - 右上 (800, 0)    : 亮色主题 - 动作状态（爪子按下/嘴巴张开）
    - 左下 (0, 450)    : 暗色主题 - 静止状态
    - 右下 (800, 450)  : 暗色主题 - 动作状态

    部分精灵图仅包含单帧（800 x 450），缺失的帧会自动回退到主帧。

加载的精灵图列表（7 张）：
    cat, mouth, paw-left, paw-right, bongo, keyboard, tambourine
"""

import pygame
from config import ASSET_DIR

FRAME_W, FRAME_H = 800, 450


def _load_sheet(name: str) -> pygame.Surface:
    path = ASSET_DIR / f"{name}.png"
    img = pygame.image.load(str(path))
    return img.convert_alpha() if img.get_flags() & pygame.SRCALPHA else img.convert()


def _extract_frames(sheet: pygame.Surface) -> list[pygame.Surface]:
    """提取 4 帧，缺失帧用同主题静态帧或主帧填充。

    返回顺序：[亮色静止, 亮色动作, 暗色静止, 暗色动作]
    """
    frames: list[pygame.Surface] = []
    sheet_rect = sheet.get_rect()

    for y in (0, FRAME_H):
        for x in (0, FRAME_W):
            rect = pygame.Rect(x, y, FRAME_W, FRAME_H)
            clipped = rect.clip(sheet_rect)
            frame = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), clipped)
            frames.append(frame)

    # 回退链：缺失帧 → 同主题静态帧 → 亮色静态帧
    for idx in range(4):
        if _is_empty(frames[idx]):
            fallback = (idx & 2)  # 同主题静态帧 (0=亮色, 2=暗色)
            if not _is_empty(frames[fallback]):
                frames[idx] = frames[fallback]
            else:
                frames[idx] = frames[0]

    return frames


def _is_empty(frame: pygame.Surface) -> bool:
    """检查帧是否完全没有可见像素（采样检测）。"""
    w, h = frame.get_size()
    step = 8
    try:
        for y in range(0, h, step):
            for x in range(0, w, step):
                if frame.get_at((x, y)).a > 0:
                    return False
    except IndexError:
        return True
    return True


class Sprites:

    NAMES = ("cat", "mouth", "paw-left", "paw-right",
             "bongo", "keyboard", "tambourine")

    def __init__(self):
        self.data: dict[str, list[pygame.Surface]] = {}
        for name in self.NAMES:
            self.data[name] = _extract_frames(_load_sheet(name))

    def get(self, name: str, dark: bool = False, active: bool = False) -> pygame.Surface:
        """获取指定精灵的对应帧，缺失帧自动回退。"""
        idx = (2 if dark else 0) + (1 if active else 0)
        return self.data[name][idx]
