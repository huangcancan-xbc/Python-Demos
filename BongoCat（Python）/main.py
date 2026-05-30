"""主程序

功能：精灵图动画 / 多乐器音效 / 键盘鼠标输入 / 演示曲目 / 暗色模式 / 帮助系统

操作：邦戈鼓 A/D，钢琴 1-0，铃鼓 B，喵叫 空格
      Tab 切换乐器，R 暗色模式，F1 演示，F2 帮助，Esc 退出
"""

import sys
import os
import time
import pygame
from config import (
    WIDTH, HEIGHT, SPRITE_Y, FPS, INSTRUMENTS, INSTRUMENT_CN,
    KEY_MAP, KEY_HINTS, LEFT_PAW_KEYS, MOUSE_MAP,
    BG_LIGHT, BG_DARK, TEXT_LIGHT, TEXT_DARK, PANEL_LIGHT, PANEL_DARK,
)
from sprites import Sprites
from sound import SoundManager


# ── 字体 ────────────────────────────────────────────────────────────────

_CN_FONT_NAMES = [
    "microsoftyahei", "microsoftyaheimonopoly", "simhei",
    "simsun", "dengxian", "nsimsun", "fangsong", "kaiti",
]
_CN_FONT_FILES: list[str] = []
if sys.platform == "win32":
    _CN_FONT_FILES = [
        "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/dengxian.ttf",
    ]
_font_cache: dict[tuple[int, bool], pygame.font.Font] = {}


def _make_font(size: int, bold: bool = False) -> pygame.font.Font:
    cache_key = (size, bold)
    if cache_key in _font_cache:
        return _font_cache[cache_key]
    for name in _CN_FONT_NAMES:
        try:
            font = pygame.font.SysFont(name, size, bold=bold)
            if font.render("测", True, (0, 0, 0)).get_width() > 5:
                _font_cache[cache_key] = font
                return font
        except Exception:
            continue
    for fpath in _CN_FONT_FILES:
        if os.path.exists(fpath):
            try:
                font = pygame.font.Font(fpath, size)
                if bold:
                    font.set_bold(True)
                if font.render("测", True, (0, 0, 0)).get_width() > 5:
                    _font_cache[cache_key] = font
                    return font
            except Exception:
                continue
    font = pygame.font.Font(None, size)
    if bold:
        font.set_bold(True)
    _font_cache[cache_key] = font
    return font


# ── 按键映射表（直接用 pygame key 常量，零转换）────────────────────────

# event.key → 虚拟按键字符串（只映射实际使用的键）
_KEY_CONST_MAP = {
    pygame.K_a: "a", pygame.K_d: "d", pygame.K_b: "b",
    pygame.K_SPACE: "space",
    pygame.K_0: "0", pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3",
    pygame.K_4: "4", pygame.K_5: "5", pygame.K_6: "6", pygame.K_7: "7",
    pygame.K_8: "8", pygame.K_9: "9",
    # 小键盘数字
    pygame.K_KP0: "0", pygame.K_KP1: "1", pygame.K_KP2: "2",
    pygame.K_KP3: "3", pygame.K_KP4: "4", pygame.K_KP5: "5",
    pygame.K_KP6: "6", pygame.K_KP7: "7", pygame.K_KP8: "8",
    pygame.K_KP9: "9",
}

# ── 常量 ────────────────────────────────────────────────────────────────

PAW_HOLD_MS = 150

DEMO_SONG = [
    (0, "1"), (200, "1"), (200, "6"), (200, "6"),
    (200, "7"), (200, "7"), (400, "6"),
    (200, "5"), (200, "5"), (200, "4"), (200, "4"),
    (200, "3"), (200, "3"), (400, "1"),
    (200, "6"), (200, "6"), (200, "5"), (200, "5"),
    (200, "4"), (200, "4"), (400, "3"),
    (200, "6"), (200, "6"), (200, "5"), (200, "5"),
    (200, "4"), (200, "4"), (400, "3"),
    (200, "1"), (200, "1"), (200, "6"), (200, "6"),
    (200, "7"), (200, "7"), (400, "6"),
    (200, "5"), (200, "5"), (200, "4"), (200, "4"),
    (200, "3"), (200, "3"), (400, "1"),
    (500, "space"),
]


def _draw_rounded_rect(surface, color, rect, radius=8):
    x, y, w, h = rect
    r = min(radius, w // 2, h // 2)
    pygame.draw.rect(surface, color, (x + r, y, w - 2 * r, h))
    pygame.draw.rect(surface, color, (x, y + r, w, h - 2 * r))
    for cx, cy in [(x+r, y+r), (x+w-r, y+r), (x+r, y+h-r), (x+w-r, y+h-r)]:
        pygame.draw.circle(surface, color, (cx, cy), r)


# ── 主应用 ──────────────────────────────────────────────────────────────

class BongoCatApp:

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("邦戈猫 - Bongo Cat")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.key.stop_text_input()  # 阻止输入法拦截字母键
        self.clock = pygame.time.Clock()

        self.sprites = Sprites()
        self.sound = SoundManager()
        self.sound.load_all()

        self.font = _make_font(16)
        self.font_sm = _make_font(13)
        self.font_title = _make_font(20, True)
        self.font_big = _make_font(26, True)

        self.running = True
        self.dark_mode = False
        self.current_instrument = 0
        self.pressed: set[str] = set()
        self._left_paw_ts: float = 0
        self._right_paw_ts: float = 0
        self._sound_idx: dict[str, int] = {n: 0 for n in INSTRUMENTS}

        self._demo_active = False
        self._demo_step = 0
        self._demo_next_ts: float = 0
        self._demo_held_key: str | None = None

        self.show_help = False

    # ── 事件 ─────────────────────────────────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._on_key_down(event)
            elif event.type == pygame.KEYUP:
                self._on_key_up(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._on_mouse_down(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self._on_mouse_up(event)

    def _on_key_down(self, event):
        key = event.key

        # ── 功能键（直接匹配常量，最高优先级）─────────────────────────
        if key == pygame.K_ESCAPE:
            self.running = False
            return
        if key == pygame.K_TAB:
            self.current_instrument = (self.current_instrument + 1) % len(INSTRUMENTS)
            return
        if key == pygame.K_F1:
            self._toggle_demo()
            return
        if key == pygame.K_F2:
            self.show_help = not self.show_help
            return
        if key == pygame.K_r:
            self.dark_mode = not self.dark_mode
            return

        # ── 乐器按键（查表，无需任何转换）────────────────────────────
        vk = _KEY_CONST_MAP.get(key)
        if vk and vk in KEY_MAP and vk not in self.pressed and not self._demo_active:
            self.pressed.add(vk)
            inst, ki = KEY_MAP[vk]
            self._play(inst, ki, vk)

    def _on_key_up(self, event):
        vk = _KEY_CONST_MAP.get(event.key)
        if vk:
            self.pressed.discard(vk)

    def _on_mouse_down(self, event):
        if self._demo_active:
            return
        vk = MOUSE_MAP.get(event.button)
        if vk and vk not in self.pressed:
            self.pressed.add(vk)
            inst, ki = KEY_MAP[vk]
            self._play(inst, ki, vk)

    def _on_mouse_up(self, event):
        vk = MOUSE_MAP.get(event.button)
        if vk:
            self.pressed.discard(vk)

    def _play(self, instrument: str, key_index: int, vk: str | None = None):
        if instrument != "meow":
            if vk in LEFT_PAW_KEYS:
                self._left_paw_ts = time.monotonic()
            else:
                self._right_paw_ts = time.monotonic()
            self.current_instrument = INSTRUMENTS.index(instrument)
        if instrument in ("tambourine", "meow"):
            idx = self._sound_idx[instrument]
            self.sound.play(instrument, idx)
            self._sound_idx[instrument] = 1 - idx
        else:
            self.sound.play(instrument, key_index)

    # ── 演示 ─────────────────────────────────────────────────────────────

    def _toggle_demo(self):
        if self._demo_active:
            self._stop_demo()
        else:
            self._demo_active = True
            self._demo_step = 0
            self._demo_next_ts = 0
            self._demo_held_key = None

    def _stop_demo(self):
        self._demo_active = False
        self._demo_step = 0
        if self._demo_held_key:
            self.pressed.discard(self._demo_held_key)
            self._demo_held_key = None

    def _update_demo(self):
        if not self._demo_active:
            return
        if self._demo_step >= len(DEMO_SONG):
            self._stop_demo()
            return

        now_mono = time.monotonic()
        if self._demo_held_key:
            if self._demo_held_key in LEFT_PAW_KEYS:
                self._left_paw_ts = now_mono
            else:
                self._right_paw_ts = now_mono

        now = now_mono * 1000
        if self._demo_next_ts == 0:
            self._demo_next_ts = now + DEMO_SONG[0][0]
        if now < self._demo_next_ts:
            return

        if self._demo_held_key:
            self.pressed.discard(self._demo_held_key)
            self._demo_held_key = None

        delay, vk = DEMO_SONG[self._demo_step]
        self.pressed.add(vk)
        if vk in KEY_MAP:
            inst, ki = KEY_MAP[vk]
            self._play(inst, ki, vk)
        self._demo_held_key = vk

        self._demo_step += 1
        if self._demo_step < len(DEMO_SONG):
            self._demo_next_ts = now + DEMO_SONG[self._demo_step][0]

    # ── 渲染 ─────────────────────────────────────────────────────────────

    def _paw_is_down(self, is_left: bool) -> bool:
        if is_left:
            keys = LEFT_PAW_KEYS
        else:
            keys = set(KEY_MAP.keys()) - LEFT_PAW_KEYS - {"space"}
        if any(k in keys for k in self.pressed):
            return True
        ts = self._left_paw_ts if is_left else self._right_paw_ts
        return (time.monotonic() - ts) * 1000 < PAW_HOLD_MS

    def _draw(self):
        dark = self.dark_mode
        self.screen.fill(BG_DARK if dark else BG_LIGHT)

        instrument = INSTRUMENTS[self.current_instrument]
        any_pressed = len(self.pressed) > 0
        left_down = self._paw_is_down(True)
        right_down = self._paw_is_down(False)
        meow_down = "space" in self.pressed

        sy = SPRITE_Y
        # 暗色猫描边偏移量：暗色变体轮廓在帧内右偏 34px，渲染时左移补偿
        cat_ox = 0 if dark else 0
        if instrument != "meow":
            self.screen.blit(self.sprites.get(instrument, dark=False, active=any_pressed), (0, sy))
        self.screen.blit(self.sprites.get("cat", dark=dark), (cat_ox, sy))
        self.screen.blit(self.sprites.get("mouth", dark=dark, active=meow_down), (0, sy))
        self.screen.blit(self.sprites.get("paw-left", dark=dark, active=left_down), (0, sy))
        self.screen.blit(self.sprites.get("paw-right", dark=dark, active=right_down), (0, sy))

        self._draw_ui(instrument)

    def _draw_ui(self, instrument: str):
        dark = self.dark_mode
        tc = TEXT_DARK if dark else TEXT_LIGHT
        pc = PANEL_DARK if dark else PANEL_LIGHT
        hi = (255, 200, 50) if not dark else (100, 180, 255)

        # 顶部信息栏
        bar_h = 52
        bar = pygame.Surface((WIDTH, bar_h), pygame.SRCALPHA)
        bar.fill((*pc, 230))
        self.screen.blit(bar, (0, 0))
        pygame.draw.line(self.screen, hi, (0, bar_h), (WIDTH, bar_h), 2)

        cn = INSTRUMENT_CN.get(instrument, instrument)
        self.screen.blit(self.font_big.render(cn, True, hi if not dark else tc), (16, 10))

        hint = KEY_HINTS.get(instrument, "")
        lbl = self.font_sm.render("按键:", True, tc)
        self.screen.blit(lbl, (160, 10))
        self.screen.blit(self.font.render(hint, True, tc), (160 + lbl.get_width() + 4, 8))

        mode_label = "暗色模式" if dark else "亮色模式"
        ms = self.font_sm.render(f"[R] {mode_label}", True, tc)
        self.screen.blit(ms, (WIDTH - ms.get_width() - 16, 8))

        if self._demo_active:
            tip = self.font_sm.render("[F1] 演示播放中...", True, hi)
        else:
            tip = self.font_sm.render("[F1] 演示  [F2] 帮助", True, tc)
        self.screen.blit(tip, (WIDTH - tip.get_width() - 16, 28))

        # 底部面板
        lines = [
            ("快捷键说明", True),
            ("邦戈鼓: A/D   钢琴: 1-0   铃鼓: B   喵叫: 空格", False),
            ("Tab: 切换乐器   R: 暗色模式   F1: 演示   F2: 帮助", False),
        ]
        line_h = 22
        panel_h = len(lines) * line_h + 16
        panel_y = HEIGHT - panel_h - 6

        panel = pygame.Surface((WIDTH, panel_h), pygame.SRCALPHA)
        panel.fill((*pc, 210))
        self.screen.blit(panel, (0, panel_y))
        pygame.draw.line(self.screen, hi, (0, panel_y), (WIDTH, panel_y), 2)

        for i, (line, is_title) in enumerate(lines):
            font = self.font_title if is_title else self.font_sm
            surf = font.render(line, True, tc)
            x = (WIDTH - surf.get_width()) // 2 if is_title else 16
            self.screen.blit(surf, (x, panel_y + 8 + i * line_h))

        # 按键可视化
        if self.pressed:
            vy = panel_y - 32
            vx = 16
            for vk in sorted(self.pressed):
                label = f" {vk.upper()} "
                ls = self.font_sm.render(label, True, (0, 0, 0))
                bw, bh = ls.get_width() + 8, ls.get_height() + 6
                box = pygame.Surface((bw, bh), pygame.SRCALPHA)
                _draw_rounded_rect(box, (*hi, 200), pygame.Rect(0, 0, bw, bh), 6)
                self.screen.blit(box, (vx, vy))
                self.screen.blit(ls, (vx + 4, vy + 3))
                vx += bw + 6

        if self.show_help:
            self._draw_help_overlay()

    def _draw_help_overlay(self):
        dark = self.dark_mode
        tc = TEXT_DARK if dark else TEXT_LIGHT
        hi = (255, 200, 50) if not dark else (100, 180, 255)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 500, 320
        bx = (WIDTH - box_w) // 2
        by = (HEIGHT - box_h) // 2

        bg_c = (30, 30, 35, 245) if dark else (250, 250, 250, 245)
        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill(bg_c)
        self.screen.blit(box, (bx, by))
        pygame.draw.rect(self.screen, hi, (bx, by, box_w, box_h), 2)

        title = self.font_big.render("邦戈猫 — 操作说明", True, hi)
        self.screen.blit(title, (bx + (box_w - title.get_width()) // 2, by + 14))

        sep_y = by + 48
        pygame.draw.line(self.screen, hi, (bx + 20, sep_y), (bx + box_w - 20, sep_y), 1)

        lines = [
            ("乐器", ""),
            ("邦戈鼓", "A / D  （或鼠标左右键）"),
            ("钢琴", "1 2 3 4 5 6 7 8 9 0"),
            ("铃鼓", "B"),
            ("喵叫", "空格键  （或鼠标中键）"),
            ("", ""),
            ("功能", ""),
            ("Tab", "切换乐器"),
            ("R", "切换暗色 / 亮色模式"),
            ("F1", "演示"),
            ("F2", "帮助"),
            ("Esc", "退出"),
        ]

        y = sep_y + 12
        for left, right in lines:
            if left == "" and right == "":
                y += 6
                continue
            if right == "":
                # 分组标题
                self.screen.blit(self.font_title.render(left, True, hi), (bx + 24, y))
                y += 26
                continue
            self.screen.blit(self.font.render(left, True, hi), (bx + 30, y))
            self.screen.blit(self.font.render(right, True, tc), (bx + 160, y))
            y += 22

        close_s = self.font_sm.render("按 F2 关闭", True, tc)
        self.screen.blit(close_s, (bx + (box_w - close_s.get_width()) // 2, by + box_h - 28))

    # ── 主循环 ───────────────────────────────────────────────────────────

    def run(self):
        while self.running:
            self._handle_events()
            self._update_demo()
            self._draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        self.sound.cleanup()
        pygame.quit()


def main():
    BongoCatApp().run()


if __name__ == "__main__":
    main()
