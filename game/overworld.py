# game/overworld.py
# Top-down overworld: OpenGL map đẹp hơn, path liền mạch, không shadow, bụi cỏ tròn
import math
import pygame as pg
from OpenGL.GL import *
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE, MAP_COLS, MAP_ROWS, PLAYER_SPEED
)

# ── Tile IDs ──────────────────────────────────────────────────────────────
T_GRASS   = 0
T_TREE    = 1
T_BUSH    = 2
T_BUSH2   = 3
T_PATH    = 4
T_BOSS    = 5
T_FENCE_H = 6
T_HOUSE   = 7
T_FENCE_V = 8

# ── Màu sắc ───────────────────────────────────────────────────────────────
GRASS_BASE  = (0.20, 0.53, 0.19)
GRASS_ALT_1 = (0.18, 0.48, 0.17)
GRASS_ALT_2 = (0.23, 0.58, 0.21)
PATH_COL    = (0.63, 0.50, 0.30)
PATH_EDGE   = (0.48, 0.36, 0.18)
PATH_LIGHT  = (0.72, 0.60, 0.38)
TREE_TRUNK  = (0.34, 0.20, 0.08)
TREE_CROWN1 = (0.09, 0.34, 0.08)
TREE_CROWN2 = (0.12, 0.45, 0.10)
TREE_CROWN3 = (0.16, 0.55, 0.13)
FENCE_DARK  = (0.38, 0.23, 0.10)
FENCE_LIGHT = (0.56, 0.38, 0.18)
BOSS_COL    = (0.62, 0.14, 0.10)
BOSS_LIGHT  = (0.95, 0.45, 0.18)

# ── Bản đồ 30x22 ─────────────────────────────────────────────────────────
_RAW_MAP = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "XXXXXXXXX           XXXXXXXXXX",
    "XXXXXXXXX     PB    XXXXXXXXXX",
    "XXXXXXXXX    PPPP   XXXXXXXXXX",
    "XXXXXXXXX    |PP|   XXXXXXXXXX",
    "XXXXXXXXX    |PP|   XXXXXXXXXX",
    "XXXXXXXXX    |PP|----XXXXXXXXXX",
    "XXXXXXXXX    |PPPPPPP222XXXXXXX",
    "XXXXXXXXX    |PPPPPPP222XXXXXXX",
    "XXXXXXXXX    |PPPPPPP222XXXXXXX",
    "XXXXXXXXX    |PP|----XXXXXXXXXX",
    "XXXXXXXXX    |PP|   XXXXXXXXXX",
    "---XXXXXX    |PP|   XXXXXXXXXX",
    "111PPPPPPPPPPPPP|   XXXXXXXXXX",
    "111PPPPPPPPPPPPP|   XXXXXXXXXX",
    "111PPPPPPPPPPPPP|   XXXXXXXXXX",
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
            elif ch == 'P':
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
MAP_ROWS = len(TILEMAP)


def tile_at(col, row):
    if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
        return TILEMAP[row][col]
    return T_TREE


class OverworldPlayer:
    def __init__(self, col=14, row=18):
        self.px = col * TILE + TILE // 2
        self.py = (MAP_ROWS - 1 - row) * TILE + TILE // 2
        self.w  = TILE - 8
        self.h  = TILE - 8
        self.anim_timer = 0
        self.frame_index = 0
        self.moving = False
        self.facing = "down"

    def col(self): return int(self.px // TILE)
    def row(self): return MAP_ROWS - 1 - int(self.py // TILE)

    def update(self, keys):
        dx = dy = 0
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            dx = -PLAYER_SPEED
            self.facing = "left"
        elif keys[pg.K_d] or keys[pg.K_RIGHT]:
            dx = PLAYER_SPEED
            self.facing = "right"

        if keys[pg.K_w] or keys[pg.K_UP]:
            dy = PLAYER_SPEED
            self.facing = "up"
        elif keys[pg.K_s] or keys[pg.K_DOWN]:
            dy = -PLAYER_SPEED
            self.facing = "down"

        if dx != 0 and dy != 0:
            dx = int(dx * 0.7071)
            dy = int(dy * 0.7071)

        self.moving = (dx != 0 or dy != 0)

        new_x = self.px + dx
        if not self._blocked_at(new_x, self.py):
            self.px = new_x
        new_y = self.py + dy
        if not self._blocked_at(self.px, new_y):
            self.py = new_y

        margin = self.w // 2
        self.px = max(margin, min(MAP_COLS * TILE - margin, self.px))
        self.py = max(margin, min(MAP_ROWS * TILE - margin, self.py))

        self.anim_timer += 1
        if self.moving:
            if self.anim_timer % 6 == 0:
                self.frame_index = (self.frame_index + 1) % 4
        else:
            self.frame_index = 0

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


# ── Primitive OpenGL helpers ──────────────────────────────────────────────
def _draw_quad(x, y, w, h, color):
    glDisable(GL_TEXTURE_2D)
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    glColor3f(1, 1, 1)




def _draw_gradient_quad(x, y, w, h, top_color, bottom_color):
    """Vẽ quad gradient dọc bằng OpenGL, dùng cho path liền khối."""
    glDisable(GL_TEXTURE_2D)
    glBegin(GL_QUADS)
    glColor3f(*bottom_color)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glColor3f(*top_color)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    glColor3f(1, 1, 1)

def _draw_circle(cx, cy, r, color, segments=16):
    glDisable(GL_TEXTURE_2D)
    glColor3f(*color)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)
    glEnd()
    glColor3f(1, 1, 1)


def _draw_tile_quad(x, y, w, h_or_color, color=None):
    if color is None:
        h = w
        color = h_or_color
    else:
        h = h_or_color
    _draw_quad(x, y, w, h, color)


# ── Tile drawing ──────────────────────────────────────────────────────────
def _draw_grass_tile(x, y, col, row):
    # Nhẹ hơn shadow: chỉ đổi màu ô nền theo pattern nhỏ.
    if (col + row) % 7 == 0:
        c = GRASS_ALT_1
    elif (col * 3 + row) % 11 == 0:
        c = GRASS_ALT_2
    else:
        c = GRASS_BASE
    _draw_quad(x, y, TILE, TILE, c)

    # Chi tiết cỏ rất nhẹ: vài vạch ngắn, không alpha, không shadow.
    glDisable(GL_TEXTURE_2D)
    glColor3f(0.16, 0.42, 0.14)
    glBegin(GL_LINES)
    if (col + row) % 3 == 0:
        glVertex2f(x + TILE * 0.25, y + TILE * 0.30)
        glVertex2f(x + TILE * 0.25, y + TILE * 0.42)
    if (col * 2 + row) % 4 == 0:
        glVertex2f(x + TILE * 0.70, y + TILE * 0.60)
        glVertex2f(x + TILE * 0.74, y + TILE * 0.72)
    glEnd()
    glColor3f(1, 1, 1)


def _is_path_like(t):
    return t in (T_PATH, T_BOSS)


def _draw_path_connected(col, row, x, y):
    top_col = (0.72, 0.60, 0.39)
    bot_col = (0.72, 0.60, 0.39)
    _draw_gradient_quad(x, y, TILE, TILE, top_col, bot_col)

    neighbors = {
        "L": tile_at(col - 1, row),
        "R": tile_at(col + 1, row),
        "U": tile_at(col, row - 1),
        "D": tile_at(col, row + 1),
    }

    # Làm các khớp nối overlap nhẹ để không bị hở pixel giữa tile.
    overlap = 1
    if _is_path_like(neighbors["L"]):
        _draw_gradient_quad(x - overlap, y, TILE * 0.5 + overlap, TILE, top_col, bot_col)
    if _is_path_like(neighbors["R"]):
        _draw_gradient_quad(x + TILE * 0.5, y, TILE * 0.5 + overlap, TILE, top_col, bot_col)
    if _is_path_like(neighbors["U"]):
        _draw_gradient_quad(x, y + TILE * 0.5, TILE, TILE * 0.5 + overlap, top_col, bot_col)
    if _is_path_like(neighbors["D"]):
        _draw_gradient_quad(x, y - overlap, TILE, TILE * 0.5 + overlap, top_col, bot_col)

    # Viền ngoài path: không vẽ ở cạnh nối với path khác.
    glDisable(GL_TEXTURE_2D)
    glLineWidth(2)
    glColor3f(*PATH_EDGE)
    glBegin(GL_LINES)
    if not _is_path_like(neighbors["L"]):
        glVertex2f(x, y)
        glVertex2f(x, y + TILE)
    if not _is_path_like(neighbors["R"]):
        glVertex2f(x + TILE, y)
        glVertex2f(x + TILE, y + TILE)
    if not _is_path_like(neighbors["U"]):
        glVertex2f(x, y + TILE)
        glVertex2f(x + TILE, y + TILE)
    if not _is_path_like(neighbors["D"]):
        glVertex2f(x, y)
        glVertex2f(x + TILE, y)
    glEnd()

    # Sỏi nhỏ: cố định theo col/row, không random để không nhấp nháy.
    pebble_color_1 = (0.50, 0.48, 0.43)
    pebble_color_2 = (0.39, 0.37, 0.33)
    pebble_color_3 = (0.66, 0.61, 0.52)

    glPointSize(3)
    glBegin(GL_POINTS)
    if (col * 7 + row * 3) % 4 == 0:
        glColor3f(*pebble_color_1)
        glVertex2f(x + TILE * 0.25, y + TILE * 0.35)
    if (col * 5 + row * 11) % 5 == 0:
        glColor3f(*pebble_color_2)
        glVertex2f(x + TILE * 0.65, y + TILE * 0.62)
    if (col * 13 + row * 2) % 6 == 0:
        glColor3f(*pebble_color_3)
        glVertex2f(x + TILE * 0.48, y + TILE * 0.22)
    glEnd()

    # Một vài viên sỏi lớn hơn bằng circle nhỏ, rất ít để không lag.
    if (col * 17 + row) % 13 == 0:
        _draw_circle(x + TILE * 0.72, y + TILE * 0.30, 2.4, pebble_color_1, segments=8)
    if (col * 3 + row * 19) % 17 == 0:
        _draw_circle(x + TILE * 0.35, y + TILE * 0.70, 2.0, pebble_color_2, segments=8)

    glColor3f(1, 1, 1)

def _draw_boss_tile(x, y):
    _draw_quad(x + TILE * 0.08, y + TILE * 0.08, TILE * 0.84, TILE * 0.84, BOSS_COL)
    _draw_circle(x + TILE * 0.5, y + TILE * 0.5, TILE * 0.22, BOSS_LIGHT, segments=18)


def _draw_tree(x, y, tile):
    # Không shadow: thân + tán 3 cụm tròn nhẹ.
    _draw_quad(x + tile * 0.39, y + tile * 0.05, tile * 0.22, tile * 0.42, TREE_TRUNK)
    _draw_circle(x + tile * 0.50, y + tile * 0.60, tile * 0.38, TREE_CROWN1, segments=18)
    _draw_circle(x + tile * 0.34, y + tile * 0.52, tile * 0.28, TREE_CROWN2, segments=16)
    _draw_circle(x + tile * 0.66, y + tile * 0.52, tile * 0.28, TREE_CROWN2, segments=16)
    _draw_circle(x + tile * 0.50, y + tile * 0.76, tile * 0.25, TREE_CROWN3, segments=16)


def _draw_fence(x, y, size, is_horizontal=True):
    glDisable(GL_TEXTURE_2D)
    if is_horizontal:
        _draw_quad(x + size * 0.18, y + size * 0.12, size * 0.11, size * 0.76, FENCE_DARK)
        _draw_quad(x + size * 0.70, y + size * 0.12, size * 0.11, size * 0.76, FENCE_DARK)
        _draw_quad(x, y + size * 0.32, size, size * 0.12, FENCE_LIGHT)
        _draw_quad(x, y + size * 0.62, size, size * 0.12, FENCE_LIGHT)
    else:
        _draw_quad(x + size * 0.12, y + size * 0.18, size * 0.76, size * 0.11, FENCE_DARK)
        _draw_quad(x + size * 0.12, y + size * 0.70, size * 0.76, size * 0.11, FENCE_DARK)
        _draw_quad(x + size * 0.32, y, size * 0.12, size, FENCE_LIGHT)
        _draw_quad(x + size * 0.62, y, size * 0.12, size, FENCE_LIGHT)
    glColor3f(1, 1, 1)


def _draw_bush_detail(x, y, bush_type):
    # Bụi cỏ tròn tròn: nhiều cụm circle chồng nhau, không shadow.
    if bush_type == T_BUSH:
        dark = (0.16, 0.53, 0.10)
        mid = (0.24, 0.68, 0.14)
        light = (0.36, 0.80, 0.20)
    else:
        dark = (0.30, 0.55, 0.08)
        mid = (0.45, 0.70, 0.12)
        light = (0.62, 0.84, 0.18)

    _draw_circle(x + TILE * 0.30, y + TILE * 0.40, TILE * 0.24, dark, segments=14)
    _draw_circle(x + TILE * 0.52, y + TILE * 0.47, TILE * 0.30, mid, segments=16)
    _draw_circle(x + TILE * 0.72, y + TILE * 0.38, TILE * 0.23, dark, segments=14)
    _draw_circle(x + TILE * 0.45, y + TILE * 0.62, TILE * 0.22, light, segments=14)
    _draw_circle(x + TILE * 0.63, y + TILE * 0.60, TILE * 0.18, light, segments=12)

    # Viền đáy nhỏ để nhìn như bụi cụm, không dùng alpha.
    glDisable(GL_TEXTURE_2D)
    glColor3f(*dark)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(x + TILE * 0.18, y + TILE * 0.25)
    glVertex2f(x + TILE * 0.82, y + TILE * 0.25)
    glEnd()
    glColor3f(1, 1, 1)


# ── Main draw ─────────────────────────────────────────────────────────────
def draw_overworld(player, text_ren, cam_x=0, cam_y=0, renderers=None):
    glClearColor(0.10, 0.25, 0.08, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    view_x = player.px - SCREEN_WIDTH // 2
    view_y = player.py - SCREEN_HEIGHT // 2
    view_x = max(0, min(MAP_COLS * TILE - SCREEN_WIDTH, view_x))
    view_y = max(0, min(MAP_ROWS * TILE - SCREEN_HEIGHT, view_y))

    glPushMatrix()
    glTranslatef(-view_x, -view_y, 0)

    # Pass 1: grass base
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            x = col * TILE
            y = (MAP_ROWS - 1 - row) * TILE
            _draw_grass_tile(x, y, col, row)

    trees = []
    fences = []
    bushes = []

    # Pass 2: connected path/boss and collect objects
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            t = TILEMAP[row][col]
            x = col * TILE
            y = (MAP_ROWS - 1 - row) * TILE

            if t == T_PATH:
                _draw_path_connected(col, row, x, y)
            elif t == T_BOSS:
                _draw_path_connected(col, row, x, y)
                _draw_boss_tile(x, y)
            elif t == T_TREE:
                trees.append((x, y))
            elif t in (T_FENCE_H, T_FENCE_V):
                fences.append((x, y, t))
            elif t in (T_BUSH, T_BUSH2):
                bushes.append((x, y, t))

    # Pass 3: objects
    for x, y, t in fences:
        _draw_fence(x, y, TILE, is_horizontal=(t == T_FENCE_H))

    for x, y, t in bushes:
        _draw_bush_detail(x, y, t)

    for x, y in trees:
        _draw_tree(x, y, TILE)

    # Player
    px = player.px - player.w // 2
    py = player.py - player.h // 2
    rabbit_front = renderers.get("rabbit_front") if renderers else None
    rabbit_back = renderers.get("rabbit_back") if renderers else None

    ren = rabbit_front if player.facing == "down" else rabbit_back
    flip = player.facing == "left"

    if ren:
        ren.draw(int(px) - 8, int(py) - 8, player.w + 16, player.h + 16, player.frame_index, flip_x=flip)
    else:
        _draw_quad(px, py, player.w, player.h, (0.9, 0.85, 0.8))
        _draw_quad(px + player.w * 0.15, py + player.h, player.w * 0.2, player.h * 0.45, (0.9, 0.80, 0.80))
        _draw_quad(px + player.w * 0.60, py + player.h, player.w * 0.2, player.h * 0.45, (0.9, 0.80, 0.80))

    glPopMatrix()

    text_ren.draw_text(
        "WASD: Move  |  Walk into bushes to encounter monsters",
        SCREEN_WIDTH // 2,
        15,
        size=18,
        color=(15, 15, 20),
        center_x=True
    )
