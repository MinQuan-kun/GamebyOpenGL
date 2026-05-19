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
    draw_ally_status, draw_enemy_status, draw_command_box,
    FloatingText, MessageLog, COL_WHITE, COL_YELLOW,
    COL_RED, COL_GREEN, COL_ORANGE, COL_PURPLE, COL_GRAY
)
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, RANGED_USES_MAX

# ── Trạng thái battle ──────────────────────────────────────────────────────
BS_PLAYER_SELECT  = "player_select"   # Chờ người chơi chọn lệnh
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


def draw_battle_bg(is_boss=False):
    key = "boss" if is_boss else "grass"
    c1, c2 = BG_COLORS[key]
    glDisable(GL_TEXTURE_2D)
    glBegin(GL_QUADS)
    glColor3f(*c2); glVertex2f(0, 0)
    glColor3f(*c2); glVertex2f(SCREEN_WIDTH, 0)
    glColor3f(*c1); glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)
    glColor3f(*c1); glVertex2f(0, SCREEN_HEIGHT)
    glEnd()
    glColor3f(1, 1, 1)
    glEnable(GL_TEXTURE_2D)


# ── Vị trí địch trên màn hình ─────────────────────────────────────────────
ENEMY_SLOTS = [
    (160, 350),   # slot 0
    (300, 290),   # slot 1
    (120, 240),   # slot 2 (hiếm khi dùng, quái thứ 3)
]

ALLY_BASE_X = 820
ALLY_BASE_Y = 320


class BattleSystem:
    def __init__(self, rabbit, enemies, text_renderer, renderers, is_boss=False):
        self.rabbit      = rabbit
        self.enemies     = enemies          # list BaseEnemy
        self.text_ren    = text_renderer
        self.renderers   = renderers        # dict: kind -> SpriteRenderer
        self.is_boss     = is_boss

        # Gán vị trí cho địch
        for i, e in enumerate(self.enemies):
            sx, sy = ENEMY_SLOTS[min(i, len(ENEMY_SLOTS)-1)]
            e.base_x = sx; e.draw_x = sx
            e.base_y = sy; e.draw_y = sy

        # Vị trí thỏ (đứng yên bên phải)
        rabbit.draw_x = ALLY_BASE_X
        rabbit.draw_y = ALLY_BASE_Y

        self.state       = BS_PLAYER_SELECT
        self.selected_cmd = 0   # 0=Attack,1=Ranged,2=Guard,3=Run
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

        self.rabbit.reset_battle_state()

        # Fox: lên kế hoạch trước
        for e in self.enemies:
            if isinstance(e, Fox):
                e.plan_turn()

        self.result_timer = 0

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _living_enemies(self):
        return [e for e in self.enemies if e.is_alive()]

    def _add_float(self, text, x, y, color=COL_WHITE, size=26):
        self.floats.append(FloatingText(text, x, y + 60, color, size))

    def _push_msg(self, msg):
        self.msg_log.push(msg)

    # ── Input xử lý ─────────────────────────────────────────────────────────
    def handle_input(self, event):
        if self.state != BS_PLAYER_SELECT:
            return

        living = self._living_enemies()
        if not living:
            return

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                self.selected_cmd = (self.selected_cmd - 1) % 4
            elif event.key == pg.K_RIGHT:
                self.selected_cmd = (self.selected_cmd + 1) % 4
            elif event.key == pg.K_UP:
                self.selected_cmd = (self.selected_cmd - 2) % 4
            elif event.key == pg.K_DOWN:
                self.selected_cmd = (self.selected_cmd + 2) % 4
            elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                self._confirm_command(living)
            # Tab: đổi mục tiêu
            elif event.key == pg.K_TAB:
                if living:
                    self.selected_target = (self.selected_target + 1) % len(living)
            # Chọn mục tiêu (số 1-3)
            elif event.key == pg.K_1 and len(living) >= 1:
                self.selected_target = 0
            elif event.key == pg.K_2 and len(living) >= 2:
                self.selected_target = 1
            elif event.key == pg.K_3 and len(living) >= 3:
                self.selected_target = 2

    def _confirm_command(self, living):
        cmd = self.selected_cmd
        if cmd == 1 and self.rabbit.ranged_uses <= 0:
            self._push_msg("Hết đạn Ranged!")
            return

        tgt = living[min(self.selected_target, len(living)-1)]

        if cmd == 0:   # Attack
            self._queue_rabbit_attack(tgt, ranged=False)
        elif cmd == 1: # Ranged
            self._queue_rabbit_attack(tgt, ranged=True)
        elif cmd == 2: # Guard
            self._queue_guard()
        elif cmd == 3: # Run
            self._queue_run()

    # ── Queue actions ────────────────────────────────────────────────────────
    def _queue_rabbit_attack(self, target, ranged=False):
        self.rabbit.is_guarding = False  # Guard chỉ kéo dài 1 lượt
        self.state = BS_PLAYER_ANIM
        self.anim_timer = 0

        if ranged:
            self.rabbit.ranged_uses -= 1
            miss_c = MISS_CHANCE_RANGED + (0.25 if self.rabbit.smoke_miss_bonus else 0)
            crit_c = CRIT_CHANCE_RANGED
        else:
            miss_c = MISS_CHANCE + (0.25 if self.rabbit.smoke_miss_bonus else 0)
            crit_c = CRIT_CHANCE

        dmg, is_crit, is_miss = calc_attack_damage(self.rabbit.atk, miss_c, crit_c)

        # Lưu vào anim_data để animation xử lý
        self.anim_data = {
            "type": "rabbit_atk",
            "ranged": ranged,
            "target": target,
            "dmg": dmg,
            "is_crit": is_crit,
            "is_miss": is_miss,
            "phase": 0,      # 0=move, 1=hit, 2=return
            "start_x": self.rabbit.draw_x,
            "start_y": self.rabbit.draw_y,
            "proj_x": float(self.rabbit.draw_x),
            "proj_y": float(self.rabbit.draw_y),
            "applied": False,
        }

    def _queue_guard(self):
        self.rabbit.is_guarding = True
        self._push_msg("Rabbit đang phòng thủ! Sát thương nhận vào giảm 1/3.")
        self._start_enemy_turn()

    def _queue_run(self):
        living = self._living_enemies()
        if self.is_boss:
            self._push_msg("Không thể bỏ trốn khỏi Boss!")
            return
        if len(living) == 1:
            success = True
        else:
            success = (random.random() > 1/3)

        if success:
            self.result = "run"
            self.state  = BS_WIN
            self._push_msg("Bỏ trốn thành công!")
        else:
            self._push_msg("Bỏ trốn thất bại! Mất lượt.")
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
        dmg, is_crit, is_miss = calc_attack_damage(
            enemy.atk,
            miss_chance=self.rabbit.get_miss_chance(),
        )
        self.anim_data = {
            "type": "enemy_atk",
            "enemy": enemy,
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
        self.anim_data = {
            "type": "fox_act",
            "fox": fox,
            "act": act,
            "phase": 0,
            "applied": False,
        }

    def _end_turn(self):
        """Cuối lượt: xử lý poison, kiểm tra thua."""
        if self.rabbit.poisoned:
            pdmg = max(1, int(self.rabbit.max_hp * 0.05 * self.rabbit.poison_stacks))
            self.rabbit.hp = max(0, self.rabbit.hp - pdmg)
            self._push_msg(f"Poison gây {pdmg} sát thương!")
            self._add_float(f"-{pdmg} PSN", self.rabbit.draw_x, self.rabbit.draw_y, COL_PURPLE)

        if not self.rabbit.is_alive():
            self.result = "lose"
            self.state  = BS_LOSE
            self._push_msg("Rabbit đã ngã xuống!")
            return

        # Guard chỉ tồn tại 1 lượt địch → reset
        self.rabbit.is_guarding = False

        # Fox lên kế hoạch cho lượt tiếp theo
        for e in self._living_enemies():
            if isinstance(e, Fox):
                e.plan_turn()

        # Thỏ luôn hành động trước trong lượt mới
        self.state = BS_PLAYER_SELECT

    # ── Update animation ─────────────────────────────────────────────────────
    def update(self):
        self.msg_log.update()
        for f in self.floats:
            f.update()
        self.floats = [f for f in self.floats if not f.is_dead()]

        if self.state == BS_PLAYER_ANIM:
            self._update_rabbit_anim()
        elif self.state == BS_ENEMY_ANIM:
            self._update_enemy_anim()
        elif self.state in (BS_WIN, BS_LOSE):
            self.result_timer += 1

    def _update_rabbit_anim(self):
        d = self.anim_data
        self.anim_timer += 1

        if d["type"] == "rabbit_atk":
            tgt = d["target"]
            tx, ty = tgt.draw_x + 60, tgt.draw_y + 40

            if not d["ranged"]:
                # Melee: di chuyển đến địch rồi quay về
                if d["phase"] == 0:
                    # Di chuyển đến mục tiêu
                    dx = tx - self.rabbit.draw_x
                    dy = ty - self.rabbit.draw_y
                    dist = math.hypot(dx, dy)
                    spd = 12
                    if dist < spd:
                        self.rabbit.draw_x = tx
                        self.rabbit.draw_y = ty
                        d["phase"] = 1
                        self.anim_timer = 0
                    else:
                        self.rabbit.draw_x += dx / dist * spd
                        self.rabbit.draw_y += dy / dist * spd
                elif d["phase"] == 1:
                    # Hit frame
                    if not d["applied"]:
                        d["applied"] = True
                        self._apply_rabbit_hit(d)
                    if self.anim_timer > 15:
                        d["phase"] = 2
                        self.anim_timer = 0
                elif d["phase"] == 2:
                    # Quay về
                    bx, by = ALLY_BASE_X, ALLY_BASE_Y
                    dx = bx - self.rabbit.draw_x
                    dy = by - self.rabbit.draw_y
                    dist = math.hypot(dx, dy)
                    spd = 12
                    if dist < spd:
                        self.rabbit.draw_x = bx
                        self.rabbit.draw_y = by
                        self._after_rabbit_action()
                    else:
                        self.rabbit.draw_x += dx / dist * spd
                        self.rabbit.draw_y += dy / dist * spd
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
                        self._apply_rabbit_hit(d)
                    if self.anim_timer > 20:
                        self._after_rabbit_action()

    def _apply_rabbit_hit(self, d):
        tgt = d["target"]
        if not tgt.is_alive():
            return
        if d["is_miss"]:
            self._push_msg(f"Rabbit tấn công... MISS!")
            self._add_float("Miss", tgt.draw_x + 40, tgt.draw_y, COL_GRAY, 28)
        else:
            actual = tgt.take_damage(d["dmg"])
            prefix = "CRIT! " if d["is_crit"] else ""
            self._push_msg(f"{prefix}Rabbit gây {actual} sát thương lên {tgt.KIND.capitalize()}!")
            col = COL_YELLOW if d["is_crit"] else COL_RED
            self._add_float(f"-{actual}", tgt.draw_x + 40, tgt.draw_y, col, 28)
            if not tgt.is_alive():
                self._push_msg(f"{tgt.KIND.capitalize()} đã bị đánh bại!")

    def _after_rabbit_action(self):
        self.rabbit.draw_x = ALLY_BASE_X
        self.rabbit.draw_y = ALLY_BASE_Y
        # Kiểm tra còn địch không
        if not self._living_enemies():
            self._resolve_win()
        else:
            self._start_enemy_turn()

    def _resolve_win(self):
        total_exp = sum(e.exp_reward for e in self.enemies)
        self.exp_gained = total_exp
        self.leveled_up = self.rabbit.gain_exp(total_exp)
        self.result = "win"
        self.state  = BS_WIN
        self._push_msg(f"Chiến thắng! +{total_exp} EXP")
        if self.leveled_up:
            self._push_msg(f"Rabbit lên Lv.{self.rabbit.level}!")

    def _update_enemy_anim(self):
        d = self.anim_data
        self.anim_timer += 1

        if d["type"] == "enemy_atk":
            enemy = d["enemy"]
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
                            self._push_msg(f"{enemy.KIND.capitalize()} tấn công... MISS!")
                            self._add_float("Miss", self.rabbit.draw_x, self.rabbit.draw_y, COL_GRAY)
                        else:
                            actual = self.rabbit.take_damage(d["dmg"])
                            prefix = "CRIT! " if d["is_crit"] else ""
                            self._push_msg(f"{prefix}{enemy.KIND.capitalize()} gây {actual} damage lên Rabbit!")
                            self._add_float(f"-{actual}", self.rabbit.draw_x, self.rabbit.draw_y, COL_RED)
                    if self.anim_timer > 35:
                        enemy.draw_x = enemy.base_x
                        self._check_rabbit_alive_then_next()

        elif d["type"] == "fox_act":
            fox = d["fox"]
            act = d["act"]
            if self.anim_timer < 25:
                offset = math.sin(self.anim_timer * 0.6) * 10
                fox.draw_x = fox.base_x + offset
            else:
                fox.draw_x = fox.base_x
                if not d["applied"]:
                    d["applied"] = True
                    self._apply_fox_action(fox, act)
                if self.anim_timer > 45:
                    self._check_rabbit_alive_then_next()

    def _apply_fox_action(self, fox, act):
        atype = act["type"]
        if atype == "power_charge":
            self._push_msg("Cáo đang tích tụ năng lượng! (Power Charge)")
            return

        if atype == "smoke":
            self._push_msg("Cáo ném lựu đạn khói! Rabbit bị ảnh hưởng.")
            self.rabbit.smoke_miss_bonus = True
            self.rabbit.poisoned = True
            self.rabbit.poison_stacks += 1
            self._add_float("SMOKE!", self.rabbit.draw_x, self.rabbit.draw_y + 30, COL_GRAY, 24)
            return

        # kunai
        guaranteed_crit = act.get("guaranteed_crit", False)
        no_miss         = act.get("no_miss", False)

        if no_miss:
            miss_c = 0.0
        else:
            miss_c = self.rabbit.get_miss_chance()

        if guaranteed_crit:
            dmg = fox.atk * 2
            is_crit = True
            is_miss = False
        else:
            dmg, is_crit, is_miss = calc_attack_damage(fox.atk, miss_c)

        if is_miss:
            self._push_msg("Cáo ném Kunai... MISS!")
            self._add_float("Miss", self.rabbit.draw_x, self.rabbit.draw_y, COL_GRAY)
        else:
            actual = self.rabbit.take_damage(dmg)
            prefix = "CRIT! " if is_crit else ""
            self._push_msg(f"{prefix}Cáo ném Kunai gây {actual} damage!")
            self._add_float(f"-{actual}", self.rabbit.draw_x, self.rabbit.draw_y, COL_ORANGE, 28)

    def _check_rabbit_alive_then_next(self):
        if not self.rabbit.is_alive():
            self.result = "lose"
            self.state  = BS_LOSE
            self._push_msg("Rabbit đã ngã xuống!")
        else:
            self._next_enemy_action()

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self):
        draw_battle_bg(self.is_boss)

        # Vẽ địch
        living = self._living_enemies()
        for i, e in enumerate(self.enemies):
            if not e.is_alive():
                continue
            rend = self.renderers.get(e.KIND)
            if rend:
                ew, eh = 90, 90
                rend.draw(int(e.draw_x), int(e.draw_y), ew, eh, 0)
                draw_enemy_status(e, int(e.draw_x), int(e.draw_y), ew, eh, self.text_ren)

        # Vẽ thỏ
        rabbit_rend = self.renderers.get("rabbit")
        if rabbit_rend:
            rw, rh = 80, 80
            rabbit_rend.draw(int(self.rabbit.draw_x), int(self.rabbit.draw_y), rw, rh, 0, flip_x=True)

        # Vẽ projectile nếu đang Ranged
        if self.state == BS_PLAYER_ANIM:
            d = self.anim_data
            if d.get("ranged") and d.get("phase") == 0:
                self._draw_projectile(int(d["proj_x"]), int(d["proj_y"]))

        # UI
        draw_ally_status(self.rabbit, self.text_ren, 20, 20)

        # Command box
        if self.state == BS_PLAYER_SELECT:
            tgt_idx = min(self.selected_target, len(living)-1) if living else 0
            draw_command_box(self.selected_cmd, "Rabbit",
                            self.text_ren, self.rabbit.ranged_uses)
            # Highlight mục tiêu đang chọn
            if living:
                te = living[tgt_idx]
                draw_rect_outline(int(te.draw_x)-4, int(te.draw_y)-4, 98, 98, (255, 220, 0), 3)
                self.text_ren.draw_text("Tab/1-2-3: Chọn mục tiêu  |  Mũi tên: Chọn lệnh  |  Enter/Z: Xác nhận",
                                        SCREEN_WIDTH//2, SCREEN_HEIGHT - 18, size=14,
                                        color=(160, 180, 160), center_x=True)
        else:
            draw_command_box(self.selected_cmd, "Rabbit",
                            self.text_ren, self.rabbit.ranged_uses, enabled=False)

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

    def _draw_projectile(self, px, py):
        glDisable(GL_TEXTURE_2D)
        glColor3f(1.0, 0.9, 0.2)
        glPointSize(10)
        glBegin(GL_POINTS)
        glVertex2f(px, py)
        glEnd()
        glColor3f(1, 1, 1)
        glEnable(GL_TEXTURE_2D)

    def _draw_result_banner(self):
        from game.ui import draw_panel
        draw_panel(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 60, 400, 120, 230)
        if self.result == "win":
            self.text_ren.draw_text("CHIẾN THẮNG!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20,
                                    size=48, color=(80, 255, 80), center_x=True)
            if self.leveled_up:
                self.text_ren.draw_text(f"Level UP! → Lv.{self.rabbit.level}",
                                        SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20,
                                        size=26, color=(240, 210, 50), center_x=True)
        elif self.result == "lose":
            self.text_ren.draw_text("THẤT BẠI...", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20,
                                    size=48, color=(255, 80, 80), center_x=True)
        elif self.result == "run":
            self.text_ren.draw_text("Đã bỏ trốn!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20,
                                    size=38, color=(200, 200, 80), center_x=True)
        self.text_ren.draw_text("Nhấn ENTER để tiếp tục",
                                SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40,
                                size=20, color=(180, 180, 180), center_x=True)

    def is_done(self):
        return self.state in (BS_WIN, BS_LOSE) and self.result_timer > 60

    def handle_done_input(self, event):
        if event.type == pg.KEYDOWN and event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
            if self.state in (BS_WIN, BS_LOSE) and self.result_timer > 30:
                return True
        return False
