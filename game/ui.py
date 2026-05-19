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
def draw_ally_status(ally, text_renderer, panel_x=20, panel_y=20):
    """
    Vẽ panel trạng thái của đồng minh ở góc dưới trái.
    HP bar trên, Energy bar dưới (ngắn hơn).
    """
    pw, ph = 340, 95
    draw_panel(panel_x, panel_y, pw, ph, 210)

    # Tên + cấp
    from game.combat_entities import Rabbit
    name = "Rabbit" if isinstance(ally, Rabbit) else ally.KIND.capitalize()
    lv_str = f"{name}  Lv.{ally.level}"
    text_renderer.draw_text(lv_str, panel_x + 8, panel_y + ph - 22, size=17, color=COL_YELLOW)

    # HP bar
    bar_x = panel_x + 8
    bar_y = panel_y + ph - 42
    bar_w = pw - 100
    bar_h = 14
    draw_hp_bar(bar_x, bar_y, bar_w, bar_h,
                ally.hp, ally.max_hp,
                COL_HP_BAR, COL_HP_BG)
    hp_txt = f"HP {ally.hp}/{ally.max_hp}"
    text_renderer.draw_text(hp_txt, bar_x + bar_w + 6, bar_y, size=13, color=COL_HP_BAR)

    # Status icons
    status_y = bar_y - 20
    if getattr(ally, 'poisoned', False):
        text_renderer.draw_text("☠ POISON", bar_x, status_y, size=13, color=COL_PURPLE)
    if getattr(ally, 'smoke_miss_bonus', False):
        text_renderer.draw_text("💨 SMOKE", bar_x + 90, status_y, size=13, color=COL_GRAY)

    # Energy bar (ngắn hơn: 70% chiều rộng HP bar)
    exp = getattr(ally, 'exp', 0)
    exp_to_next = getattr(ally, 'exp_to_next', 100)
    en_bar_w = int(bar_w * 0.70)
    en_bar_y = bar_y - 38
    en_bar_h = 10
    draw_hp_bar(bar_x, en_bar_y, en_bar_w, en_bar_h,
                exp, exp_to_next,
                COL_EN_BAR, COL_EN_BG)
    en_txt = f"EXP {exp}/{exp_to_next}"
    text_renderer.draw_text(en_txt, bar_x + en_bar_w + 6, en_bar_y, size=13, color=COL_BAR_TEXT_TINT if 'COL_BAR_TEXT_TINT' in globals() else COL_EN_BAR)


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
COMMANDS = ["Attack", "Ranged Attack", "Guard", "Item", "Run"]
CMD_W, CMD_H = 180, 38
CMD_GAP = 6

def draw_command_box(selected_cmd, actor_name, text_renderer,
                     ranged_uses=0, enabled=True, commands=None):
    """
    Vẽ hộp lệnh dọc 1 cột ở dưới phải.
    selected_cmd: index 0 đến len(commands)-1
    actor_name: tên nhân vật đang hành động (hiển thị phía trên box)
    """
    if commands is None:
        commands = ["Attack", "Ranged Attack", "Guard", "Item", "Run"]
        
    cols = 1
    rows = len(commands)
    total_w = CMD_W + 20
    total_h = rows * CMD_H + (rows - 1) * CMD_GAP + 50
    box_x = SCREEN_WIDTH - total_w - 20
    box_y = 20

    draw_panel(box_x, box_y, total_w, total_h, 220)

    # Tên nhân vật hành động
    name_y = box_y + total_h - 22
    text_renderer.draw_text(f"► {actor_name}", box_x + 10, name_y, size=17, color=COL_YELLOW)

    if not enabled:
        return box_x, box_y, total_w, total_h

    for i, label in enumerate(commands):
        cx = box_x + 10
        # Đảo chiều Y để vẽ Attack ở trên cùng, Run ở dưới cùng
        cy = box_y + 10 + (rows - 1 - i) * (CMD_H + CMD_GAP)

        is_sel = (i == selected_cmd)
        bg = (60, 100, 180) if is_sel else (30, 40, 60)
        border = COL_YELLOW if is_sel else (80, 100, 140)

        draw_rect_gl(cx, cy, CMD_W, CMD_H, bg, 220)
        draw_rect_outline(cx, cy, CMD_W, CMD_H, border, 2 if is_sel else 1)

        # Disabled style cho Ranged khi hết lượt
        col_txt = COL_WHITE
        if label.startswith("Ranged Attack") and ranged_uses <= 0:
            col_txt = COL_GRAY
        text_renderer.draw_text(label, cx + CMD_W // 2, cy + CMD_H // 2 - 8,
                                size=16, color=col_txt, center_x=True)

    return box_x, box_y, total_w, total_h


# ─────────────────────────────────────────────────────────────────────────────
#  ITEM SUBMENU (Hiển thị hòm đồ Pokemon Red Style trong trận)
# ─────────────────────────────────────────────────────────────────────────────
def draw_item_submenu(selected_idx, item_options, text_renderer, net_qty=100, carrot_qty=100, revive_qty=100, is_target_select=False):
    """
    Vẽ menu chọn vật phẩm nhỏ đè/nằm cạnh Command Box phong cách Pokemon Red.
    """
    sub_w = 230
    sub_h = 130
    sub_x = SCREEN_WIDTH - sub_w - 230
    sub_y = 20
    
    # Vẽ hộp bảng điều khiển Pokemon Red
    draw_pokemon_panel(sub_x, sub_y, sub_w, sub_h)
    
    # Tiêu đề mục vật phẩm
    title = "SELECT MONSTER" if is_target_select else "ITEMS"
    text_renderer.draw_text(title, sub_x + 15, sub_y + sub_h - 25, size=17, color=(15, 15, 20))
    
    # Vẽ các tùy chọn
    for i, item in enumerate(item_options):
        item_y = sub_y + sub_h - 60 - i * 35
        
        # Con trỏ chọn ▶
        if i == selected_idx:
            text_renderer.draw_text("▶", sub_x + 15, item_y, size=16, color=(15, 15, 20))
            
        if is_target_select:
            qty_str = ""
        else:
            if item == "Net": qty_str = f"x{net_qty}"
            elif item == "Revive": qty_str = f"x{revive_qty}"
            else: qty_str = f"x{carrot_qty}"
            
        text_renderer.draw_text(item, sub_x + 35, item_y, size=16, color=(15, 15, 20))
        if qty_str:
            text_renderer.draw_text(qty_str, sub_x + 170, item_y, size=16, color=(15, 15, 20))


# ─────────────────────────────────────────────────────────────────────────────
#  POKEMON RED PARTY MENU (Màn hình quản lý đội hình)
# ─────────────────────────────────────────────────────────────────────────────
def draw_pokemon_party_menu(selected_idx, party, text_renderer, swap_idx=None, menu_mode=None):
    """
    Vẽ giao diện danh sách quái vật Pokemon Red cổ điển, hỗ trợ đổi chỗ.
    """
    from game.combat_entities import Rabbit
    
    menu_w = 640
    menu_h = 500
    menu_x = (SCREEN_WIDTH - menu_w) // 2
    menu_y = (SCREEN_HEIGHT - menu_h) // 2
    
    # Panel nền xám viền kép
    draw_pokemon_panel(menu_x, menu_y, menu_w, menu_h)
    
    # Tiêu đề
    pass
    
    # Vẽ các slot
    slot_h = 62
    slot_gap = 8
    start_y = menu_y + menu_h - 110
    
    for i in range(6):
        sy = start_y - i * (slot_h + slot_gap)
        
        is_sel = (i == selected_idx)
        is_swap = (i == swap_idx)
        
        # Màu nền slot tương ứng
        if is_sel:
            bg_col = (210, 220, 245)
        elif is_swap:
            bg_col = (245, 210, 210)
        else:
            bg_col = (235, 235, 235)
            
        draw_rect_gl(menu_x + 30, sy, menu_w - 60, slot_h, bg_col, 255)
        draw_rect_outline(menu_x + 30, sy, menu_w - 60, slot_h, (15, 15, 20), 2 if is_sel or is_swap else 1)
        
        if i < len(party):
            member = party[i]
            kind = "Rabbit" if isinstance(member, Rabbit) else member.KIND.capitalize()
            
            # Con trỏ chọn ▶
            if is_sel:
                text_renderer.draw_text("▶", menu_x + 45, sy + slot_h // 2 - 8, size=18, color=(15, 15, 20))
                
            # Tên quái vật
            text_renderer.draw_text(kind, menu_x + 75, sy + slot_h - 26, size=18, color=(15, 15, 20))
            
            # Cấp độ dạng :Lxx
            text_renderer.draw_text(f":L{member.level}", menu_x + 240, sy + slot_h - 26, size=18, color=(15, 15, 20))
            
            # Thanh HP
            bar_x = menu_x + 75
            bar_y = sy + 15
            bar_w = 200
            bar_h = 10
            # Màu thanh máu tùy lượng HP
            hp_ratio = member.hp / member.max_hp if member.max_hp > 0 else 0
            if hp_ratio > 0.5:
                bar_color = (40, 190, 40)  # Xanh lá
            elif hp_ratio > 0.2:
                bar_color = (210, 180, 40) # Vàng
            else:
                bar_color = (210, 50, 40)  # Đỏ
                
            draw_hp_bar(bar_x, bar_y, bar_w, bar_h,
                        member.hp, member.max_hp,
                        bar_color, (180, 180, 180))
            
            # HP text dạng phân số
            hp_txt = f"{member.hp}/ {member.max_hp}"
            text_renderer.draw_text(hp_txt, menu_x + 290, sy + 12, size=16, color=(15, 15, 20))
            
            # Trạng thái ra trận (3 slots đầu)
            if i < 3:
                text_renderer.draw_text("BATTLE", menu_x + 470, sy + slot_h // 2 - 8, size=14, color=(40, 130, 40))
            else:
                text_renderer.draw_text("STANDBY", menu_x + 470, sy + slot_h // 2 - 8, size=14, color=(100, 100, 100))
        else:
            text_renderer.draw_text("- EMPTY -", menu_x + 75, sy + slot_h // 2 - 8, size=16, color=(120, 120, 120))

    # Dòng hướng dẫn cuối menu
    if menu_mode == "revive":
        guide_txt = "W/S: Select fainted ally to REVIVE  |  X/Esc: Back"
    elif menu_mode == "heal":
        guide_txt = "W/S: Select injured ally to HEAL  |  X/Esc: Back"
    elif menu_mode == "release":
        guide_txt = "W/S: Select standby ally to RELEASE  |  X/Esc: Back"
    else:
        guide_txt = "W/S: Select  |  Z: Select/Swap  |  X/Esc: Back"
        if swap_idx is not None:
            guide_txt = "Move cursor and press Z to SWAP | X: Cancel"
    text_renderer.draw_text(guide_txt, menu_x + menu_w // 2, menu_y + 15, size=15, color=(15, 15, 20), center_x=True)


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
            is_last = (i == len(self.lines) - 1)
            color = COL_YELLOW if is_last else (180, 180, 180)
            text_renderer.draw_text(line, x, py + 8 + i * 26,
                                    size=18, color=color, center_x=True)


# ─────────────────────────────────────────────────────────────────────────────
#  OVERWORLD MENU
# ─────────────────────────────────────────────────────────────────────────────
def draw_pokemon_panel(x, y, w, h):
    """
    Vẽ một panel nền sáng viền kép (Double Border) giống Pokemon Red.
    """
    # 1. Vẽ nền sáng màu xám trắng
    draw_rect_gl(x, y, w, h, (242, 242, 242), alpha=255)
    
    # 2. Vẽ viền ngoài dày màu đen bóng
    draw_rect_outline(x, y, w, h, (15, 15, 20), thickness=2)
    
    # 3. Vẽ viền trong mảnh màu đen bóng, lùi vào trong 4 pixel
    offset = 4
    draw_rect_outline(x + offset, y + offset, w - offset * 2, h - offset * 2, (15, 15, 20), thickness=1)


def draw_overworld_menu(selected_idx, options, text_renderer):
    """
    Vẽ Menu Overworld ở bên phải màn hình.
    """
    menu_w = 220
    menu_h = 160
    menu_x = SCREEN_WIDTH - menu_w - 40
    menu_y = (SCREEN_HEIGHT - menu_h) // 2 + 50
    
    # Vẽ panel Pokemon
    draw_pokemon_panel(menu_x, menu_y, menu_w, menu_h)
    
    # Vẽ các Option
    start_y = menu_y + menu_h - 45
    line_gap = 40
    
    for i, opt in enumerate(options):
        opt_y = start_y - i * line_gap
        # Nếu đang được chọn, vẽ con trỏ ▶ màu đen
        if i == selected_idx:
            text_renderer.draw_text("▶", menu_x + 25, opt_y, size=22, color=(15, 15, 20))
        
        # Vẽ text nhãn
        text_renderer.draw_text(opt, menu_x + 55, opt_y, size=22, color=(15, 15, 20))

