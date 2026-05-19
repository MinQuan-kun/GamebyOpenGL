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
T_FENCE_H = 6   # Hàng rào ngang
T_HOUSE   = 7   # Nhà
T_FENCE_V = 8   # Hàng rào dọc

# ── Màu sắc tile ──────────────────────────────────────────────────────────
TILE_COLORS = {
    T_GRASS: (0.22, 0.55, 0.20),
    T_TREE:  (0.08, 0.30, 0.08),
    T_BUSH:  (0.30, 0.65, 0.15),
    T_BUSH2: (0.45, 0.70, 0.10),
    T_PATH:  (0.60, 0.50, 0.30),
    T_BOSS:  (0.60, 0.15, 0.10),
    T_FENCE_H: (0.50, 0.35, 0.20),
    T_HOUSE: (0.40, 0.40, 0.50),
    T_FENCE_V: (0.50, 0.35, 0.20),
}

TREE_TRUNK = (0.35, 0.22, 0.08)
TREE_CROWN = (0.10, 0.40, 0.08)

# ── Bản đồ 30x22 ─────────────────────────────────────────────────────────
# X = Tree, . = Grass, 1 = Bush1(Slime), 2 = Bush2(Bee/Slime), P = Path, B = Boss
# Người chơi bắt đầu ở (2,10)
_RAW_MAP = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "XXXXXXXXX      B    XXXXXXXXXX",
    "XXXXXXXXX      H    XXXXXXXXXX",
    "XXXXXXXXX    PPPP   XXXXXXXXXX",
    "XXXXXXXXX    |PP|   XXXXXXXXXX",
    "XXXXXXXXX    |PP|   ---XXXXXXX",
    "XXXXXXXXX    |PP|   P2|XXXXXXX",
    "XXXXXXXXX    |PP|   P2|XXXXXXX",
    "XXXXXXXXX    |PPPPPPP2|XXXXXXX",
    "XXXXXXXXX    |PP|---|2|XXXXXXX",
    "XXXXXXXXX    |PP|   ---XXXXXXX",
    "XXXXXXXXX    |PP|   XXXXXXXXXX",
    "---XXXXXX    |PP|   XXXXXXXXXX",
    "11|XXXXXX    |PP|   XXXXXXXXXX",
    "11PPPPPPPPPPPPPP|   XXXXXXXXXX",
    "11|XXXXXX    |PP|   XXXXXXXXXX",
    "---XXXXXX    |PP|   XXXXXXXXXX",
    "XXXXXXXXX    |PP|   XXXXXXXXXX",
    "XXXXXXXXX    |PP|   XXXXXXXXXX",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
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
            elif ch == '-':
                line.append(T_FENCE_H)
            elif ch == '|':
                line.append(T_FENCE_V)
            elif ch == 'H':
                line.append(T_HOUSE)
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
    def __init__(self, col=14, row=18):
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
            t = tile_at(c, r)
            if t in (T_TREE, T_FENCE_H, T_FENCE_V, T_HOUSE):
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


def _draw_fence(x, y, size, is_horizontal=True):
    """Vẽ hàng rào gỗ chéo/thẳng bằng OpenGL."""
    glColor4f(0.4, 0.25, 0.1, 1.0)
    glBegin(GL_QUADS)
    if is_horizontal:
        # Cọc dọc
        glVertex2f(x + size*0.2, y + size*0.1)
        glVertex2f(x + size*0.3, y + size*0.1)
        glVertex2f(x + size*0.3, y + size*0.9)
        glVertex2f(x + size*0.2, y + size*0.9)

        glVertex2f(x + size*0.7, y + size*0.1)
        glVertex2f(x + size*0.8, y + size*0.1)
        glVertex2f(x + size*0.8, y + size*0.9)
        glVertex2f(x + size*0.7, y + size*0.9)
        glEnd()

        # Thanh ngang
        glColor4f(0.5, 0.35, 0.2, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(x, y + size*0.3)
        glVertex2f(x + size, y + size*0.3)
        glVertex2f(x + size, y + size*0.4)
        glVertex2f(x, y + size*0.4)
        
        glVertex2f(x, y + size*0.6)
        glVertex2f(x + size, y + size*0.6)
        glVertex2f(x + size, y + size*0.7)
        glVertex2f(x, y + size*0.7)
    else:
        # Cọc ngang
        glVertex2f(x + size*0.1, y + size*0.2)
        glVertex2f(x + size*0.1, y + size*0.3)
        glVertex2f(x + size*0.9, y + size*0.3)
        glVertex2f(x + size*0.9, y + size*0.2)

        glVertex2f(x + size*0.1, y + size*0.7)
        glVertex2f(x + size*0.1, y + size*0.8)
        glVertex2f(x + size*0.9, y + size*0.8)
        glVertex2f(x + size*0.9, y + size*0.7)
        glEnd()

        # Thanh dọc
        glColor4f(0.5, 0.35, 0.2, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(x + size*0.3, y)
        glVertex2f(x + size*0.4, y)
        glVertex2f(x + size*0.4, y + size)
        glVertex2f(x + size*0.3, y + size)
        
        glVertex2f(x + size*0.6, y)
        glVertex2f(x + size*0.7, y)
        glVertex2f(x + size*0.7, y + size)
        glVertex2f(x + size*0.6, y + size)
    glEnd()


def draw_overworld(player, text_ren, cam_x=0, cam_y=0, renderers=None):
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

    # Lấy renderers
    grass_ren = renderers.get("grass") if renderers else None
    path_ren = renderers.get("path") if renderers else None
    fence_h_ren = renderers.get("fence_h") if renderers else None
    fence_v_ren = renderers.get("fence_v") if renderers else None
    
    # Không dùng tree và house renderer nữa theo yêu cầu
    tree_ren = None
    house_ren = None
    map_bg_ren = None

    # Lựa chọn 2: Vẽ tiles rời rạc
    trees = []
    houses = []
    fences = []
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            t = TILEMAP[row][col]
            x = col * TILE
            y = (MAP_ROWS - 1 - row) * TILE
            
            # Luôn vẽ cỏ làm nền dưới cùng
            if grass_ren:
                grass_ren.draw(x, y, TILE, TILE, 0)
            else:
                _draw_tile_quad(x, y, TILE, TILE_COLORS[T_GRASS])
                
            if t == T_TREE:
                trees.append((x, y))
            elif t == T_HOUSE:
                pass # houses.append((x, y)) - Ẩn nhà tạm thời
            elif t in (T_FENCE_H, T_FENCE_V):
                fences.append((x, y, t))
            elif t == T_PATH or t == T_BOSS:
                if path_ren:
                    path_ren.draw(x, y, TILE, TILE, 0)
                else:
                    _draw_tile_quad(x, y, TILE, TILE_COLORS[T_PATH])
            elif t in (T_BUSH, T_BUSH2):
                _draw_bush_detail(x, y, t)

    for (x, y, t_type) in fences:
        _draw_fence(x, y, TILE, is_horizontal=(t_type == T_FENCE_H))

    for (x, y) in houses:
        if house_ren:
            # Chỉnh kích thước to ra
            house_ren.draw(int(x - TILE*0.5), int(y), int(TILE*2), int(TILE*2), 0)
        else:
            _draw_tile_quad(x, y, TILE, TILE_COLORS[T_HOUSE])

    for (x, y) in trees:
        if tree_ren:
            tree_ren.draw(int(x - TILE*0.25), int(y), int(TILE*1.5), int(TILE*1.5), 0)
        else:
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
