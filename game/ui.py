# game/ui.py
# Các hàm vẽ UI cho battle và overworld
from OpenGL.GL import *
import pygame as pg
from utils.constants import *


def draw_rect_gl(x, y, w, h, color, alpha=255):
    """Vẽ hình chữ nhật màu đặc (không texture)."""
    r, g, b = color[0]/255, color[1]/255, color[2]/255
    a = alpha / 255
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(r, g, b, a)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    glColor4f(1, 1, 1, 1)
    glDisable(GL_BLEND)


def draw_rect_outline(x, y, w, h, color, thickness=2):
    """Vẽ khung viền."""
    r, g, b = color[0]/255, color[1]/255, color[2]/255
    glDisable(GL_TEXTURE_2D)
    glColor3f(r, g, b)
    glLineWidth(thickness)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    glColor3f(1, 1, 1)


def draw_hp_bar(x, y, w, h, current, maximum, bar_color, bg_color, text_renderer=None, label=""):
    """Vẽ thanh HP/Energy với label."""
    draw_rect_gl(x, y, w, h, bg_color)
    if maximum > 0:
        fill = max(0, min(1, current / maximum))
        draw_rect_gl(x, y, int(w * fill), h, bar_color)
    draw_rect_outline(x, y, w, h, COL_WHITE, 1)
    if text_renderer and label:
        text_renderer.draw_text(label, x, y + h + 2, size=14, color=COL_WHITE)


def draw_panel(x, y, w, h, alpha=200):
    """Vẽ panel nền tối bán trong suốt."""
    draw_rect_gl(x, y, w, h, (20, 20, 35), alpha)
    draw_rect_outline(x, y, w, h, (100, 150, 220), 2)


# ─────────────────────────────────────────────────────────────────────────────
#  ALLY STATUS PANEL (dưới màn hình, hiển thị HP + Energy Rabbit)
# ─────────────────────────────────────────────────────────────────────────────
def draw_ally_status(rabbit, text_renderer, panel_x=20, panel_y=20):
    """
    Vẽ panel trạng thái Rabbit ở góc dưới trái.
    HP bar trên, Energy bar dưới (ngắn hơn).
    """
    pw, ph = 340, 80
    draw_panel(panel_x, panel_y, pw, ph, 210)

    # Tên + cấp
    lv_str = f"Rabbit  Lv.{rabbit.level}"
    text_renderer.draw_text(lv_str, panel_x + 8, panel_y + ph - 22, size=17, color=COL_YELLOW)

    # HP bar
    bar_x = panel_x + 8
    bar_y = panel_y + ph - 42
    bar_w = pw - 100
    bar_h = 14
    draw_hp_bar(bar_x, bar_y, bar_w, bar_h,
                rabbit.hp, rabbit.max_hp,
                COL_HP_BAR, COL_HP_BG)
    hp_txt = f"HP {rabbit.hp}/{rabbit.max_hp}"
    text_renderer.draw_text(hp_txt, bar_x + bar_w + 6, bar_y, size=13, color=COL_HP_BAR)

    # Status icons
    if rabbit.poisoned:
        text_renderer.draw_text("☠ POISON", bar_x, bar_y - 16, size=13, color=COL_PURPLE)
    if rabbit.smoke_miss_bonus:
        text_renderer.draw_text("💨 SMOKE", bar_x + 90, bar_y - 16, size=13, color=COL_GRAY)

    # Energy bar (ngắn hơn: 70% chiều rộng HP bar)
    en_bar_w = int(bar_w * 0.70)
    en_bar_y = bar_y - 18
    en_bar_h = 10
    draw_hp_bar(bar_x, en_bar_y, en_bar_w, en_bar_h,
                rabbit.exp, rabbit.exp_to_next,
                COL_EN_BAR, COL_EN_BG)
    en_txt = f"EXP {rabbit.exp}/{rabbit.exp_to_next}"
    text_renderer.draw_text(en_txt, bar_x + en_bar_w + 6, en_bar_y, size=13, color=COL_EN_BAR)


# ─────────────────────────────────────────────────────────────────────────────
#  ENEMY STATUS (hiển thị HP trên đầu địch)
# ─────────────────────────────────────────────────────────────────────────────
def draw_enemy_status(enemy, ex, ey, ew, eh, text_renderer, index=0):
    """Vẽ thanh HP nhỏ phía trên sprite địch."""
    bw, bh = 80, 10
    bx = ex + ew // 2 - bw // 2
    by = ey + eh + 5
    draw_hp_bar(bx, by, bw, bh,
                enemy.hp, enemy.max_hp,
                COL_FOX_HP if enemy.KIND == "fox" else COL_HP_BAR,
                COL_HP_BG)
    lbl = f"Lv.{enemy.level} {enemy.KIND.capitalize()}"
    text_renderer.draw_text(lbl, bx, by + bh + 2, size=13, color=COL_WHITE)


# ─────────────────────────────────────────────────────────────────────────────
#  COMMAND BOX (dưới phải)
# ─────────────────────────────────────────────────────────────────────────────
COMMANDS = ["Attack", "Ranged", "Guard", "Run"]
CMD_W, CMD_H = 140, 38
CMD_GAP = 6

def draw_command_box(selected_cmd, actor_name, text_renderer,
                     ranged_uses=0, enabled=True):
    """
    Vẽ hộp lệnh 4 nút ở dưới phải.
    selected_cmd: index 0-3
    actor_name: tên nhân vật đang hành động (hiển thị phía trên box)
    """
    cols = 2
    rows = 2
    total_w = cols * CMD_W + (cols - 1) * CMD_GAP + 20
    total_h = rows * CMD_H + (rows - 1) * CMD_GAP + 50
    box_x = SCREEN_WIDTH - total_w - 20
    box_y = 20

    draw_panel(box_x, box_y, total_w, total_h, 220)

    # Tên nhân vật hành động
    name_y = box_y + total_h - 22
    text_renderer.draw_text(f"► {actor_name}", box_x + 10, name_y, size=17, color=COL_YELLOW)

    if not enabled:
        return box_x, box_y, total_w, total_h

    labels = [
        "Attack",
        f"Ranged ({ranged_uses})",
        "Guard",
        "Run"
    ]
    for i, label in enumerate(labels):
        col = i % cols
        row = 1 - (i // cols)  # Đảo chiều Y vẽ để Attack/Ranged lên trên, Guard/Run xuống dưới
        cx = box_x + 10 + col * (CMD_W + CMD_GAP)
        cy = box_y + 10 + row * (CMD_H + CMD_GAP)

        is_sel = (i == selected_cmd)
        bg = (60, 100, 180) if is_sel else (30, 40, 60)
        border = COL_YELLOW if is_sel else (80, 100, 140)

        draw_rect_gl(cx, cy, CMD_W, CMD_H, bg, 220)
        draw_rect_outline(cx, cy, CMD_W, CMD_H, border, 2 if is_sel else 1)

        # Disabled style cho Ranged khi hết lượt
        col_txt = COL_WHITE
        if i == 1 and ranged_uses <= 0:
            col_txt = COL_GRAY
        text_renderer.draw_text(label, cx + CMD_W // 2, cy + CMD_H // 2 - 8,
                                size=16, color=col_txt, center_x=True)

    return box_x, box_y, total_w, total_h


# ─────────────────────────────────────────────────────────────────────────────
#  FLOATING TEXT (Miss, Crit, số damage)
# ─────────────────────────────────────────────────────────────────────────────
class FloatingText:
    def __init__(self, text, x, y, color=COL_WHITE, size=24, life=80):
        self.text  = text
        self.x     = x
        self.y     = y
        self.color = color
        self.size  = size
        self.life  = life
        self.max_life = life
        self.vy    = 1.2  # Bay lên

    def update(self):
        self.y  += self.vy
        self.life -= 1

    def draw(self, text_renderer):
        if self.life <= 0:
            return
        alpha_ratio = self.life / self.max_life
        # Fade out: giảm brightness (đơn giản = vẽ với màu gốc, không cần alpha text)
        text_renderer.draw_text(self.text, int(self.x), int(self.y),
                                size=self.size, color=self.color, center_x=True)

    def is_dead(self):
        return self.life <= 0


# ─────────────────────────────────────────────────────────────────────────────
#  MESSAGE LOG (giữa màn hình)
# ─────────────────────────────────────────────────────────────────────────────
class MessageLog:
    def __init__(self, max_lines=4):
        self.lines    = []
        self.max_lines = max_lines
        self.timer    = 0
        self.display_duration = 120  # frames

    def push(self, msg):
        self.lines.append(msg)
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)
        self.timer = self.display_duration

    def update(self):
        if self.timer > 0:
            self.timer -= 1

    def draw(self, text_renderer, x=SCREEN_WIDTH // 2, y=180):
        if self.timer <= 0:
            return
        panel_w = 560
        panel_h = len(self.lines) * 26 + 16
        px = x - panel_w // 2
        py = y - panel_h
        draw_panel(px, py, panel_w, panel_h, 200)
        for i, line in enumerate(self.lines):
            text_renderer.draw_text(line, x, py + 8 + i * 26,
                                    size=18, color=COL_WHITE, center_x=True)
