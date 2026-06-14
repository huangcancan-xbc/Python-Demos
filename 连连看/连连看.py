import pygame
import random
import sys
from typing import List, Tuple, Optional
import os

# 初始化pygame
pygame.init()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (230, 230, 230)

# 5种图案颜色
COLORS = [
    (255, 80, 80),    # 红色
    (80, 200, 80),    # 绿色
    (80, 80, 255),    # 蓝色
    (255, 200, 40),   # 黄色
    (200, 80, 200),   # 紫色
]

# 游戏常数
CELL_SIZE = 70
BOARD_ROWS = 8
BOARD_COLS = 8
MARGIN = 50
WINDOW_WIDTH = BOARD_COLS * CELL_SIZE + 2 * MARGIN
WINDOW_HEIGHT = BOARD_ROWS * CELL_SIZE + 2 * MARGIN + 100

def get_chinese_font(size):
    """获取支持中文的字体"""
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return pygame.font.Font(font_path, size)
            except:
                continue
    
    try:
        return pygame.font.SysFont("microsoftyaheiui", size)
    except:
        return pygame.font.Font(None, size)

class LianLianKan:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("连连看")
        self.clock = pygame.time.Clock()
        self.font = get_chinese_font(28)
        self.small_font = get_chinese_font(20)
        
        self.board: List[List[int]] = []
        self.selected: Optional[Tuple[int, int]] = None
        self.matched: List[Tuple[int, int]] = []
        self.score = 0
        self.game_won = False
        self.message = ""
        self.message_timer = 0
        
        self.init_board()
    
    def init_board(self):
        """初始化游戏棋盘"""
        # 8x8=64格子，32对图案，5种颜色，每种颜色6-7对
        # 使用 0-4 表示5种颜色
        num_pairs = (BOARD_ROWS * BOARD_COLS) // 2  # 32对
        pairs = []
        for i in range(num_pairs):
            pairs.append(i % 5)  # 5种颜色循环
        
        # 每种颜色需要成对出现
        pairs = pairs * 2  # 64个
        random.shuffle(pairs)
        
        # 填充棋盘
        self.board = []
        index = 0
        for row in range(BOARD_ROWS):
            board_row = []
            for col in range(BOARD_COLS):
                board_row.append(pairs[index])
                index += 1
            self.board.append(board_row)
        
        self.selected = None
        self.matched = []
        self.score = 0
        self.game_won = False
        self.message = ""
        self.message_timer = 0
    
    def is_cell_empty(self, row: int, col: int) -> bool:
        """检查格子是否为空（已被消除）"""
        return (row, col) in self.matched
    
    def is_cell_blocked(self, row: int, col: int) -> bool:
        """检查格子是否被占用（未被消除）"""
        return (row, col) not in self.matched
    
    def draw_shape(self, surface, x, y, size, color, shape_type):
        """绘制不同形状"""
        cx, cy = x + size // 2, y + size // 2
        r = size // 3
        
        if shape_type == 0:  # 圆形
            pygame.draw.circle(surface, color, (cx, cy), r)
            pygame.draw.circle(surface, BLACK, (cx, cy), r, 2)
        elif shape_type == 1:  # 方形
            rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BLACK, rect, 2)
        elif shape_type == 2:  # 三角形
            points = [(cx, cy - r), (cx - r, cy + r), (cx + r, cy + r)]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 2)
        elif shape_type == 3:  # 菱形
            points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 2)
        elif shape_type == 4:  # 五角星
            import math
            points = []
            for i in range(5):
                angle = math.radians(i * 72 - 90)
                points.append((cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))
                angle = math.radians(i * 72 - 90 + 36)
                points.append((cx + int(r * 0.4 * math.cos(angle)), cy + int(r * 0.4 * math.sin(angle))))
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 2)
    
    def draw_cell(self, row: int, col: int, selected: bool = False):
        """绘制单个格子"""
        x = MARGIN + col * CELL_SIZE
        y = MARGIN + row * CELL_SIZE
        
        # 绘制背景
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        if selected:
            pygame.draw.rect(self.screen, (255, 255, 150), rect)  # 选中高亮
        else:
            pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
        pygame.draw.rect(self.screen, BLACK, rect, 2)
        
        # 绘制图案
        pattern_id = self.board[row][col]
        color = COLORS[pattern_id]
        self.draw_shape(self.screen, x, y, CELL_SIZE, color, pattern_id)
    
    def draw_board(self):
        """绘制整个棋盘"""
        self.screen.fill(WHITE)
        
        # 绘制标题
        title = self.font.render("连连看", True, BLACK)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 25))
        self.screen.blit(title, title_rect)
        
        # 绘制分数
        score_text = self.small_font.render(f"分数: {self.score}", True, BLACK)
        self.screen.blit(score_text, (MARGIN, MARGIN - 35))
        
        # 绘制棋盘
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if not self.is_cell_empty(row, col):
                    selected = self.selected == (row, col)
                    self.draw_cell(row, col, selected)
        
        # 绘制消息
        if self.message and self.message_timer > 0:
            msg_text = self.small_font.render(self.message, True, (255, 0, 0))
            msg_rect = msg_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80))
            self.screen.blit(msg_text, msg_rect)
            self.message_timer -= 1
        
        # 绘制游戏胜利信息
        if self.game_won:
            win_text = self.font.render("恭喜你赢了！", True, (0, 150, 0))
            text_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80))
            self.screen.blit(win_text, text_rect)
        
        # 绘制重新开始按钮
        restart_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 50, 120, 40)
        pygame.draw.rect(self.screen, GRAY, restart_rect)
        pygame.draw.rect(self.screen, BLACK, restart_rect, 2)
        restart_text = self.small_font.render("重新开始", True, BLACK)
        text_rect = restart_text.get_rect(center=restart_rect.center)
        self.screen.blit(restart_text, text_rect)
        
        return restart_rect
    
    def get_cell_from_pos(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """根据鼠标位置获取格子坐标"""
        x, y = pos
        col = (x - MARGIN) // CELL_SIZE
        row = (y - MARGIN) // CELL_SIZE
        
        if 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS:
            return (row, col)
        return None
    
    def can_connect_line(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """检查两点之间直线是否通畅"""
        r1, c1 = pos1
        r2, c2 = pos2
        
        if r1 == r2:  # 同一行
            min_c, max_c = min(c1, c2), max(c1, c2)
            for c in range(min_c + 1, max_c):
                if self.is_cell_blocked(r1, c):
                    return False
            return True
        
        if c1 == c2:  # 同一列
            min_r, max_r = min(r1, r2), max(r1, r2)
            for r in range(min_r + 1, max_r):
                if self.is_cell_blocked(r, c1):
                    return False
            return True
        
        return False
    
    def is_path_clear(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """检查两个位置之间是否可以用不超过两个转弯的直线连接"""
        r1, c1 = pos1
        r2, c2 = pos2
        
        # 0个转弯：直线连接
        if self.can_connect_line(pos1, pos2):
            return True
        
        # 1个转弯：L形连接
        # 转折点1: (r1, c2)
        if self.is_cell_empty(r1, c2):
            if self.can_connect_line(pos1, (r1, c2)) and self.can_connect_line((r1, c2), pos2):
                return True
        
        # 转折点2: (r2, c1)
        if self.is_cell_empty(r2, c1):
            if self.can_connect_line(pos1, (r2, c1)) and self.can_connect_line((r2, c1), pos2):
                return True
        
        # 2个转弯：Z形/U形连接
        # 检查水平方向扩展（向上和向下）
        for r in range(-1, BOARD_ROWS + 1):
            if r == r1 or r == r2:
                continue
            
            # 检查转折点是否可用（棋盘外的位置总是可用）
            if r >= 0 and r < BOARD_ROWS:
                if not self.is_cell_empty(r, c1) or not self.is_cell_empty(r, c2):
                    continue
            
            # 检查路径是否通畅
            # 路径1: pos1 -> (r, c1)
            path1_ok = True
            if r >= 0 and r < BOARD_ROWS:
                path1_ok = self.can_connect_line(pos1, (r, c1))
            else:
                # 检查从pos1到边界是否通畅
                if r == -1:
                    for i in range(0, r1):
                        if self.is_cell_blocked(i, c1):
                            path1_ok = False
                            break
                else:  # r == BOARD_ROWS
                    for i in range(r1 + 1, BOARD_ROWS):
                        if self.is_cell_blocked(i, c1):
                            path1_ok = False
                            break
            
            if not path1_ok:
                continue
            
            # 路径2: (r, c1) -> (r, c2)
            path2_ok = True
            if r >= 0 and r < BOARD_ROWS:
                path2_ok = self.can_connect_line((r, c1), (r, c2))
            # 棋盘外的水平路径总是通畅的
            
            if not path2_ok:
                continue
            
            # 路径3: (r, c2) -> pos2
            path3_ok = True
            if r >= 0 and r < BOARD_ROWS:
                path3_ok = self.can_connect_line((r, c2), pos2)
            else:
                # 检查从pos2到边界是否通畅
                if r == -1:
                    for i in range(0, r2):
                        if self.is_cell_blocked(i, c2):
                            path3_ok = False
                            break
                else:  # r == BOARD_ROWS
                    for i in range(r2 + 1, BOARD_ROWS):
                        if self.is_cell_blocked(i, c2):
                            path3_ok = False
                            break
            
            if path1_ok and path2_ok and path3_ok:
                return True
        
        # 检查垂直方向扩展（向左和向右）
        for c in range(-1, BOARD_COLS + 1):
            if c == c1 or c == c2:
                continue
            
            # 检查转折点是否可用（棋盘外的位置总是可用）
            if c >= 0 and c < BOARD_COLS:
                if not self.is_cell_empty(r1, c) or not self.is_cell_empty(r2, c):
                    continue
            
            # 检查路径是否通畅
            # 路径1: pos1 -> (r1, c)
            path1_ok = True
            if c >= 0 and c < BOARD_COLS:
                path1_ok = self.can_connect_line(pos1, (r1, c))
            else:
                # 检查从pos1到边界是否通畅
                if c == -1:
                    for j in range(0, c1):
                        if self.is_cell_blocked(r1, j):
                            path1_ok = False
                            break
                else:  # c == BOARD_COLS
                    for j in range(c1 + 1, BOARD_COLS):
                        if self.is_cell_blocked(r1, j):
                            path1_ok = False
                            break
            
            if not path1_ok:
                continue
            
            # 路径2: (r1, c) -> (r2, c)
            path2_ok = True
            if c >= 0 and c < BOARD_COLS:
                path2_ok = self.can_connect_line((r1, c), (r2, c))
            # 棋盘外的垂直路径总是通畅的
            
            if not path2_ok:
                continue
            
            # 路径3: (r2, c) -> pos2
            path3_ok = True
            if c >= 0 and c < BOARD_COLS:
                path3_ok = self.can_connect_line((r2, c), pos2)
            else:
                # 检查从pos2到边界是否通畅
                if c == -1:
                    for j in range(0, c2):
                        if self.is_cell_blocked(r2, j):
                            path3_ok = False
                            break
                else:  # c == BOARD_COLS
                    for j in range(c2 + 1, BOARD_COLS):
                        if self.is_cell_blocked(r2, j):
                            path3_ok = False
                            break
            
            if path1_ok and path2_ok and path3_ok:
                return True
        
        return False
    
    def check_match(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """检查两个位置是否可以消除"""
        r1, c1 = pos1
        r2, c2 = pos2
        
        if pos1 == pos2:
            return False
        
        if self.board[r1][c1] != self.board[r2][c2]:
            return False
        
        if self.is_cell_empty(r1, c1) or self.is_cell_empty(r2, c2):
            return False
        
        return self.is_path_clear(pos1, pos2)
    
    def handle_click(self, pos: Tuple[int, int]):
        """处理鼠标点击"""
        if self.game_won:
            return
        
        restart_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 50, 120, 40)
        if restart_rect.collidepoint(pos):
            self.init_board()
            return
        
        cell = self.get_cell_from_pos(pos)
        if cell is None:
            return
        
        row, col = cell
        
        if self.is_cell_empty(row, col):
            return
        
        if self.selected is None:
            self.selected = cell
            return
        
        if self.selected == cell:
            self.selected = None
            return
        
        if self.check_match(self.selected, cell):
            self.matched.append(self.selected)
            self.matched.append(cell)
            self.score += 10
            self.selected = None
            self.message = ""
            
            if len(self.matched) == BOARD_ROWS * BOARD_COLS:
                self.game_won = True
        else:
            self.message = "无法连接！"
            self.message_timer = 60
            self.selected = cell
    
    def run(self):
        """运行游戏主循环"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)
            
            self.draw_board()
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

def main():
    game = LianLianKan()
    game.run()

if __name__ == "__main__":
    main()