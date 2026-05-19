# game/overworld.py
# Top-down overworld: rừng, cây, bụi cỏ, di chuyển WASD
import pygame as pg
from OpenGL.GL import *
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE, MAP_COLS, MAP_ROWS, PLAYER_SPEED
)

# ── Tile IDs ──────────────────────────────────────────────────────────────
T_GRASS   = 0   # Đất nền
T_TREE    = 1   # Cây (blocking)
T_BUSH    = 2   # Bụi cỏ #1 (Slime)
T_BUSH2   = 3   # Bụi cỏ #2 (Slime/Bee mix)
T_PATH    = 4   # Đường đi (safe)
T_BOSS    = 5   # Điểm boss

# ── Màu sắc tile ──────────────────────────────────────────────────────────
TILE_COLORS = {
    T_GRASS: (0.22, 0.55, 0.20),
    T_TREE:  (0.08, 0.30, 0.08),
    T_BUSH:  (0.30, 0.65, 0.15),
    T_BUSH2: (0.45, 0.70, 0.10),
    T_PATH:  (0.60, 0.50, 0.30),
    T_BOSS:  (0.60, 0.15, 0.10),
}

TREE_TRUNK = (0.35, 0.22, 0.08)
TREE_CROWN = (0.10, 0.40, 0.08)

# ── Bản đồ 30x22 ─────────────────────────────────────────────────────────
# X = Tree, . = Grass, 1 = Bush1(Slime), 2 = Bush2(Bee/Slime), P = Path, B = Boss
# Người chơi bắt đầu ở (2,10)
_RAW_MAP = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X............................X",
    "X....XXXXX.....XXXX..........X",
    "X....X.........X.............X",
    "X....X...11....X.....XXXXX...X",
    "X....X...11....X.............X",
    "X....XXXXX.....X.............X",
    "X..............X..22222......X",
    "X..............X..22222......X",
    "X..PP..........X.............X",
    "X..PP..........PPPPPPPPPP....X",
    "X..PP..XXXXXXXXX.............X",
    "X..PP..X.....................X",
    "X..PPPPX.....................X",
    "X......X.............XXXXX...X",
    "X......XXXXXXXXX.............X",
    "X............................X",
    "X.....PPPPPPPPPPPPPPPPPPPB...X",
    "X............................X",
    "X............................X",
    "X............................X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]

def _parse_map(raw):
    grid = []
    for row in raw:
        line = []
        for ch in row:
            if ch == 'X':
                line.append(T_TREE)
            elif ch == '1':
                line.append(T_BUSH)
            elif ch == '2':
                line.append(T_BUSH2)
            elif ch in ('P',):
                line.append(T_PATH)
            elif ch == 'B':
                line.append(T_BOSS)
            else:
                line.append(T_GRASS)
        grid.append(line)
    return grid

TILEMAP = _parse_map(_RAW_MAP)

def tile_at(col, row):
    if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
        return TILEMAP[row][col]
    return T_TREE  # ngoài biên = blocking


class OverworldPlayer:
    def __init__(self, col=2, row=10):
        # Vị trí theo pixel (tính từ góc dưới-trái OpenGL)
        self.px = col * TILE + TILE // 2
        self.py = (MAP_ROWS - 1 - row) * TILE + TILE // 2
        self.w  = TILE - 8
        self.h  = TILE - 8
        self.anim_timer = 0
        self.frame      = 0
        self.moving     = False

    def col(self): return int(self.px // TILE)
    def row(self): return MAP_ROWS - 1 - int(self.py // TILE)

    def update(self, keys):
        dx = dy = 0
        if keys[pg.K_a] or keys[pg.K_LEFT]:  dx = -PLAYER_SPEED
        if keys[pg.K_d] or keys[pg.K_RIGHT]: dx =  PLAYER_SPEED
        if keys[pg.K_w] or keys[pg.K_UP]:    dy =  PLAYER_SPEED
        if keys[pg.K_s] or keys[pg.K_DOWN]:  dy = -PLAYER_SPEED

        self.moving = (dx != 0 or dy != 0)

        # Di chuyển từng trục để tránh kẹt góc
        new_x = self.px + dx
        if not self._blocked_at(new_x, self.py):
            self.px = new_x
        new_y = self.py + dy
        if not self._blocked_at(self.px, new_y):
            self.py = new_y

        # Clamp
        margin = self.w // 2
        self.px = max(margin, min(MAP_COLS * TILE - margin, self.px))
        self.py = max(margin, min(MAP_ROWS * TILE - margin, self.py))

        self.anim_timer += 1
        if self.moving and self.anim_timer % 12 == 0:
            self.frame = (self.frame + 1) % 2

    def _blocked_at(self, wx, wy):
        half = (self.w // 2) - 2
        for corner_x, corner_y in [
            (wx - half, wy - half), (wx + half, wy - half),
            (wx - half, wy + half), (wx + half, wy + half),
        ]:
            c = int(corner_x // TILE)
            r = MAP_ROWS - 1 - int(corner_y // TILE)
            if tile_at(c, r) == T_TREE:
                return True
        return False

    def current_tile(self):
        return tile_at(self.col(), self.row())


def _draw_tile_quad(x, y, w, h_or_color, color=None):
    """Vẽ quad: (x,y,w,h,color) hoặc dạng cũ (x,y,size,color)."""
    if color is None:
        # gọi kiểu cũ: _draw_tile_quad(x,y,size,color)
        h = w
        color = h_or_color
    else:
        h = h_or_color
    glDisable(GL_TEXTURE_2D)
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    glColor3f(1, 1, 1)


def _draw_tree(x, y, tile):
    # Thân cây
    tw = tile * 0.4
    th = tile * 0.45
    tx = x + tile * 0.3
    ty = y
    _draw_tile_quad(tx, ty, tw, th, TREE_TRUNK)
    # Tán lá
    cw = tile * 0.9
    ch = tile * 0.7
    cx = x + tile * 0.05
    cy = y + tile * 0.30
    _draw_tile_quad(cx, cy, cw, ch, TREE_CROWN)


def draw_overworld(player, text_ren, cam_x=0, cam_y=0):
    """Vẽ toàn bộ overworld map + player."""
    # Nền
    glClearColor(0.10, 0.25, 0.08, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    # Camera center trên player
    view_x = player.px - SCREEN_WIDTH  // 2
    view_y = player.py - SCREEN_HEIGHT // 2

    # Clamp camera
    view_x = max(0, min(MAP_COLS * TILE - SCREEN_WIDTH,  view_x))
    view_y = max(0, min(MAP_ROWS * TILE - SCREEN_HEIGHT, view_y))

    glPushMatrix()
    glTranslatef(-view_x, -view_y, 0)

    # Vẽ tiles
    trees = []  # Cây vẽ sau cùng (lớp trên)
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            t = TILEMAP[row][col]
            x = col * TILE
            y = (MAP_ROWS - 1 - row) * TILE
            if t == T_TREE:
                trees.append((x, y))
            else:
                _draw_tile_quad(x, y, TILE, TILE_COLORS[t])
                # Viền bụi cỏ
                if t in (T_BUSH, T_BUSH2):
                    _draw_bush_detail(x, y, t)

    for (x, y) in trees:
        _draw_tile_quad(x, y, TILE, TILE_COLORS[T_TREE])
        _draw_tree(x, y, TILE)

    # Vẽ player (hình thỏ đơn giản = hình chữ nhật + tai)
    px = player.px - player.w // 2
    py = player.py - player.h // 2
    _draw_tile_quad(px, py, player.w, player.h, (0.9, 0.85, 0.8))
    # Tai
    ear_w = player.w * 0.2
    ear_h = player.h * 0.45
    _draw_tile_quad(px + player.w * 0.15, py + player.h, ear_w, ear_h, (0.9, 0.80, 0.80))
    _draw_tile_quad(px + player.w * 0.60, py + player.h, ear_w, ear_h, (0.9, 0.80, 0.80))

    glPopMatrix()

    # HUD
    text_ren.draw_text("WASD: Di chuyển  |  Đi vào bụi cỏ để gặp quái",
                        SCREEN_WIDTH // 2, 12, size=15, color=(200, 230, 200), center_x=True)


def _draw_bush_detail(x, y, bush_type):
    glDisable(GL_TEXTURE_2D)
    n_blades = 5
    import math
    for i in range(n_blades):
        bx = x + 4 + i * (TILE - 8) / max(n_blades - 1, 1)
        by = y + 2
        bh = TILE * 0.4 + math.sin(i * 1.5) * 4
        bw = 3
        c = (0.20, 0.70, 0.10) if bush_type == T_BUSH else (0.40, 0.75, 0.05)
        glColor3f(*c)
        glBegin(GL_QUADS)
        glVertex2f(bx, by)
        glVertex2f(bx + bw, by)
        glVertex2f(bx + bw // 2 + 1, by + bh)
        glVertex2f(bx - 1, by + bh)
        glEnd()
    glColor3f(1, 1, 1)
    glEnable(GL_TEXTURE_2D)
