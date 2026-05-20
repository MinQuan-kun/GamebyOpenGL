# game/battle.py
import random
import math
import pygame as pg
from OpenGL.GL import *
from game.combat_entities import (
    Rabbit, Slime, Bee, Fox,
    calc_attack_damage, CRIT_CHANCE, CRIT_CHANCE_RANGED,
    MISS_CHANCE, MISS_CHANCE_RANGED
)
from game.ui import (
    draw_rect_gl, draw_rect_outline, draw_panel,
    draw_ally_status, draw_enemy_status, draw_ally_sprite_status, draw_target_aura, draw_command_box,
    FloatingText, MessageLog, COL_WHITE, COL_YELLOW,
    COL_RED, COL_GREEN, COL_ORANGE, COL_PURPLE, COL_GRAY
)
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, RANGED_USES_MAX

# ── Trạng thái battle ──────────────────────────────────────────────────────
BS_PLAYER_SELECT  = "player_select"   # Chờ người chơi chọn lệnh
BS_TARGET_SELECT  = "target_select"   # Chờ chọn mục tiêu quái vật
BS_PLAYER_ANIM    = "player_anim"     # Đang chạy animation phe ta
BS_ENEMY_TURN     = "enemy_turn"      # Lượt địch
BS_ENEMY_ANIM     = "enemy_anim"      # Animation địch
BS_WIN            = "win"
BS_LOSE           = "lose"
BS_RUN_FAIL       = "run_fail"
BS_LEVEL_UP       = "level_up"


# Màu sắc nền battle
BG_COLORS = {
    "grass": [(0.18, 0.45, 0.18), (0.08, 0.22, 0.08)],
    "boss":  [(0.25, 0.08, 0.08), (0.10, 0.03, 0.03)],
}


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


def _draw_circle(cx, cy, r, color, segments=32):
    glDisable(GL_TEXTURE_2D)
    glColor3f(*color)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)
    glEnd()
    glColor3f(1, 1, 1)


def _draw_platform(cx, cy, rx, ry, color):
    glDisable(GL_TEXTURE_2D)
    glColor3f(*color)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(49):
        a = 2 * math.pi * i / 48
        glVertex2f(cx + math.cos(a) * rx, cy + math.sin(a) * ry)
    glEnd()
    glColor3f(1, 1, 1)


def _draw_rect(x, y, w, h, color):
    glDisable(GL_TEXTURE_2D)
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    glColor3f(1, 1, 1)


def _draw_circle(cx, cy, r, color, segments=24):
    glDisable(GL_TEXTURE_2D)
    glColor3f(*color)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)

    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)

    glEnd()
    glColor3f(1, 1, 1)


def _draw_tree_cluster(x, y, scale=1.0, dark=False):
    trunk = (0.20, 0.11, 0.04) if not dark else (0.05, 0.02, 0.02)
    leaf1 = (0.10, 0.36, 0.10) if not dark else (0.07, 0.02, 0.02)
    leaf2 = (0.14, 0.48, 0.13) if not dark else (0.11, 0.03, 0.03)

    _draw_rect(x + 16 * scale, y, 12 * scale, 55 * scale, trunk)
    _draw_circle(x + 20 * scale, y + 58 * scale, 34 * scale, leaf1)
    _draw_circle(x - 2 * scale, y + 48 * scale, 24 * scale, leaf2)
    _draw_circle(x + 42 * scale, y + 46 * scale, 26 * scale, leaf2)


def _draw_round_bush(x, y, scale=1.0, variant=0):
    if variant == 0:
        c1, c2, c3 = (0.12, 0.45, 0.12), (0.18, 0.58, 0.15), (0.22, 0.66, 0.18)
    else:
        c1, c2, c3 = (0.30, 0.48, 0.10), (0.42, 0.62, 0.12), (0.52, 0.72, 0.16)

    _draw_circle(x, y, 24 * scale, c1)
    _draw_circle(x + 20 * scale, y + 3 * scale, 22 * scale, c2)
    _draw_circle(x - 18 * scale, y + 1 * scale, 20 * scale, c2)
    _draw_circle(x + 2 * scale, y + 16 * scale, 21 * scale, c3)


def _draw_flower_patch(x, y, color=(0.95, 0.78, 0.25)):
    _draw_circle(x, y, 3, color, 10)
    _draw_circle(x + 8, y + 5, 3, color, 10)
    _draw_circle(x - 7, y + 6, 2.5, color, 10)


def _draw_grass_strokes(base_y, color):
    glDisable(GL_TEXTURE_2D)
    glColor3f(*color)
    glLineWidth(2)
    glBegin(GL_LINES)

    for x in range(20, SCREEN_WIDTH, 38):
        h = 10 + (x % 5) * 3
        glVertex2f(x, base_y)
        glVertex2f(x + 5, base_y + h)

    glEnd()
    glColor3f(1, 1, 1)


def draw_battle_bg(bg_type="bush1"):
    MID_Y = SCREEN_HEIGHT // 2

    # Trời chỉ xuất hiện phía sau cây/bụi
    SKY_START_Y = MID_Y + 120

    glDisable(GL_TEXTURE_2D)

    # ───────────────── BASE BACKGROUND ─────────────────
    if bg_type == "boss":
        top = (0.25, 0.08, 0.08)
        bottom = (0.10, 0.03, 0.03)

    elif bg_type == "bush2":
        top = (0.40, 0.62, 0.22)
        bottom = (0.18, 0.36, 0.13)

    else:
        top = (0.25, 0.58, 0.24)
        bottom = (0.12, 0.34, 0.12)

    glBegin(GL_QUADS)

    glColor3f(*bottom)
    glVertex2f(0, 0)

    glColor3f(*bottom)
    glVertex2f(SCREEN_WIDTH, 0)

    glColor3f(*top)
    glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)

    glColor3f(*top)
    glVertex2f(0, SCREEN_HEIGHT)

    glEnd()

    # ───────────────── SKY (ONLY NON-BOSS) ─────────────────
    if bg_type != "boss":

        sky_top = (0.50, 0.82, 1.00)
        sky_bottom = (0.30, 0.68, 0.92)

        glBegin(GL_QUADS)

        glColor3f(*sky_bottom)
        glVertex2f(0, SKY_START_Y)

        glColor3f(*sky_bottom)
        glVertex2f(SCREEN_WIDTH, SKY_START_Y)

        glColor3f(*sky_top)
        glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)

        glColor3f(*sky_top)
        glVertex2f(0, SCREEN_HEIGHT)

        glEnd()

        # Clouds
        for cx, cy, scale in [
            (180, SKY_START_Y + 120, 1.0),
            (500, SKY_START_Y + 160, 1.25),
            (850, SKY_START_Y + 115, 0.9),
            (1130, SKY_START_Y + 150, 1.1),
        ]:

            cloud_col = (0.95, 0.98, 1.0)

            _draw_circle(cx, cy, 28 * scale, cloud_col)
            _draw_circle(cx + 30 * scale, cy + 8 * scale, 24 * scale, cloud_col)
            _draw_circle(cx - 32 * scale, cy + 6 * scale, 22 * scale, cloud_col)
            _draw_circle(cx + 8 * scale, cy + 18 * scale, 26 * scale, cloud_col)

    # ───────────────── BOSS ─────────────────
    if bg_type == "boss":

        _draw_rect(
            0,
            0,
            SCREEN_WIDTH,
            MID_Y - 70,
            (0.13, 0.04, 0.03)
        )

        _draw_rect(
            0,
            MID_Y - 70,
            SCREEN_WIDTH,
            8,
            (0.22, 0.06, 0.04)
        )

        # Trees
        for x in range(40, SCREEN_WIDTH, 115):
            _draw_tree_cluster(
                x,
                MID_Y + 40,
                1.25,
                dark=True
            )

        # Ember particles
        for x in range(60, SCREEN_WIDTH, 90):

            _draw_circle(
                x,
                MID_Y + 20 + (x % 4) * 9,
                3,
                (0.65, 0.16, 0.06),
                10
            )

    # ───────────────── BUSH 2 ─────────────────
    elif bg_type == "bush2":

        _draw_rect(
            0,
            0,
            SCREEN_WIDTH,
            MID_Y - 70,
            (0.22, 0.42, 0.14)
        )

        _draw_rect(
            0,
            MID_Y - 70,
            SCREEN_WIDTH,
            8,
            (0.38, 0.56, 0.18)
        )

        # Bushes
        for x in range(35, SCREEN_WIDTH, 105):

            _draw_round_bush(
                x,
                MID_Y + 80 + (x % 3) * 12,
                1.05,
                variant=1
            )

        # Flowers
        for x in range(65, SCREEN_WIDTH, 125):

            _draw_flower_patch(
                x,
                MID_Y + 45 + (x % 2) * 18,
                (0.96, 0.84, 0.24)
            )

        # Grass
        _draw_grass_strokes(
            MID_Y + 10,
            (0.55, 0.78, 0.25)
        )

    # ───────────────── BUSH 1 ─────────────────
    else:

        _draw_rect(
            0,
            0,
            SCREEN_WIDTH,
            MID_Y - 70,
            (0.16, 0.40, 0.13)
        )

        _draw_rect(
            0,
            MID_Y - 70,
            SCREEN_WIDTH,
            8,
            (0.28, 0.55, 0.20)
        )

        # Trees
        for x in range(80, SCREEN_WIDTH, 180):

            _draw_tree_cluster(
                x,
                MID_Y + 70,
                0.78,
                dark=False
            )

        # Bushes
        for x in range(35, SCREEN_WIDTH, 120):

            _draw_round_bush(
                x,
                MID_Y + 45 + (x % 4) * 8,
                0.85,
                variant=0
            )

        # Flowers
        for x in range(60, SCREEN_WIDTH, 155):

            _draw_flower_patch(
                x,
                MID_Y + 30 + (x % 3) * 10,
                (0.94, 0.86, 0.58)
            )

        # Grass
        _draw_grass_strokes(
            MID_Y + 10,
            (0.32, 0.68, 0.25)
        )

    glColor3f(1, 1, 1)
    glEnable(GL_TEXTURE_2D)


# ── Vị trí địch trên màn hình ─────────────────────────────────────────────
ENEMY_SLOTS = [
    (960, 350),   # slot 0
    (820, 290),   # slot 1
    (1000, 240),  # slot 2 (bên phải)
]

ALLY_BASE_X = 250   # bên trái
ALLY_BASE_Y = 320


class BattleSystem:
    def __init__(self, party, enemies, text_renderer, renderers, inventory, is_boss=False, bg_type="bush1"):
        self.party       = party
        self.inventory   = inventory
        self.rabbit      = next((m for m in party if isinstance(m, Rabbit)), party[0])
        self.enemies     = enemies          # list BaseEnemy
        self.text_ren    = text_renderer
        self.renderers   = renderers        # dict: kind -> SpriteRenderer
        self.is_boss     = is_boss
        self.bg_type = "boss" if is_boss else bg_type

        # Gán vị trí cho địch
        for i, e in enumerate(self.enemies):
            sx, sy = ENEMY_SLOTS[min(i, len(ENEMY_SLOTS)-1)]
            e.base_x = sx; e.draw_x = sx
            e.base_y = sy; e.draw_y = sy

        # Vị trí cho đồng minh (phe ta)
        self.battle_party = list(self.party[:3])
        ALLY_SLOTS = [
            (250, 320),   # slot 0
            (110, 260),   # slot 1
            (290, 210),   # slot 2
        ]
        for i, ally in enumerate(self.battle_party):
            sx, sy = ALLY_SLOTS[min(i, len(ALLY_SLOTS)-1)]
            ally.base_x = sx; ally.draw_x = sx
            ally.base_y = sy; ally.draw_y = sy

        self.state       = BS_PLAYER_SELECT
        self.selected_cmd = 0   
        self.selected_target = 0

        self.floats      = []   # FloatingText[]
        self.msg_log     = MessageLog()

        # Hàng đợi action (list of callable)
        self.action_queue = []
        self.anim_timer   = 0
        self.anim_data    = {}   # dữ liệu tạm cho animation hiện tại

        # Kết quả
        self.result       = None   # "win" / "lose" / "run"
        self.exp_gained   = 0
        self.leveled_up   = False
        self.caught_enemy_targets = []  # Quái đã bị bắt trong trận


        # Reset trạng thái tất cả quái vật đồng minh
        for ally in self.party:
            if isinstance(ally, Rabbit):
                ally.reset_battle_state()
            else:
                ally.is_guarding = False
                if hasattr(ally, 'smoke_miss_bonus'):
                    ally.smoke_miss_bonus = False
                if hasattr(ally, 'poisoned'):
                    ally.poisoned = False
                    ally.poison_stacks = 0
            if ally.is_alive() and hasattr(ally, "set_anim"):
                ally.set_anim("idle")

        # Fox: lên kế hoạch trước
        any_smoke = any(getattr(m, 'smoke_miss_bonus', False) for m in self.battle_party if m.is_alive())
        for e in self.enemies:
            if isinstance(e, Fox):
                e.plan_turn(rabbit_has_smoke=any_smoke)

        self.result_timer = 0
        self.ally_queue = []
        self.current_actor = self.rabbit
        self.actor_commands = ["Attack", "Ranged Attack", "Guard", "Item", "Run"]
        
        self.caught_this_battle = []
        self._replenish_battle_party()
        # Bắt đầu lượt của phe ta
        self._start_ally_turn()

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _living_enemies(self):
        return [e for e in self.enemies if e.is_alive()]

    def _add_float(self, text, x, y, color=COL_WHITE, size=26):
        self.floats.append(FloatingText(text, x, y + 60, color, size))

    def _push_msg(self, msg, is_enemy=None):
        if is_enemy is None:
            # Tự động phát hiện dựa trên trạng thái hiện tại hoặc nội dung hành động của địch
            is_enemy = self.state in (BS_ENEMY_TURN, BS_ENEMY_ANIM, "fox_act")
        self.msg_log.push(msg, is_enemy)

    def _play_anim(self, entity, state, fallback=None):
        """Chạy animation nếu entity có animation đó. Fallback dùng khi state chưa được mapping."""
        if not hasattr(entity, "set_anim") or not hasattr(entity, "animations"):
            return

        animations = getattr(entity, "animations", None)
        if not animations:
            return

        if state in animations:
            entity.set_anim(state)
        elif fallback and fallback in animations:
            entity.set_anim(fallback)

    # ── Tốc Độ Lượt Đi Phe Ta ──────────────────────────────────────────────────
    def _start_ally_turn(self):
        """Khởi tạo vòng mới, sắp xếp đồng minh sống theo thứ tự Rabbit -> Bee -> Slime."""
        def get_ally_speed_key(entity):
            if isinstance(entity, Rabbit):
                type_order = 0
            elif entity.KIND == "bee":
                type_order = 1
            elif entity.KIND == "slime":
                type_order = 2
            else:
                type_order = 9
            return (type_order, -entity.level)

        living_allies = [m for m in self.battle_party if m.is_alive()]
        self.ally_queue = sorted(living_allies, key=get_ally_speed_key)
        self.new_round_started = True
        self._next_ally_action()

    def _next_ally_action(self):
        """Chuyển sang đồng minh tiếp theo trong hàng đợi."""
        if not self.ally_queue:
            # Hết lượt phe ta -> Sang lượt địch
            self._start_enemy_turn()
            return

        self.current_actor = self.ally_queue.pop(0)
        self.current_actor.is_guarding = False  # Reset guard ở đầu lượt của nó
        self.state = BS_PLAYER_SELECT
        self.selected_cmd = 0

        if getattr(self, 'new_round_started', False):
            self.new_round_started = False

        if isinstance(self.current_actor, Rabbit):
            self.actor_commands = ["Attack", "Ranged Attack", "Guard", "Item", "Run"]
        else:
            self.actor_commands = ["Attack", "Guard", "Item", "Run"]

    # ── Input xử lý ─────────────────────────────────────────────────────────
    def handle_input(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.msg_log.scroll_down()
            elif event.button == 5:
                self.msg_log.scroll_up()

        if self.state not in (BS_PLAYER_SELECT, BS_TARGET_SELECT, "item_select", "catch_target_select", "revive_target_select", "heal_target_select"):
            return

        living = self._living_enemies()
        if not living:
            return

        if self.state == BS_PLAYER_SELECT:
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_UP, pg.K_w, pg.K_LEFT, pg.K_a):
                    self.selected_cmd = (self.selected_cmd - 1) % len(self.actor_commands)
                elif event.key in (pg.K_DOWN, pg.K_s, pg.K_RIGHT, pg.K_d):
                    self.selected_cmd = (self.selected_cmd + 1) % len(self.actor_commands)
                elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                    cmd_label = self.actor_commands[self.selected_cmd]
                    if cmd_label == "Attack":
                        self.state = BS_TARGET_SELECT
                        self.selected_target = 0
                    elif cmd_label == "Ranged Attack":
                        if isinstance(self.current_actor, Rabbit) and self.current_actor.ranged_uses <= 0:
                            self._push_msg("Out of Ranged ammo!")
                        else:
                            self.state = BS_TARGET_SELECT
                            self.selected_target = 0
                    elif cmd_label == "Guard":
                        self._queue_guard()
                    elif cmd_label == "Item":
                        # Mở hộp chọn item phụ
                        self.state = "item_select"
                        self.selected_item_idx = 0
                        self.item_options = ["Net", "Carrot"]
                    elif cmd_label == "Run":
                        self._queue_run()

        elif self.state == "item_select":
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_UP, pg.K_w, pg.K_LEFT, pg.K_a):
                    self.selected_item_idx = (self.selected_item_idx - 1) % len(self.item_options)
                elif event.key in (pg.K_DOWN, pg.K_s, pg.K_RIGHT, pg.K_d):
                    self.selected_item_idx = (self.selected_item_idx + 1) % len(self.item_options)
                elif event.key in (pg.K_ESCAPE, pg.K_x, pg.K_BACKSPACE):
                    self.state = BS_PLAYER_SELECT
                elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                    selected_item = self.item_options[self.selected_item_idx]
                    if selected_item == "Net":
                        if self.inventory.get("Net", 0) <= 0:
                            self._push_msg("No Nets left!")
                        elif len(self.party) >= 6:
                            self._push_msg("Party is full! Cannot catch more.")
                            self._add_float("Full Party!", self.current_actor.draw_x, self.current_actor.draw_y, COL_ORANGE)
                        else:
                            self.state = "catch_target_select"
                            self.selected_target = 0
                    elif selected_item == "Carrot":
                        if self.inventory.get("Carrot", 0) <= 0:
                            self._push_msg("No Carrots left!")
                        else:
                            actor = self.current_actor
                            if actor.hp >= actor.max_hp:
                                actor_name = "Rabbit" if isinstance(actor, Rabbit) else actor.KIND.capitalize()
                                self._push_msg(f"{actor_name} is already at full HP!")
                            else:
                                self._queue_heal(actor)
                                if "Carrot" in self.inventory:
                                    self.inventory["Carrot"] = max(0, self.inventory["Carrot"] - 1)

        elif self.state == "revive_target_select":
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_UP, pg.K_w, pg.K_LEFT, pg.K_a):
                    self.selected_target = (self.selected_target - 1) % len(self.revive_targets)
                elif event.key in (pg.K_DOWN, pg.K_s, pg.K_RIGHT, pg.K_d):
                    self.selected_target = (self.selected_target + 1) % len(self.revive_targets)
                elif event.key in (pg.K_ESCAPE, pg.K_x, pg.K_BACKSPACE):
                    self.state = "item_select"
                elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                    tgt = self.revive_targets[self.selected_target]
                    self._queue_revive(tgt)

        elif self.state == "heal_target_select":
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_UP, pg.K_w, pg.K_LEFT, pg.K_a):
                    self.selected_target = (self.selected_target - 1) % len(self.heal_targets)
                elif event.key in (pg.K_DOWN, pg.K_s, pg.K_RIGHT, pg.K_d):
                    self.selected_target = (self.selected_target + 1) % len(self.heal_targets)
                elif event.key in (pg.K_ESCAPE, pg.K_x, pg.K_BACKSPACE):
                    self.state = "item_select"
                elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                    tgt = self.heal_targets[self.selected_target]
                    self._queue_heal(tgt)

        elif self.state == "catch_target_select":
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_UP, pg.K_w, pg.K_LEFT, pg.K_a):
                    self.selected_target = (self.selected_target - 1) % len(living)
                elif event.key in (pg.K_DOWN, pg.K_s, pg.K_RIGHT, pg.K_d):
                    self.selected_target = (self.selected_target + 1) % len(living)
                elif event.key in (pg.K_ESCAPE, pg.K_x, pg.K_BACKSPACE):
                    self.state = "item_select"
                elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                    tgt = living[min(self.selected_target, len(living)-1)]
                    if tgt.KIND == "fox":
                        self._queue_catch(tgt)
                    else:
                        self._queue_catch(tgt)
                        if "Net" in self.inventory:
                            self.inventory["Net"] = max(0, self.inventory["Net"] - 1)

        elif self.state == BS_TARGET_SELECT:
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_UP, pg.K_w, pg.K_LEFT, pg.K_a):
                    self.selected_target = (self.selected_target - 1) % len(living)
                elif event.key in (pg.K_DOWN, pg.K_s, pg.K_RIGHT, pg.K_d):
                    self.selected_target = (self.selected_target + 1) % len(living)
                elif event.key in (pg.K_ESCAPE, pg.K_x, pg.K_BACKSPACE):
                    self.state = BS_PLAYER_SELECT
                elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                    tgt = living[min(self.selected_target, len(living)-1)]
                    cmd_label = self.actor_commands[self.selected_cmd]
                    if cmd_label == "Attack":
                        self._queue_ally_attack(tgt, ranged=False)
                    elif cmd_label == "Ranged Attack":
                        self._queue_ally_attack(tgt, ranged=True)

    # ── Queue actions ────────────────────────────────────────────────────────
    def _queue_ally_attack(self, target, ranged=False):
        self.current_actor.is_guarding = False  # Guard chỉ kéo dài 1 lượt
        self.state = BS_PLAYER_ANIM
        self.anim_timer = 0

        # Animation Attack / Ranged cho phe ta
        if ranged:
            self._play_anim(self.current_actor, "ranged", fallback="attack")
        else:
            self._play_anim(self.current_actor, "attack")

        if ranged:
            if isinstance(self.current_actor, Rabbit):
                self.current_actor.ranged_uses -= 1
            miss_c = MISS_CHANCE_RANGED + (0.25 if getattr(self.current_actor, 'smoke_miss_bonus', False) else 0)
            crit_c = CRIT_CHANCE_RANGED
        else:
            miss_c = MISS_CHANCE + (0.25 if getattr(self.current_actor, 'smoke_miss_bonus', False) else 0)
            crit_c = CRIT_CHANCE

        dmg, is_crit, is_miss = calc_attack_damage(self.current_actor.atk, miss_c, crit_c)

        # Vị trí xuất projectile từ nhân vật
        proj_offset_x = 115 if isinstance(self.current_actor, Rabbit) else 70
        proj_offset_y = 85 if isinstance(self.current_actor, Rabbit) else 55

        self.anim_data = {
            "type": "ally_atk",
            "actor": self.current_actor,
            "ranged": ranged,
            "target": target,
            "dmg": dmg,
            "is_crit": is_crit,
            "is_miss": is_miss,
            "phase": 0,      # 0=move/fly, 1=hit, 2=return
            "start_x": self.current_actor.draw_x,
            "start_y": self.current_actor.draw_y,
            "proj_x": float(self.current_actor.draw_x + proj_offset_x),
            "proj_y": float(self.current_actor.draw_y + proj_offset_y),
            "applied": False,
        }


    def _queue_catch(self, target):
        """Bắt quái thường, Cáo thất bại không mất lượt."""
        if target.KIND == "fox":
            self._push_msg("Cannot catch Boss Fox!")
            self._add_float("Failed!", target.draw_x + 40, target.draw_y, COL_GRAY)
            self.state = BS_PLAYER_SELECT
            return

        self.state = BS_PLAYER_ANIM
        self.anim_timer = 0

        # Animation dùng lưới. Nếu Rabbit chưa có mapping "net", fallback sang "ranged".
        self._play_anim(self.current_actor, "net", fallback="ranged")

        # Máu càng thấp tỷ lệ bắt càng cao. Slime > Bee
        base_rate = 0.55 if target.KIND == "slime" else 0.35
        hp_ratio = target.hp / target.max_hp if target.max_hp > 0 else 1.0
        catch_chance = base_rate * (1.5 - hp_ratio)
        success = random.random() < catch_chance

        self.anim_data = {
            "type": "catch",
            "actor": self.current_actor,
            "target": target,
            "success": success,
            "phase": 0,
            "proj_x": float(self.current_actor.draw_x + 115),
            "proj_y": float(self.current_actor.draw_y + 85),
            "applied": False,
        }


    def _queue_revive(self, target):
        self.state = BS_PLAYER_ANIM
        self.anim_timer = 0
        self.anim_data = {
            "type": "revive",
            "actor": self.current_actor,
            "target": target,
            "phase": 0,
            "applied": False,
        }

    def _queue_heal(self, target):
        self.state = BS_PLAYER_ANIM
        self.anim_timer = 0

        # Animation hồi máu khi dùng Carrot.
        self._play_anim(target, "heal", fallback="idle")
        
        # Phát SFX khi dùng cà rốt hồi máu
        try:
            if pg.mixer.get_init():
                sfx = pg.mixer.Sound("assets/sounds/heal_sfx.mp3")
                sfx.set_volume(0.8)
                sfx.play()
        except Exception as e:
            print(f"Cannot play heal SFX: {e}")

        self.anim_data = {
            "type": "heal",
            "actor": self.current_actor,
            "target": target,
            "phase": 0,
            "applied": False,
        }


    def _queue_guard(self):
        self.current_actor.is_guarding = True
        self._play_anim(self.current_actor, "guard", fallback="idle")

        actor_name = "Rabbit" if isinstance(self.current_actor, Rabbit) else self.current_actor.KIND.capitalize()
        self._push_msg(f"{actor_name} is guarding! Damage received reduced by 1/3.")
        self._add_float("Guard!", self.current_actor.draw_x, self.current_actor.draw_y, COL_GREEN)
        self._after_ally_action()


    def _queue_run(self):
        living = self._living_enemies()
        if self.is_boss:
            self._push_msg("Cannot flee from Boss!")
            self.state = BS_PLAYER_SELECT
            return
        if len(living) == 1:
            success = True
        else:
            success = (random.random() > 1/3)

        if success:
            self.result = "run"
            self.state  = BS_WIN
            self._push_msg("Escaped successfully!")
        else:
            self._push_msg("Failed to escape! Turn lost.")
            self.ally_queue = [] # xóa hàng đợi đồng minh
            self._start_enemy_turn()

    # ── Enemy Turn ───────────────────────────────────────────────────────────
    def _start_enemy_turn(self):
        self.state = BS_ENEMY_TURN
        # Sắp xếp thứ tự: Bee(5) < Slime(10) < Fox(20)
        ordered = sorted(self._living_enemies(), key=lambda e: e.SPEED_ORDER)
        self.enemy_queue = list(ordered)
        self._next_enemy_action()

    def _next_enemy_action(self):
        if not self.enemy_queue:
            self._end_turn()
            return
        enemy = self.enemy_queue.pop(0)
        if isinstance(enemy, Fox):
            act = enemy.next_action()
            if act is None:
                self._next_enemy_action()
                return
            self._do_fox_action(enemy, act)
            # Nếu Fox còn hành động nữa, đưa lại vào đầu hàng đợi
            if enemy.has_more_actions():
                self.enemy_queue.insert(0, enemy)
        else:
            self._do_enemy_attack(enemy)

    def _do_enemy_attack(self, enemy):
        self.state = BS_ENEMY_ANIM
        living_allies = [m for m in self.battle_party if m.is_alive()]
        if not living_allies:
            target = self.rabbit
        else:
            target = random.choice(living_allies)

        miss_chance = getattr(target, 'get_miss_chance', lambda: MISS_CHANCE)()
        dmg, is_crit, is_miss = calc_attack_damage(
            enemy.atk,
            miss_chance=miss_chance,
        )
        self.anim_data = {
            "type": "enemy_atk",
            "enemy": enemy,
            "target": target,
            "dmg": dmg,
            "is_crit": is_crit,
            "is_miss": is_miss,
            "phase": 0,
            "applied": False,
        }
        self.anim_timer = 0

    def _do_fox_action(self, fox, act):
        self.state = BS_ENEMY_ANIM
        self.anim_timer = 0

        atype = act["type"]
        if atype == "kunai":
            self._play_anim(fox, "kunai", fallback="idle")
            proj_type = "kunai"
        elif atype == "smoke":
            self._play_anim(fox, "smoke", fallback="idle")
            proj_type = "smoke"
        elif atype == "power_charge":
            self._play_anim(fox, "power_charge", fallback="idle")
            proj_type = None
        else:
            proj_type = None

        # Chọn mục tiêu để projectile bay tới
        living_allies = [m for m in self.battle_party if m.is_alive()]
        target = random.choice(living_allies) if living_allies else self.rabbit

        self.anim_data = {
            "type": "fox_act",
            "fox": fox,
            "act": act,
            "target": target,
            "phase": 0,
            "applied": False,
            "proj_type": proj_type,
            "proj_x": float(fox.draw_x + 80),
            "proj_y": float(fox.draw_y + 120),
            "target_x": float(target.draw_x + 65),
            "target_y": float(target.draw_y + 90),
        }


    def _end_turn(self):
        """Cuối lượt: xử lý poison, kiểm tra thua."""
        living_allies = [m for m in self.battle_party if m.is_alive()]
        for ally in living_allies:
            if getattr(ally, 'poisoned', False):
                self._play_anim(ally, "poison", fallback="idle")
                pdmg = max(1, int(ally.max_hp * 0.05 * getattr(ally, 'poison_stacks', 1)))
                ally.hp = max(0, ally.hp - pdmg)
                ally_name = "Rabbit" if isinstance(ally, Rabbit) else ally.KIND.capitalize()
                self._push_msg(f"Poison deals {pdmg} damage to {ally_name}!")
                self._add_float(f"-{pdmg} PSN", ally.draw_x, ally.draw_y, COL_PURPLE)

        # Trận đấu kết thúc khi Thỏ hết HP hoặc toàn bộ battle_party hết HP
        if self.rabbit.hp <= 0 or all(m.hp <= 0 for m in self.battle_party):
            for ally in self.battle_party:
                if ally.hp <= 0:
                    self._play_anim(ally, "dead", fallback="hit")
            self.result = "lose"
            self.state  = BS_LOSE
            self._push_msg("Rabbit has fainted! Game Over!")
            return

        self._replenish_battle_party()

        # Guard chỉ tồn tại 1 lượt địch → reset
        for ally in self.battle_party:
            if hasattr(ally, 'is_guarding'):
                ally.is_guarding = False
                if hasattr(ally, "set_anim") and ally.is_alive():
                    ally.set_anim("idle")

        # Giảm số lượt hiệu ứng bom khói của party
        for ally in self.battle_party:
            if getattr(ally, 'smoke_turns', 0) > 0:
                ally.smoke_turns -= 1
                if ally.smoke_turns <= 0:
                    ally.smoke_miss_bonus = False

        any_smoke = any(getattr(m, 'smoke_miss_bonus', False) for m in self.battle_party if m.is_alive())
        # Fox lên kế hoạch cho lượt tiếp theo
        for e in self._living_enemies():
            if isinstance(e, Fox):
                e.plan_turn(rabbit_has_smoke=any_smoke)

        # Bắt đầu ngay lượt mới phe ta
        self._start_ally_turn()

    # ── Update animation ─────────────────────────────────────────────────────
    def update(self):
        self.msg_log.update()

        # Update animation cho toàn bộ phe ta và phe địch
        for ally in self.battle_party:
            if hasattr(ally, "update_animation"):
                ally.update_animation()

        for e in self.enemies:
            if hasattr(e, "update_animation"):
                e.update_animation()

        for f in self.floats:
            f.update()
        self.floats = [f for f in self.floats if not f.is_dead()]

        if self.state == BS_PLAYER_ANIM:
            self._update_ally_anim()
        elif self.state == BS_ENEMY_ANIM:
            self._update_enemy_anim()
        elif self.state in (BS_WIN, BS_LOSE):
            self.result_timer += 1


    def _update_ally_anim(self):
        d = self.anim_data
        self.anim_timer += 1
        actor = d["actor"]

        if d["type"] == "ally_atk":
            tgt = d["target"]
            if not d["ranged"]:
                tx, ty = tgt.draw_x - 60, tgt.draw_y + 40  # Đứng bên trái quái
            else:
                tx, ty = tgt.draw_x + 30, tgt.draw_y + 40  # Đạn chạm mặt quái

            if not d["ranged"]:
                # Melee: di chuyển đến địch rồi quay về
                if d["phase"] == 0:
                    # Di chuyển đến mục tiêu
                    dx = tx - actor.draw_x
                    dy = ty - actor.draw_y
                    dist = math.hypot(dx, dy)
                    spd = 12
                    if dist < spd:
                        actor.draw_x = tx
                        actor.draw_y = ty
                        d["phase"] = 1
                        self.anim_timer = 0
                    else:
                        actor.draw_x += dx / dist * spd
                        actor.draw_y += dy / dist * spd
                elif d["phase"] == 1:
                    # Hit frame
                    if not d["applied"]:
                        d["applied"] = True
                        self._apply_ally_hit(d)
                    if self.anim_timer > 15:
                        d["phase"] = 2
                        self.anim_timer = 0
                elif d["phase"] == 2:
                    # Quay về
                    bx, by = d["start_x"], d["start_y"]
                    dx = bx - actor.draw_x
                    dy = by - actor.draw_y
                    dist = math.hypot(dx, dy)
                    spd = 12
                    if dist < spd:
                        actor.draw_x = bx
                        actor.draw_y = by
                        self._after_ally_action()
                    else:
                        actor.draw_x += dx / dist * spd
                        actor.draw_y += dy / dist * spd
            else:
                # Ranged: bắn projectile
                if d["phase"] == 0:
                    # Bay đến mục tiêu
                    px, py = d["proj_x"], d["proj_y"]
                    dx = tx - px
                    dy = ty - py
                    dist = math.hypot(dx, dy)
                    spd = 18
                    if dist < spd:
                        d["proj_x"] = tx
                        d["proj_y"] = ty
                        d["phase"] = 1
                        self.anim_timer = 0
                    else:
                        d["proj_x"] += dx / dist * spd
                        d["proj_y"] += dy / dist * spd
                elif d["phase"] == 1:
                    if not d["applied"]:
                        d["applied"] = True
                        self._apply_ally_hit(d)
                    if self.anim_timer > 20:
                        self._after_ally_action()

        elif d["type"] == "catch":
            tgt = d["target"]
            tx, ty = tgt.draw_x + 30, tgt.draw_y + 40

            if d["phase"] == 0:
                # Projectile net bay
                px, py = d["proj_x"], d["proj_y"]
                dx = tx - px
                dy = ty - py
                dist = math.hypot(dx, dy)
                spd = 18
                if dist < spd:
                    d["proj_x"] = tx
                    d["proj_y"] = ty
                    d["phase"] = 1
                    self.anim_timer = 0
                else:
                    d["proj_x"] += dx / dist * spd
                    d["proj_y"] += dy / dist * spd
            elif d["phase"] == 1:
                if not d["applied"]:
                    d["applied"] = True
                    self._apply_catch_hit(d)
                if self.anim_timer > 20:
                    self._after_ally_action()

        elif d["type"] == "revive":
            tgt = d["target"]
            if not d["applied"]:
                d["applied"] = True
                tgt.hp = max(1, tgt.max_hp // 2)
                if hasattr(tgt, "set_anim"):
                    tgt.set_anim("idle")
                tgt_name = "Rabbit" if isinstance(tgt, Rabbit) else tgt.KIND.capitalize()
                self._push_msg(f"Revived {tgt_name}!")
            
            if self.anim_timer > 32:
                self._after_ally_action()

        elif d["type"] == "heal":
            tgt = d["target"]
            if not d["applied"]:
                d["applied"] = True
                self._play_anim(tgt, "heal", fallback="idle")
                heal_amt = tgt.max_hp // 2
                tgt.hp = min(tgt.max_hp, tgt.hp + heal_amt)
                tgt_name = "Rabbit" if isinstance(tgt, Rabbit) else tgt.KIND.capitalize()
                self._push_msg(f"{tgt_name} recovered {heal_amt} HP!")
                if tgt in self.battle_party:
                    self._add_float(f"+{heal_amt}", tgt.draw_x + 40, tgt.draw_y, COL_GREEN, 28)
            
            if self.anim_timer > 20:
                self._after_ally_action()

    def _apply_ally_hit(self, d):
        # Phát SFX cho Attack hoặc Ranged Attack khi chạm mục tiêu
        try:
            if pg.mixer.get_init():
                sfx = pg.mixer.Sound("assets/sounds/atk_sfx.mp3")
                sfx.set_volume(0.7)
                sfx.play()
        except Exception as e:
            print(f"Cannot play attack SFX: {e}")

        actor = d["actor"]
        tgt = d["target"]
        if not tgt.is_alive():
            return

        actor_name = "Rabbit" if isinstance(actor, Rabbit) else actor.KIND.capitalize()

        if d["is_miss"]:
            self._push_msg(f"{actor_name} attacks... MISS!")
            self._add_float("Miss", tgt.draw_x + 40, tgt.draw_y, COL_GRAY, 28)
        else:
            actual = tgt.take_damage(d["dmg"])

            # Animation bị đánh / chết cho mục tiêu
            if hasattr(tgt, "set_anim"):
                if tgt.is_alive():
                    self._play_anim(tgt, "hit", fallback="idle")
                else:
                    self._play_anim(tgt, "dead", fallback="hit")

            prefix = "CRIT! " if d["is_crit"] else ""
            self._push_msg(f"{prefix}{actor_name} deals {actual} damage to {tgt.KIND.capitalize()}!")
            if d["is_crit"]:
                self._add_float(f"-{actual}!!!", tgt.draw_x + 40, tgt.draw_y, COL_YELLOW, 45)
            else:
                self._add_float(f"-{actual}", tgt.draw_x + 40, tgt.draw_y, COL_RED, 28)

            if not tgt.is_alive():
                self._push_msg(f"{tgt.KIND.capitalize()} has been defeated!")


    def _apply_catch_hit(self, d):
        tgt = d["target"]
        if not tgt.is_alive():
            return

        success = d["success"]
        if success:
            self._push_msg(f"Successfully caught {tgt.KIND.capitalize()}!")
            self._add_float("CAUGHT!", tgt.draw_x + 40, tgt.draw_y, COL_GREEN, 28)
            try:
                if pg.mixer.get_init():
                    sfx = pg.mixer.Sound("assets/sounds/catch_sfx.mp3")
                    sfx.set_volume(0.8)
                    sfx.play()
            except Exception as e:
                print(f"Cannot play catch SFX: {e}")
            
            prev_hp = tgt.hp
            tgt.hp = 0  # xóa khỏi trận đấu
            self.caught_enemy_targets.append(tgt)
            
            # Thêm quái vật vào party
            from game.combat_entities import Slime, Bee
            if tgt.KIND == "slime":
                new_member = Slime(tgt.level)
            else:
                new_member = Bee(tgt.level)
                
            new_member.hp = max(1, prev_hp) # Giữ nguyên HP khi bắt
            self.party.append(new_member)
            self.caught_this_battle.append(new_member)
        else:
            self._push_msg(f"Failed to catch {tgt.KIND.capitalize()}!")
            self._add_float("Failed!", tgt.draw_x + 40, tgt.draw_y, COL_GRAY, 28)

    def _after_ally_action(self):
        ALLY_SLOTS = [
            (250, 320),
            (110, 260),
            (290, 210),
        ]
        for i, ally in enumerate(self.battle_party):
            if not ally.is_alive() and getattr(ally, "anim_state", None) != "dead":
                continue
            sx, sy = ALLY_SLOTS[min(i, len(ALLY_SLOTS)-1)]
            ally.draw_x = sx
            ally.draw_y = sy

        # Kiểm tra còn địch không
        if not self._living_enemies():
            self._resolve_win()
        else:
            self._replenish_battle_party()
            # Di chuyển sang đồng minh tiếp theo
            self._next_ally_action()

    def _resolve_win(self):
        total_exp = sum(
            e.exp_reward for e in self.enemies
            if e not in self.caught_enemy_targets
        )
        self.exp_gained = total_exp
        
        # Ngừng nhạc nền và phát SFX chiến thắng đúng 1 lần
        try:
            if pg.mixer.get_init():
                pg.mixer.music.stop()
                victory_sfx = pg.mixer.Sound("assets/sounds/victory_sfx.mp3")
                victory_sfx.set_volume(0.8)
                victory_sfx.play()
        except Exception as e:
            print(f"Cannot play victory SFX: {e}")

        rabbit = next((m for m in self.party if isinstance(m, Rabbit)), self.party[0])
        self.leveled_up = rabbit.gain_exp(total_exp)
        self.result = "win"
        self.state  = BS_WIN
        
        self._push_msg("Victory!")
        if total_exp == 0 and self.caught_enemy_targets:
            self._push_msg("All monsters caught.")
            
        self._push_msg(f"Rabbit: +{total_exp} EXP")
        if self.leveled_up:
            self._push_msg(f"Rabbit leveled up to Lv.{rabbit.level}!")
        
        # Đồng minh khác nhận XP và in thông báo
        for m in self.party:
            if m is not rabbit and m not in self.caught_this_battle:
                m_name = m.KIND.capitalize()
                self._push_msg(f"{m_name}: +{total_exp} EXP")
                m_leveled = m.gain_exp(total_exp)
                if m_leveled:
                    self._push_msg(f"{m_name} leveled up to Lv.{m.level}!")

    def _update_enemy_anim(self):
        d = self.anim_data
        self.anim_timer += 1

        if d["type"] == "enemy_atk":
            enemy = d["enemy"]
            target = d["target"]
            target_name = "Rabbit" if isinstance(target, Rabbit) else target.KIND.capitalize()

            if d["phase"] == 0:
                # Rung lắc địch rồi hit
                if self.anim_timer < 20:
                    offset = math.sin(self.anim_timer * 0.8) * 8
                    enemy.draw_x = enemy.base_x + offset
                else:
                    enemy.draw_x = enemy.base_x
                    if not d["applied"]:
                        d["applied"] = True
                        if d["is_miss"]:
                            self._push_msg(f"{enemy.KIND.capitalize()} attacks... MISS!")
                            self._add_float("Miss", target.draw_x, target.draw_y, COL_GRAY)
                        else:
                            actual = target.take_damage(d["dmg"])
                            self._play_anim(target, "hit", fallback="idle")
                            try:
                                if pg.mixer.get_init():
                                    dmg_sfx = pg.mixer.Sound("assets/sounds/take_dmg_sfx.mp3")
                                    dmg_sfx.set_volume(0.8)
                                    dmg_sfx.play()
                            except Exception as e:
                                print(f"Cannot play take damage SFX: {e}")
                            if not target.is_alive():
                                self._play_anim(target, "dead", fallback="hit")
                                target.dead_wait_timer = 0
                                target.pending_remove = True

                            prefix = "CRIT! " if d["is_crit"] else ""
                            self._push_msg(f"{prefix}{enemy.KIND.capitalize()} deals {actual} damage to {target_name}!")
                            if d["is_crit"]:
                                self._add_float(f"-{actual}!!!", target.draw_x, target.draw_y, COL_YELLOW, 45)
                            else:
                                self._add_float(f"-{actual}", target.draw_x, target.draw_y, COL_RED, 28)

                    if self.anim_timer > 35:
                        enemy.draw_x = enemy.base_x
                        self._check_rabbit_alive_then_next()

        elif d["type"] == "fox_act":
            fox = d["fox"]
            act = d["act"]

            if act["type"] == "power_charge":
                if self.anim_timer > 35:
                    if not d["applied"]:
                        d["applied"] = True
                        self._apply_fox_action(fox, act)
                    if self.anim_timer > 55:
                        self._check_rabbit_alive_then_next()
                return

            # Kunai / Smoke bay đến mục tiêu
            if d.get("proj_type") in ("kunai", "smoke") and d["phase"] == 0:
                px, py = d["proj_x"], d["proj_y"]
                tx, ty = d["target_x"], d["target_y"]

                dx = tx - px
                dy = ty - py
                dist = math.hypot(dx, dy)
                spd = 10

                if dist < spd:
                    d["proj_x"] = tx
                    d["proj_y"] = ty
                    d["phase"] = 1
                    self.anim_timer = 0
                else:
                    d["proj_x"] += dx / dist * spd
                    d["proj_y"] += dy / dist * spd

            elif d["phase"] == 1:
                if not d["applied"]:
                    d["applied"] = True
                    self._apply_fox_action(fox, act)

                if self.anim_timer > 25:
                    self._check_rabbit_alive_then_next()


    def _apply_fox_action(self, fox, act):
        atype = act["type"]

        target = self.anim_data.get("target") if isinstance(self.anim_data, dict) else None
        if target is None or not target.is_alive():
            target = self.rabbit if self.rabbit.is_alive() else None
        if target is None:
            living_allies = [m for m in self.battle_party if m.is_alive()]
            target = random.choice(living_allies) if living_allies else self.rabbit

        target_name = "Rabbit" if isinstance(target, Rabbit) else target.KIND.capitalize()

        if atype == "power_charge":
            fox.powered_up_visual = True
            if hasattr(fox, "powered_up_visual"):
                fox.powered_up_visual = True
            self._play_anim(fox, "power_charge", fallback="idle")
            self._push_msg("Fox is gathering energy! (Power Charge)")
            return

        if atype == "smoke":
            self._push_msg("Fox threw a Smoke Grenade! The active party is affected.")
            for ally in self.battle_party:
                if ally.is_alive():
                    ally.smoke_miss_bonus = True
                    ally.smoke_turns = 3  # Tác dụng trong 3 lượt
                    ally.poisoned = True
                    ally.poison_stacks = getattr(ally, 'poison_stacks', 0) + 1
                    self._play_anim(ally, "poison", fallback="hit")
                    self._add_float("SMOKE!", ally.draw_x, ally.draw_y + 30, COL_GRAY, 24)
            try:
                if pg.mixer.get_init():
                    sfx = pg.mixer.Sound("assets/sounds/poison_sfx.mp3")
                    sfx.set_volume(0.8)
                    sfx.play()
            except Exception as e:
                print(f"Cannot play poison SFX: {e}")
            return

        # kunai
        guaranteed_crit = act.get("guaranteed_crit", False)
        no_miss         = act.get("no_miss", False)

        if no_miss:
            miss_c = 0.0
        else:
            miss_c = target.get_miss_chance() if hasattr(target, 'get_miss_chance') else MISS_CHANCE

        if guaranteed_crit:
            dmg = fox.atk * 2
            is_crit = True
            is_miss = False
        else:
            dmg, is_crit, is_miss = calc_attack_damage(fox.atk, miss_c)

        if is_miss:
            self._push_msg("Fox threw Kunai... MISS!")
            self._add_float("Miss", target.draw_x, target.draw_y, COL_GRAY)
        else:
            actual = target.take_damage(dmg)
            self._play_anim(target, "hit", fallback="idle")
            try:
                if pg.mixer.get_init():
                    dmg_sfx = pg.mixer.Sound("assets/sounds/take_dmg_sfx.mp3")
                    dmg_sfx.set_volume(0.8)
                    dmg_sfx.play()
            except Exception as e:
                print(f"Cannot play take damage SFX: {e}")
            if not target.is_alive():
                self._play_anim(target, "dead", fallback="hit")
                target.dead_wait_timer = 0
                target.pending_remove = True

            if act.get("guaranteed_crit", False) and hasattr(fox, "clear_power_visual"):
                fox.clear_power_visual()

            prefix = "CRIT! " if is_crit else ""
            self._push_msg(f"{prefix}Fox threw Kunai dealing {actual} damage to {target_name}!")
            if is_crit:
                self._add_float(f"-{actual}!!!", target.draw_x, target.draw_y, COL_ORANGE, 45)
            else:
                self._add_float(f"-{actual}", target.draw_x, target.draw_y, COL_ORANGE, 28)


    def _check_rabbit_alive_then_next(self):
        all_party_dead = all(m.hp <= 0 for m in self.battle_party)

        if all_party_dead:
            for ally in self.battle_party:
                self._play_anim(ally, "dead", fallback="hit")
                ally.pending_remove = False

            self.result = "lose"
            self.state = BS_LOSE
            self._push_msg("The entire party has been defeated!")
            return

        # Nếu có ally vừa chết, cho dead animation chạy rồi mới thay người
        dead_waiting = [
            m for m in self.battle_party
            if m.hp <= 0 and getattr(m, "pending_remove", False)
        ]

        if dead_waiting:
            for m in dead_waiting:
                m.dead_wait_timer = getattr(m, "dead_wait_timer", 0) + 1

            if any(m.dead_wait_timer < 45 for m in dead_waiting):
                return

            for m in dead_waiting:
                m.pending_remove = False

        self._replenish_battle_party()
        self._next_enemy_action()

    def _replenish_battle_party(self):
        living_in_battle = [
            m for m in self.battle_party
            if m.is_alive() or getattr(m, "pending_remove", False)
        ]
        if len(living_in_battle) < 3:
            new_battle_party = list(living_in_battle)
            for m in self.party:
                if m.is_alive() and m not in new_battle_party and m not in getattr(self, 'caught_this_battle', []):
                    new_battle_party.append(m)
                if len(new_battle_party) == 3:
                    break
            
            if len(new_battle_party) > len(living_in_battle):
                self.battle_party = new_battle_party
                ALLY_SLOTS = [(250, 320), (110, 260), (290, 210)]
                for i, ally in enumerate(self.battle_party):
                    sx, sy = ALLY_SLOTS[min(i, len(ALLY_SLOTS)-1)]
                    ally.base_x = sx; ally.draw_x = sx
                    ally.base_y = sy; ally.draw_y = sy
                self._push_msg("Reserve ally automatically enters battle!")

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self):
        draw_battle_bg(self.bg_type)

        # Vẽ địch
        living = self._living_enemies()
        for i, e in enumerate(self.enemies):
            if not e.is_alive() and getattr(e, "anim_state", None) != "dead":
                continue

            rend = self.renderers.get(e.KIND)
            if rend:
                frame = e.get_current_frame() if hasattr(e, "get_current_frame") else 0

                if isinstance(e, Fox):
                    ew, eh = 300, 300     # scale up Fox
                    ox, oy = -70, -50
                    flip = True           # flip Fox hoàn toàn
                else:
                    ew, eh = 90, 90
                    ox, oy = 0, 0
                    flip = False

                rend.draw(
                    int(e.draw_x + ox),
                    int(e.draw_y + oy),
                    ew,
                    eh,
                    frame,
                    flip_x=flip
                )

                draw_enemy_status(
                    e,
                    int(e.draw_x + ox),
                    int(e.draw_y + oy),
                    ew,
                    eh,
                    self.text_ren,
                    is_active=(e == self.current_actor)
                )

        # Vẽ đồng minh (phe ta)
        for i, ally in enumerate(self.battle_party):
            if (
                not ally.is_alive()
                and getattr(ally, "anim_state", None) != "dead"
                and not getattr(ally, "pending_remove", False)
            ):
                continue

            if isinstance(ally, Rabbit):
                kind = "rabbit_battle"
            else:
                kind = ally.KIND

            rend = self.renderers.get(kind)
            if rend:
                if isinstance(ally, Rabbit):
                    aw, ah = 160, 160
                    flip = False
                    frame = ally.get_current_frame() if hasattr(ally, "get_current_frame") else 0
                else:
                    aw, ah = 90, 90
                    flip = True
                    frame = ally.get_current_frame() if hasattr(ally, "get_current_frame") else 0

                rend.draw(
                    int(ally.draw_x),
                    int(ally.draw_y),
                    aw,
                    ah,
                    frame,
                    flip_x=flip
                )

                # Vẽ tên + cấp phía trên sprite đồng minh
                draw_ally_sprite_status(
                    ally,
                    int(ally.draw_x),
                    int(ally.draw_y),
                    aw,
                    ah,
                    self.text_ren,
                    is_active=(ally == self.current_actor)
                )

        # Vẽ projectile nếu đang Ranged hoặc Catch
        if self.state == BS_PLAYER_ANIM:
            d = self.anim_data
            if (d.get("ranged") or d.get("type") == "catch") and d.get("phase") == 0:
                self._draw_projectile(
                    int(d["proj_x"]),
                    int(d["proj_y"]),
                    is_catch=(d.get("type") == "catch")
                )

        # Vẽ projectile của Fox: Kunai / Smoke
        if self.state == BS_ENEMY_ANIM:
            d = self.anim_data
            if d.get("type") == "fox_act" and d.get("phase") == 0:
                if d.get("proj_type") == "kunai":
                    self._draw_kunai(int(d["proj_x"]), int(d["proj_y"]))
                elif d.get("proj_type") == "smoke":
                    self._draw_smoke_ball(int(d["proj_x"]), int(d["proj_y"]))

        # UI: Vẽ panel thông số ở sát góc dưới bên trái khi tới lượt hành động của quái phe ta
        show_ally = None
        if self.state in (BS_PLAYER_SELECT, BS_TARGET_SELECT, "item_select", "catch_target_select"):
            show_ally = self.current_actor
        elif self.state == BS_PLAYER_ANIM:
            if isinstance(self.anim_data, dict):
                show_ally = self.anim_data.get("actor")
            if not show_ally:
                show_ally = self.current_actor

        if show_ally and show_ally.is_alive():
            draw_ally_status(show_ally, self.text_ren, 20, 20, is_active=(show_ally == self.current_actor))

        # Command box dọc
        if self.state in (BS_PLAYER_SELECT, BS_TARGET_SELECT, "item_select", "catch_target_select"):
            tgt_idx = min(self.selected_target, len(living)-1) if living else 0
            actor_name = "Rabbit" if isinstance(self.current_actor, Rabbit) else self.current_actor.KIND.capitalize()

            draw_command_box(
                self.selected_cmd,
                actor_name,
                self.text_ren,
                getattr(self.current_actor, 'ranged_uses', 0),
                enabled=(self.state == BS_PLAYER_SELECT),
                commands=self.actor_commands
            )

            # Vẽ Item Submenu nếu đang chọn Item hoặc ném Net hoặc Revive hoặc Heal
            if self.state in ("item_select", "catch_target_select", "revive_target_select", "heal_target_select"):
                from game.ui import draw_item_submenu
                if self.state == "revive_target_select":
                    revive_names = [("Rabbit" if isinstance(m, Rabbit) else m.KIND.capitalize()) for m in self.revive_targets]
                    draw_item_submenu(self.selected_target, revive_names, self.text_ren, is_target_select=True)
                elif self.state == "heal_target_select":
                    heal_names = [("Rabbit" if isinstance(m, Rabbit) else m.KIND.capitalize()) for m in self.heal_targets]
                    draw_item_submenu(self.selected_target, heal_names, self.text_ren, is_target_select=True)
                else:
                    draw_item_submenu(
                        self.selected_item_idx,
                        self.item_options,
                        self.text_ren,
                        net_qty=self.inventory.get("Net", 0),
                        carrot_qty=self.inventory.get("Carrot", 0),
                        revive_qty=self.inventory.get("Revive", 0)
                    )

            # Chỉ vẽ hiệu ứng highlight mục tiêu và dòng hướng dẫn khi ở trạng thái chọn mục tiêu hoặc ném Net
            if self.state in (BS_TARGET_SELECT, "catch_target_select") and living:
                te = living[tgt_idx]
                draw_target_aura(
                    int(te.draw_x) - 4,
                    int(te.draw_y) - 4,
                    98,
                    98,
                    anim_frame=self.anim_timer
                )
                self.text_ren.draw_text(
                    "WASD / Arrows: Choose target | Enter/Z: Confirm | Esc: Back",
                    SCREEN_WIDTH//2,
                    SCREEN_HEIGHT - 22,
                    size=18,
                    color=(15, 15, 20),
                    center_x=True
                )
            elif self.state == BS_PLAYER_SELECT:
                self.text_ren.draw_text(
                    "WASD / Arrows: Select command | Enter/Z/Space: Confirm",
                    SCREEN_WIDTH//2,
                    SCREEN_HEIGHT - 22,
                    size=18,
                    color=(15, 15, 20),
                    center_x=True
                )
            elif self.state == "item_select":
                self.text_ren.draw_text(
                    "WASD / Arrows: Select item | Enter/Z: Confirm | Esc: Back",
                    SCREEN_WIDTH//2,
                    SCREEN_HEIGHT - 22,
                    size=18,
                    color=(15, 15, 20),
                    center_x=True
                )
            elif self.state in ("revive_target_select", "heal_target_select"):
                self.text_ren.draw_text(
                    "WASD / Arrows: Select member | Enter/Z: Confirm | Esc: Back",
                    SCREEN_WIDTH//2,
                    SCREEN_HEIGHT - 22,
                    size=18,
                    color=(15, 15, 20),
                    center_x=True
                )
        else:
            if self.state not in (BS_WIN, BS_LOSE):
                actor_name = "Rabbit" if isinstance(self.current_actor, Rabbit) else self.current_actor.KIND.capitalize()
                draw_command_box(
                    self.selected_cmd,
                    actor_name,
                    self.text_ren,
                    getattr(self.current_actor, 'ranged_uses', 0),
                    enabled=False,
                    commands=self.actor_commands
                )

        # Floating texts
        for f in self.floats:
            f.draw(self.text_ren)

        # Message log
        self.msg_log.draw(self.text_ren, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)

        # Kết quả
        if self.state == BS_WIN and self.result_timer > 30:
            self._draw_result_banner()
        elif self.state == BS_LOSE and self.result_timer > 30:
            self._draw_result_banner()


    def _draw_projectile(self, px, py, is_catch=False):
        glDisable(GL_TEXTURE_2D)

        if is_catch:
            # Vẽ lưới bắt quái: hình thoi + các đường lưới
            size = 18
            glColor3f(0.55, 0.25, 0.85)
            glLineWidth(3)

            glBegin(GL_LINE_LOOP)
            glVertex2f(px, py + size)
            glVertex2f(px + size, py)
            glVertex2f(px, py - size)
            glVertex2f(px - size, py)
            glEnd()

            glLineWidth(1)
            glBegin(GL_LINES)
            glVertex2f(px - size, py)
            glVertex2f(px + size, py)
            glVertex2f(px, py - size)
            glVertex2f(px, py + size)
            glVertex2f(px - size // 2, py + size // 2)
            glVertex2f(px + size // 2, py - size // 2)
            glVertex2f(px - size // 2, py - size // 2)
            glVertex2f(px + size // 2, py + size // 2)
            glEnd()
        else:
            # Đạn ranged của Rabbit: viên tròn vàng
            radius = 8
            segments = 24

            glColor3f(1.0, 0.9, 0.2)
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(px, py)
            for i in range(segments + 1):
                angle = 2 * math.pi * i / segments
                glVertex2f(px + math.cos(angle) * radius, py + math.sin(angle) * radius)
            glEnd()

            glColor3f(1.0, 0.6, 0.1)
            glLineWidth(2)
            glBegin(GL_LINE_LOOP)
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                glVertex2f(px + math.cos(angle) * (radius + 2), py + math.sin(angle) * (radius + 2))
            glEnd()

        glColor3f(1, 1, 1)
        glEnable(GL_TEXTURE_2D)

    def _draw_kunai(self, px, py):
        glDisable(GL_TEXTURE_2D)

        # Kunai nhọn bay sang trái
        glColor3f(0.85, 0.85, 0.85)
        glBegin(GL_TRIANGLES)
        glVertex2f(px - 24, py)
        glVertex2f(px + 14, py + 8)
        glVertex2f(px + 14, py - 8)
        glEnd()

        # Cán kunai
        glColor3f(0.20, 0.20, 0.20)
        glLineWidth(4)
        glBegin(GL_LINES)
        glVertex2f(px + 12, py)
        glVertex2f(px + 28, py)
        glEnd()

        glColor3f(1, 1, 1)
        glEnable(GL_TEXTURE_2D)

    def _draw_smoke_ball(self, px, py):
        radius = 14
        segments = 24

        glDisable(GL_TEXTURE_2D)

        glColor3f(0.45, 0.45, 0.45)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(px, py)
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            glVertex2f(px + math.cos(angle) * radius, py + math.sin(angle) * radius)
        glEnd()

        glColor3f(0.65, 0.65, 0.65)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            glVertex2f(px + math.cos(angle) * (radius + 3), py + math.sin(angle) * (radius + 3))
        glEnd()

        glColor3f(1, 1, 1)
        glEnable(GL_TEXTURE_2D)


    def _draw_result_banner(self):
        from game.ui import draw_pokemon_panel
        panel_w = 460
        panel_h = 180
        panel_x = SCREEN_WIDTH // 2 - panel_w // 2
        panel_y = SCREEN_HEIGHT // 2 - panel_h // 2
        draw_pokemon_panel(panel_x, panel_y, panel_w, panel_h)
        rabbit = next((m for m in self.party if isinstance(m, Rabbit)), self.party[0])
        mid_y = SCREEN_HEIGHT // 2
        if self.result == "win":
            self.text_ren.draw_text("VICTORY!", SCREEN_WIDTH//2, mid_y + 40 if self.leveled_up else mid_y + 20,
                                    size=48, color=(20, 120, 20), center_x=True, center_y=True)
            if self.leveled_up:
                self.text_ren.draw_text(f"Level UP! → Lv.{rabbit.level}",
                                        SCREEN_WIDTH//2, mid_y,
                                        size=26, color=(200, 100, 10), center_x=True, center_y=True)
            self.text_ren.draw_text("Press ENTER to continue",
                                    SCREEN_WIDTH//2, mid_y - 45 if self.leveled_up else mid_y - 30,
                                    size=20, color=(80, 80, 80), center_x=True, center_y=True)
        elif self.result == "lose":
            self.text_ren.draw_text("DEFEAT...", SCREEN_WIDTH//2, mid_y + 20,
                                    size=48, color=(180, 20, 20), center_x=True, center_y=True)
            self.text_ren.draw_text("Press ENTER to continue",
                                    SCREEN_WIDTH//2, mid_y - 30,
                                    size=20, color=(80, 80, 80), center_x=True, center_y=True)
        elif self.result == "run":
            self.text_ren.draw_text("Escaped!", SCREEN_WIDTH//2, mid_y + 20,
                                    size=38, color=(20, 80, 160), center_x=True, center_y=True)
            self.text_ren.draw_text("Press ENTER to continue",
                                    SCREEN_WIDTH//2, mid_y - 30,
                                    size=20, color=(80, 80, 80), center_x=True, center_y=True)

    def is_done(self):
        return self.state in (BS_WIN, BS_LOSE) and self.result_timer > 60

    def handle_done_input(self, event):
        if event.type == pg.KEYDOWN and event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
            if self.state in (BS_WIN, BS_LOSE) and self.result_timer > 30:
                return True
        return False
