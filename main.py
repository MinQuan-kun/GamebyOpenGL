# main.py  –  Pokemon Turn-Based Game (OpenGL + Pygame)
import pygame as pg
from OpenGL.GL import *
from OpenGL.GLU import *

from renderer.sprite_renderer import SpriteRenderer
from utils.text_renderer import TextRenderer
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT

from game.overworld import (
    OverworldPlayer, draw_overworld,
    TILEMAP, T_BUSH, T_BUSH2, T_BOSS, MAP_ROWS, TILE
)
from game.combat_entities import (
    Rabbit, Fox, spawn_bush1_enemies, spawn_bush2_enemies
)
from game.battle import BattleSystem

# ── Game States ───────────────────────────────────────────────────────────
ST_TITLE     = 0
ST_OVERWORLD = 1
ST_BATTLE    = 2
ST_GAMEOVER  = 3
ST_WIN       = 4

# ── Cooldown bụi cỏ (frames) để không liên tục trigger ───────────────────
BUSH_COOLDOWN = 180


def setup_opengl():
    glViewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


def draw_title(text_ren):
    glClearColor(0.05, 0.08, 0.05, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    # Tiêu đề
    from game.ui import draw_rect_gl, draw_panel
    draw_panel(SCREEN_WIDTH//2 - 320, SCREEN_HEIGHT//2 - 20, 640, 120, 220)
    text_ren.draw_text("RABBIT ADVENTURE", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50,
                       size=60, color=(100, 240, 100), center_x=True)
    text_ren.draw_text("Turn-Based  Pokemon-Style", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10,
                       size=26, color=(180, 230, 180), center_x=True)
    text_ren.draw_text("Nhấn ENTER để bắt đầu", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60,
                       size=22, color=(200, 200, 100), center_x=True)
    text_ren.draw_text("WASD: Di chuyển  |  Mũi tên: Chọn lệnh  |  ENTER/Z: Xác nhận  |  1-2-3: Chọn mục tiêu",
                       SCREEN_WIDTH//2, 30, size=16, color=(140, 160, 140), center_x=True)


def draw_gameover(text_ren):
    from game.ui import draw_panel
    glClearColor(0.12, 0.02, 0.02, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_panel(SCREEN_WIDTH//2 - 260, SCREEN_HEIGHT//2 - 60, 520, 150, 220)
    text_ren.draw_text("GAME OVER", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40,
                       size=64, color=(255, 60, 60), center_x=True)
    text_ren.draw_text("Nhấn ENTER để chơi lại", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30,
                       size=26, color=(200, 140, 140), center_x=True)


def draw_win(text_ren, rabbit):
    from game.ui import draw_panel
    glClearColor(0.02, 0.10, 0.02, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_panel(SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT//2 - 80, 600, 180, 220)
    text_ren.draw_text("CHIẾN THẮNG!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60,
                       size=60, color=(80, 255, 80), center_x=True)
    text_ren.draw_text(f"Bạn đã đánh bại Boss Cáo!  Lv.{rabbit.level}",
                       SCREEN_WIDTH//2, SCREEN_HEIGHT//2, size=28,
                       color=(220, 210, 80), center_x=True)
    text_ren.draw_text("Nhấn ENTER để chơi lại", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50,
                       size=22, color=(160, 200, 160), center_x=True)


def main():
    pg.init()
    pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.DOUBLEBUF | pg.OPENGL)
    pg.display.set_caption("Rabbit Adventure – Turn-Based Pokemon")
    setup_opengl()

    text_ren = TextRenderer("consolas")

    # Sprite renderers (dùng placeholder 1×1 nếu file chưa có)
    def safe_renderer(path, rows=1, cols=1):
        try:
            return SpriteRenderer(path, rows, cols)
        except Exception:
            return None

    renderers = {
        # Overworld rabbit
        "rabbit": safe_renderer("assets/player/Player.png", 3, 3),

        # Battle rabbit spritesheet 11x6
        "rabbit_battle": safe_renderer(
            "assets/sprite_sheets/rabbit_spritesheet.png",
            6,
            6
        ),

        "rabbit_front": safe_renderer("assets/player/Player_front.png", 4, 1),
        "rabbit_back":  safe_renderer("assets/player/Player_back.png", 4, 1),

        "slime":  safe_renderer("assets/enemies/Enemy.png", 2, 4),
        "bee":    safe_renderer("assets/enemies/Enemy.png", 2, 4),
        "fox":    safe_renderer("assets/enemies/Enemy.png", 2, 4),

        "grass":  safe_renderer("assets/newassets/grass.png", 1, 1),
    }

    def new_game():
        return OverworldPlayer(col=14, row=18), Rabbit()

    ow_player, rabbit = new_game()
    state        = ST_TITLE
    battle_sys   = None
    bush_cd      = 0   # cooldown bụi cỏ
    boss_defeated = False

    ow_menu_active = False
    ow_menu_selected = 0
    ow_menu_options = ["ITEM", "PARTY", "EXIT"]

    clock = pg.time.Clock()

    while True:
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                return

            # ── TITLE ───────────────────────────────────────────────────
            if state == ST_TITLE:
                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    state = ST_OVERWORLD

            # ── GAMEOVER / WIN ──────────────────────────────────────────
            elif state in (ST_GAMEOVER, ST_WIN):
                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    ow_player, rabbit = new_game()
                    boss_defeated = False
                    bush_cd = 0
                    state = ST_OVERWORLD

            # ── OVERWORLD ───────────────────────────────────────────────
            elif state == ST_OVERWORLD:
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        ow_menu_active = not ow_menu_active
                        if ow_menu_active:
                            ow_menu_selected = 0
                    elif ow_menu_active:
                        if event.key in (pg.K_UP, pg.K_w):
                            ow_menu_selected = (ow_menu_selected - 1) % len(ow_menu_options)
                        elif event.key in (pg.K_DOWN, pg.K_s):
                            ow_menu_selected = (ow_menu_selected + 1) % len(ow_menu_options)
                        elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                            sel_opt = ow_menu_options[ow_menu_selected]
                            if sel_opt == "EXIT":
                                pg.quit()
                                return
                            elif sel_opt == "ITEM":
                                print("Chức năng ITEM sẽ được thực hiện trong tương lai.")
                            elif sel_opt == "PARTY":
                                print("Chức năng PARTY sẽ được thực hiện trong tương lai.")


            # ── BATTLE ──────────────────────────────────────────────────
            elif state == ST_BATTLE and battle_sys is not None:
                battle_sys.handle_input(event)
                if battle_sys.handle_done_input(event):
                    # Kết thúc battle
                    result = battle_sys.result
                    if result == "lose":
                        state = ST_GAMEOVER
                    elif result == "win" and battle_sys.is_boss:
                        state = ST_WIN
                        boss_defeated = True
                    else:
                        # win thường hoặc run → về overworld
                        if rabbit.hp <= 0:
                            state = ST_GAMEOVER
                        else:
                            state = ST_OVERWORLD
                            bush_cd = BUSH_COOLDOWN
                            # Lưu lại ô cỏ vừa kết thúc trận đấu để không gặp lại khi đứng yên
                            ow_player.last_battle_tile = (ow_player.col(), ow_player.row())
                    battle_sys = None

        # ── UPDATE ──────────────────────────────────────────────────────────
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if state == ST_TITLE:
            draw_title(text_ren)

        elif state == ST_OVERWORLD:
            keys = pg.key.get_pressed()
            if not ow_menu_active:
                ow_player.update(keys)
            else:
                ow_player.moving = False

            if bush_cd > 0:
                bush_cd -= 1

            # Kiểm tra tile hiện tại
            cur_col, cur_row = ow_player.col(), ow_player.row()
            cur_tile = ow_player.current_tile()

            # Nếu rời khỏi ô cỏ đã gặp trận đấu, reset last_battle_tile
            if getattr(ow_player, 'last_battle_tile', None) != (cur_col, cur_row):
                ow_player.last_battle_tile = None

            # Chỉ kích hoạt trận đấu khi:
            # 1. Bụi cỏ hết cooldown (bush_cd == 0)
            # 2. Đứng trên ô cỏ hoặc boss
            # 3. Người chơi đang thực sự di chuyển (ow_player.moving == True)
            # 4. Ô này không phải là ô cỏ vừa diễn ra trận đấu trước đó (ow_player.last_battle_tile is None)
            if (bush_cd == 0 and 
                cur_tile in (T_BUSH, T_BUSH2, T_BOSS) and 
                ow_player.moving and 
                getattr(ow_player, 'last_battle_tile', None) is None):
                # Trigger encounter
                if cur_tile == T_BOSS and not boss_defeated:
                    boss_lv = max(rabbit.level, rabbit.level)
                    fox = Fox(boss_lv)
                    battle_sys = BattleSystem(rabbit, [fox], text_ren, renderers, is_boss=True)
                    state = ST_BATTLE
                    bush_cd = BUSH_COOLDOWN
                    ow_menu_active = False
                elif cur_tile == T_BUSH:
                    enemies = spawn_bush1_enemies(rabbit.level)
                    battle_sys = BattleSystem(rabbit, enemies, text_ren, renderers, is_boss=False)
                    state = ST_BATTLE
                    bush_cd = BUSH_COOLDOWN
                    ow_menu_active = False
                elif cur_tile == T_BUSH2:
                    enemies = spawn_bush2_enemies(rabbit.level)
                    battle_sys = BattleSystem(rabbit, enemies, text_ren, renderers, is_boss=False)
                    state = ST_BATTLE
                    bush_cd = BUSH_COOLDOWN
                    ow_menu_active = False

            draw_overworld(ow_player, text_ren, renderers=renderers)

            if ow_menu_active:
                from game.ui import draw_overworld_menu
                draw_overworld_menu(ow_menu_selected, ow_menu_options, text_ren)

            # Mini HUD rabbit
            text_ren.draw_text(
                f"Rabbit  Lv.{rabbit.level}  HP:{rabbit.hp}/{rabbit.max_hp}  EXP:{rabbit.exp}/{rabbit.exp_to_next}",
                10, SCREEN_HEIGHT - 22, size=16, color=(200, 240, 200)
            )
            if boss_defeated:
                text_ren.draw_text("Boss đã bị đánh bại!", SCREEN_WIDTH//2, SCREEN_HEIGHT - 22,
                                   size=16, color=(220, 200, 80), center_x=True)

        elif state == ST_BATTLE and battle_sys is not None:
            battle_sys.update()
            battle_sys.draw()

        elif state == ST_GAMEOVER:
            draw_gameover(text_ren)

        elif state == ST_WIN:
            draw_win(text_ren, rabbit)

        pg.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
