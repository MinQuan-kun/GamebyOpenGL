# game/combat_entities.py
# Định nghĩa các thực thể chiến đấu: Rabbit, Slime, Bee, Fox
from utils.animation import Animation
import random
import math
from utils.constants import (
    RABBIT_BASE_HP, RABBIT_BASE_ATK, RABBIT_START_LV,
    CRIT_CHANCE, CRIT_CHANCE_RANGED, MISS_CHANCE, MISS_CHANCE_RANGED,
    RANGED_USES_MAX
)


def _level_scale(base, level, factor=0.15):
    """Scale giá trị base theo cấp."""
    return int(base * (1 + factor * (level - 1)))


# ─────────────────────────────────────────────────────────────────────────────
#  RABBIT (phe ta - nhân vật chính)
# ─────────────────────────────────────────────────────────────────────────────
RABBIT_ANIMATIONS = {
    "idle": Animation(
        frames=[0],
        loop=True
    ),

    "hit": Animation(
        frames=[5],
        loop=False
    ),

    "poison": Animation(
        frames=[6],
        loop=False
    ),

    "guard": Animation(
        frames=[2],
        loop=False
    ),

    "attack": Animation(
        frames=[12, 13, 14, 15, 16, 17],
        speed=10,
        loop=False
    ),

    "ranged": Animation(
        frames=[4],
        speed=5,
        loop=False
    ),

    "dead": Animation(
        frames=[8, 9],
        speed=12,
        loop=False
    ),
}

class Rabbit:
    def __init__(self):
        self.level = RABBIT_START_LV
        self.exp = 0
        self.exp_to_next = self._calc_exp_to_next()
        self._recalc_stats()
        self.hp = self.max_hp
        # Trạng thái chiến đấu
        self.is_guarding = False        # Đang trong trạng thái Guard
        self.ranged_uses = RANGED_USES_MAX  # Lượt dùng Ranged còn lại trong trận
        self.poisoned = False           # Dính độc
        self.poison_stacks = 0         # Số lần dính độc
        self.smoke_miss_bonus = False   # Bị giảm độ chính xác do khói
        # Animation state
        #Idle
        self.animations = {
            name: Animation(anim.frames[:], anim.speed, anim.loop)
            for name, anim in RABBIT_ANIMATIONS.items()
        }

        self.anim_state = "idle"
        self.current_anim = self.animations["idle"]

        self.base_x = 820               # Vị trí X mặc định trong battle
        self.base_y = 320               # Vị trí Y mặc định trong battle
        self.draw_x = self.base_x
        self.draw_y = self.base_y

    def _calc_exp_to_next(self):
        return 20 + self.level * 15

    def _recalc_stats(self):
        self.max_hp  = _level_scale(RABBIT_BASE_HP,  self.level, 0.12)
        self.atk     = _level_scale(RABBIT_BASE_ATK, self.level, 0.10)

    def gain_exp(self, amount):
        """Cộng EXP, trả về True nếu lên cấp."""
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            old_max = self.max_hp
            self._recalc_stats()
            self.hp = min(self.hp + (self.max_hp - old_max), self.max_hp)
            self.exp_to_next = self._calc_exp_to_next()
            leveled = True
        return leveled

    def reset_battle_state(self):
        self.is_guarding = False
        self.ranged_uses = RANGED_USES_MAX
        self.poisoned = False
        self.poison_stacks = 0
        self.smoke_miss_bonus = False

    def get_miss_chance(self):
        base = MISS_CHANCE
        if self.smoke_miss_bonus:
            base += 0.25  # Khói làm tăng 25% tỉ lệ bị né
        return base

    def take_damage(self, dmg):
        if self.is_guarding:
            dmg = max(1, int(dmg * 2 / 3))
        self.hp = max(0, self.hp - dmg)
        return dmg

    def is_alive(self):
        return self.hp > 0

    def set_anim(self, state):
        if self.anim_state == state:
            return

        self.anim_state = state
        self.current_anim = self.animations[state]
        self.current_anim.reset()

    def update_animation(self):
        self.current_anim.update()

        if self.anim_state == "dead":
            return

        if self.current_anim.finished:
            if self.anim_state in ("attack", "ranged", "hit"):
                if self.hp <= 0:
                    self.set_anim("dead")
                elif self.poisoned:
                    self.set_anim("poison")
                else:
                    self.set_anim("idle")

    def get_current_frame(self):
        return self.current_anim.get_frame()


# ─────────────────────────────────────────────────────────────────────────────
#  BASE ENEMY
# ─────────────────────────────────────────────────────────────────────────────
class BaseEnemy:
    KIND    = "enemy"
    BASE_HP  = 20
    BASE_ATK = 5
    BASE_EXP = 8
    SPEED_ORDER = 0   # Số nhỏ hơn hành động trước

    def __init__(self, level):
        self.level = max(1, level)
        self.max_hp  = _level_scale(self.BASE_HP,  self.level, 0.12)
        self.atk     = _level_scale(self.BASE_ATK, self.level, 0.10)
        self.exp_reward = _level_scale(self.BASE_EXP, self.level, 0.20)
        self.hp = self.max_hp
        # Animation
        self.anim_state = "idle"
        self.anim_timer = 0
        self.anim_frame = 0
        self.base_x = 200
        self.base_y = 300
        self.draw_x = self.base_x
        self.draw_y = self.base_y
        # Trạng thái
        self.is_alive_flag = True

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        return dmg

    def choose_action(self, targets):
        """Trả về dict mô tả hành động."""
        return {"type": "attack", "target": random.choice(targets)}


# ─────────────────────────────────────────────────────────────────────────────
#  SLIME
# ─────────────────────────────────────────────────────────────────────────────
class Slime(BaseEnemy):
    KIND     = "slime"
    BASE_HP  = 18
    BASE_ATK = 5
    BASE_EXP = 8
    SPEED_ORDER = 10   # Hành động sau Bee

    def __init__(self, level):
        super().__init__(level)


# ─────────────────────────────────────────────────────────────────────────────
#  BEE
# ─────────────────────────────────────────────────────────────────────────────
class Bee(BaseEnemy):
    KIND     = "bee"
    BASE_HP  = 14
    BASE_ATK = 7
    BASE_EXP = 10
    SPEED_ORDER = 5    # Hành động trước Slime

    def __init__(self, level):
        super().__init__(level)


# ─────────────────────────────────────────────────────────────────────────────
#  FOX (Boss)
# ─────────────────────────────────────────────────────────────────────────────
class Fox(BaseEnemy):
    KIND     = "fox"
    BASE_HP  = 80
    BASE_ATK = 14
    BASE_EXP = 0       # Boss không cho EXP thông thường
    SPEED_ORDER = 20   # Hành động sau mọi thứ

    def __init__(self, level):
        super().__init__(level)
        self.power_charged = False     # Đang ở trạng thái Power Charge
        self.actions_this_turn = []    # Danh sách hành động trong lượt này
        self.action_index = 0          # Chỉ số hành động hiện tại

    def plan_turn(self):
        """Lên kế hoạch 2 hành động cho lượt này của Cáo."""
        if self.power_charged:
            # Sau Power Charge: chỉ 1 hành động = Kunai crit
            self.actions_this_turn = [{"type": "kunai", "guaranteed_crit": True, "no_miss": True}]
            self.power_charged = False
        else:
            act1 = self._random_action(can_power_charge=False)
            act2 = self._random_action(can_power_charge=True)
            self.actions_this_turn = [act1, act2]
        self.action_index = 0

    def _random_action(self, can_power_charge):
        r = random.random()
        if can_power_charge and r < 0.25:
            self.power_charged = True  # Lượt này charge, lượt sau chắc chắn Kunai crit
            return {"type": "power_charge"}
        elif r < 0.55:
            return {"type": "kunai", "guaranteed_crit": False, "no_miss": False}
        else:
            return {"type": "smoke"}

    def next_action(self):
        """Lấy hành động tiếp theo, trả về None nếu hết."""
        if self.action_index < len(self.actions_this_turn):
            act = self.actions_this_turn[self.action_index]
            self.action_index += 1
            return act
        return None

    def has_more_actions(self):
        return self.action_index < len(self.actions_this_turn)


# ─────────────────────────────────────────────────────────────────────────────
#  HÀM TIỆN ÍCH TẠO ĐÁM QUÁI
# ─────────────────────────────────────────────────────────────────────────────
def make_enemy_level(rabbit_level):
    """
    Tạo cấp quái dựa trên cấp thỏ.
    Cấp quái ≤ cấp thỏ. Quái cấp thấp hơn có tỉ lệ cao hơn.
    """
    choices = []
    weights = []
    for lv in range(1, rabbit_level + 1):
        choices.append(lv)
        # Trọng số giảm dần khi lv tăng: lv thấp → nặng hơn
        weights.append(rabbit_level - lv + 1)
    return random.choices(choices, weights=weights)[0]


def spawn_bush1_enemies(rabbit_level):
    """Bụi 1: 1-3 Slime."""
    count = random.randint(1, 3)
    return [Slime(make_enemy_level(rabbit_level)) for _ in range(count)]


def spawn_bush2_enemies(rabbit_level):
    """Bụi 2: 1-3 quái, ngẫu nhiên Slime/Bee."""
    count = random.randint(1, 3)
    enemies = []
    for _ in range(count):
        cls = random.choice([Slime, Bee])
        enemies.append(cls(make_enemy_level(rabbit_level)))
    return enemies


# ─────────────────────────────────────────────────────────────────────────────
#  TÍNH TOÁN DAMAGE
# ─────────────────────────────────────────────────────────────────────────────
def calc_attack_damage(attacker_atk, miss_chance=MISS_CHANCE,
                        crit_chance=CRIT_CHANCE, extra_miss=0.0):
    """
    Trả về (damage, is_crit, is_miss).
    damage = 0 nếu miss.
    """
    total_miss = miss_chance + extra_miss
    if random.random() < total_miss:
        return 0, False, True
    is_crit = random.random() < crit_chance
    base = attacker_atk + random.randint(-1, 2)
    dmg = base * 2 if is_crit else base
    return max(1, dmg), is_crit, False
