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
    text_ren.draw_text("Press ENTER to start", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60,
                       size=22, color=(200, 200, 100), center_x=True)
    text_ren.draw_text("WASD: Move  |  Arrows: Select  |  ENTER/Z: Confirm  |  1-2-3: Select Target",
                       SCREEN_WIDTH//2, 30, size=16, color=(140, 160, 140), center_x=True)


def draw_gameover(text_ren):
    from game.ui import draw_panel
    glClearColor(0.12, 0.02, 0.02, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_panel(SCREEN_WIDTH//2 - 260, SCREEN_HEIGHT//2 - 60, 520, 150, 220)
    text_ren.draw_text("GAME OVER", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40,
                       size=64, color=(255, 60, 60), center_x=True)
    text_ren.draw_text("Press ENTER to retry", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30,
                       size=26, color=(200, 140, 140), center_x=True)


def draw_win(text_ren, rabbit):
    from game.ui import draw_panel
    glClearColor(0.02, 0.10, 0.02, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_panel(SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT//2 - 80, 600, 180, 220)
    text_ren.draw_text("VICTORY!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60,
                       size=60, color=(80, 255, 80), center_x=True)
    text_ren.draw_text(f"You defeated Boss Fox!  Lv.{rabbit.level}",
                       SCREEN_WIDTH//2, SCREEN_HEIGHT//2, size=28,
                       color=(220, 210, 80), center_x=True)
    text_ren.draw_text("Press ENTER to play again", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50,
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
        # Rabbit dùng cho overworld
        "rabbit": safe_renderer("assets/player/Player.png", 3, 3),

        # Rabbit dùng riêng trong Battle animation
        "rabbit_battle": safe_renderer(
            "assets/sprite_sheets/rabbit_spritesheet.png",
            6,
            6
        ),

        "rabbit_front": safe_renderer("assets/player/Player_front.png", 4, 1),
        "rabbit_back":  safe_renderer("assets/player/Player_back.png", 4, 1),

        "slime":  safe_renderer("assets/enemies/Enemy.png", 2, 4),
        "bee":    safe_renderer("assets/enemies/Enemy.png", 2, 4),

        # Fox battle animation spritesheet
        "fox": safe_renderer(
            "assets/sprite_sheets/fox_spritesheet.png",
            6,
            6
        ),

        "grass":  safe_renderer("assets/newassets/grass.png", 1, 1),
    }

    def new_game():
        r = Rabbit()
        return OverworldPlayer(col=14, row=18), r, [r]

    ow_player, rabbit, party = new_game()
    state        = ST_TITLE
    battle_sys   = None
    bush_cd      = 0   # cooldown bụi cỏ
    boss_defeated = False

    ow_menu_active = False
    ow_menu_selected = 0
    ow_menu_options = ["ACTION", "PARTY", "EXIT"]

    # Party menu state variables
    ST_PARTY_MENU = 5
    ST_ITEM_MENU = 6
    ST_MESSAGE = 7
    inventory = {"Net": 100, "Carrot": 100, "Revive": 100}
    party_selected_idx = 0
    party_swap_idx = None
    party_menu_mode = None  # None, "swap", "revive", "heal", "release"
    item_selected_idx = 0
    # item_menu_options will be dynamically formatted with quantities
    item_menu_options = [
        f"CARROT (x{inventory['Carrot']})",
        f"REVIVE (x{inventory['Revive']})",
        "RELEASE",
        "CANCEL"
    ]
    ow_message = ""
    ow_post_message_state = ST_OVERWORLD

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
                    ow_player, rabbit, party = new_game()
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
                            elif sel_opt == "ACTION":
                                state = ST_ITEM_MENU
                                item_selected_idx = 0
                                ow_menu_active = False
                            elif sel_opt == "PARTY":
                                state = ST_PARTY_MENU
                                party_menu_mode = "swap"
                                party_selected_idx = 0
                                party_swap_idx = None
                                ow_menu_active = False

            # ── ITEM MENU ───────────────────────────────────────────────
            elif state == ST_ITEM_MENU:
                item_menu_options = [
                    f"CARROT (x{inventory['Carrot']})",
                    f"REVIVE (x{inventory['Revive']})",
                    "RELEASE",
                    "CANCEL"
                ]
                if event.type == pg.KEYDOWN:
                    if event.key in (pg.K_ESCAPE, pg.K_x, pg.K_BACKSPACE):
                        state = ST_OVERWORLD
                        ow_menu_active = True
                        ow_menu_selected = 0
                    elif event.key in (pg.K_UP, pg.K_w):
                        item_selected_idx = (item_selected_idx - 1) % len(item_menu_options)
                    elif event.key in (pg.K_DOWN, pg.K_s):
                        item_selected_idx = (item_selected_idx + 1) % len(item_menu_options)
                    elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                        sel_item = item_menu_options[item_selected_idx]
                        if "CANCEL" in sel_item:
                            state = ST_OVERWORLD
                            ow_menu_active = True
                            ow_menu_selected = 0
                        elif "CARROT" in sel_item:
                            if inventory["Carrot"] <= 0:
                                ow_message = "No Carrots left!"
                                ow_post_message_state = ST_ITEM_MENU
                                state = ST_MESSAGE
                            else:
                                alive_members = [m for m in party if m.hp > 0 and m.hp < m.max_hp]
                                if not alive_members:
                                    ow_message = "No injured allies need healing!"
                                    ow_post_message_state = ST_ITEM_MENU
                                    state = ST_MESSAGE
                                else:
                                    state = ST_PARTY_MENU
                                    party_menu_mode = "heal"
                                    party_selected_idx = 0
                        elif "REVIVE" in sel_item:
                            if inventory["Revive"] <= 0:
                                ow_message = "No Revives left!"
                                ow_post_message_state = ST_ITEM_MENU
                                state = ST_MESSAGE
                            else:
                                fainted_members = [m for m in party if m.hp <= 0]
                                if not fainted_members:
                                    ow_message = "No fainted allies to revive!"
                                    ow_post_message_state = ST_ITEM_MENU
                                    state = ST_MESSAGE
                                else:
                                    state = ST_PARTY_MENU
                                    party_menu_mode = "revive"
                                    party_selected_idx = 0
                        elif "RELEASE" in sel_item:
                            if len(party) <= 3:
                                ow_message = "No standby allies to release!"
                                ow_post_message_state = ST_ITEM_MENU
                                state = ST_MESSAGE
                            else:
                                state = ST_PARTY_MENU
                                party_menu_mode = "release"
                                party_selected_idx = 3

            # ── PARTY MENU ──────────────────────────────────────────────
            elif state == ST_PARTY_MENU:
                if event.type == pg.KEYDOWN:
                    if event.key in (pg.K_ESCAPE, pg.K_x):
                        if party_swap_idx is not None:
                            party_swap_idx = None
                        else:
                            if party_menu_mode in ("revive", "heal", "release"):
                                state = ST_ITEM_MENU
                                party_menu_mode = None
                            else:
                                state = ST_OVERWORLD
                                ow_menu_active = True
                    elif event.key in (pg.K_UP, pg.K_w):
                        party_selected_idx = (party_selected_idx - 1) % 6
                    elif event.key in (pg.K_DOWN, pg.K_s):
                        party_selected_idx = (party_selected_idx + 1) % 6
                    elif event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE):
                        if party_menu_mode == "revive":
                            if party_selected_idx < len(party):
                                member = party[party_selected_idx]
                                if member.hp <= 0:
                                    inventory["Revive"] = max(0, inventory["Revive"] - 1)
                                    member.hp = member.max_hp // 2
                                    member_name = "Rabbit" if isinstance(member, Rabbit) else member.KIND.capitalize()
                                    ow_message = f"Revived {member_name}!"
                                    ow_post_message_state = ST_ITEM_MENU
                                    state = ST_MESSAGE
                                    party_menu_mode = None
                                else:
                                    ow_message = "This ally is not fainted!"
                                    ow_post_message_state = ST_PARTY_MENU
                                    state = ST_MESSAGE
                            else:
                                ow_message = "This slot is empty!"
                                ow_post_message_state = ST_PARTY_MENU
                                state = ST_MESSAGE
                        elif party_menu_mode == "heal":
                            if party_selected_idx < len(party):
                                member = party[party_selected_idx]
                                if member.hp <= 0:
                                    ow_message = "Cannot heal a fainted ally!"
                                    ow_post_message_state = ST_PARTY_MENU
                                    state = ST_MESSAGE
                                elif member.hp >= member.max_hp:
                                    ow_message = "This ally is already at full HP!"
                                    ow_post_message_state = ST_PARTY_MENU
                                    state = ST_MESSAGE
                                else:
                                    inventory["Carrot"] = max(0, inventory["Carrot"] - 1)
                                    heal_amt = member.max_hp // 2
                                    member.hp = min(member.max_hp, member.hp + heal_amt)
                                    member_name = "Rabbit" if isinstance(member, Rabbit) else member.KIND.capitalize()
                                    ow_message = f"{member_name} recovered {heal_amt} HP!"
                                    ow_post_message_state = ST_ITEM_MENU
                                    state = ST_MESSAGE
                                    party_menu_mode = None
                            else:
                                ow_message = "This slot is empty!"
                                ow_post_message_state = ST_PARTY_MENU
                                state = ST_MESSAGE
                        elif party_menu_mode == "release":
                            if party_selected_idx < 3:
                                ow_message = "Cannot release active battle members!"
                                ow_post_message_state = ST_PARTY_MENU
                                state = ST_MESSAGE
                            elif party_selected_idx >= len(party):
                                ow_message = "This slot is empty!"
                                ow_post_message_state = ST_PARTY_MENU
                                state = ST_MESSAGE
                            else:
                                member = party[party_selected_idx]
                                member_name = "Rabbit" if isinstance(member, Rabbit) else member.KIND.capitalize()
                                party.pop(party_selected_idx)
                                rabbit = next((m for m in party if isinstance(m, Rabbit)), party[0])
                                ow_message = f"Released {member_name} back to the wild!"
                                ow_post_message_state = ST_ITEM_MENU
                                state = ST_MESSAGE
                                party_menu_mode = None
                        else:
                            if party_swap_idx is None:
                                if party_selected_idx < len(party):
                                    party_swap_idx = party_selected_idx
                            else:
                                if party_selected_idx < len(party):
                                    idx1, idx2 = party_swap_idx, party_selected_idx
                                    party[idx1], party[idx2] = party[idx2], party[idx1]
                                    rabbit = next((m for m in party if isinstance(m, Rabbit)), party[0])
                                party_swap_idx = None

            # ── MESSAGE STATE ───────────────────────────────────────────
            elif state == ST_MESSAGE:
                if event.type == pg.KEYDOWN:
                    if event.key in (pg.K_RETURN, pg.K_z, pg.K_SPACE, pg.K_ESCAPE, pg.K_x):
                        state = ow_post_message_state
                        ow_message = ""

            # ── BATTLE ──────────────────────────────────────────────────
            elif state == ST_BATTLE and battle_sys is not None:
                battle_sys.handle_input(event)
                if battle_sys.handle_done_input(event):
                    # Kết thúc battle
                    result = battle_sys.result
                    if result == "win" and battle_sys.is_boss:
                        state = ST_WIN
                        boss_defeated = True
                    else:
                        if all(m.hp <= 0 for m in party):
                            state = ST_GAMEOVER
                        else:
                            state = ST_OVERWORLD
                            bush_cd = BUSH_COOLDOWN
                            # Lưu lại ô cỏ vừa kết thúc trận đấu để không gặp lại khi đứng yên
                            ow_player.last_battle_tile = (ow_player.col(), ow_player.row())
                            
                            if all(m.hp <= 0 for m in party[:3]):
                                alive = [m for m in party if m.hp > 0]
                                dead = [m for m in party if m.hp <= 0]
                                party.clear()
                                party.extend(alive + dead)
                                rabbit = next((m for m in party if isinstance(m, Rabbit)), party[0])
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
                    boss_lv = max(1, rabbit.level)
                    fox = Fox(boss_lv)
                    battle_sys = BattleSystem(party, [fox], text_ren, renderers, inventory, is_boss=True)
                    state = ST_BATTLE
                    bush_cd = BUSH_COOLDOWN
                    ow_menu_active = False
                elif cur_tile == T_BUSH:
                    enemies = spawn_bush1_enemies(rabbit.level)
                    battle_sys = BattleSystem(party, enemies, text_ren, renderers, inventory, is_boss=False)
                    state = ST_BATTLE
                    bush_cd = BUSH_COOLDOWN
                    ow_menu_active = False
                elif cur_tile == T_BUSH2:
                    enemies = spawn_bush2_enemies(rabbit.level)
                    battle_sys = BattleSystem(party, enemies, text_ren, renderers, inventory, is_boss=False)
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
                text_ren.draw_text("Boss has been defeated!", SCREEN_WIDTH//2, SCREEN_HEIGHT - 22,
                                   size=16, color=(220, 200, 80), center_x=True)

        elif state == ST_ITEM_MENU:
            draw_overworld(ow_player, text_ren, renderers=renderers)
            from game.ui import draw_overworld_menu
            item_menu_options = [
                f"CARROT (x{inventory['Carrot']})",
                f"REVIVE (x{inventory['Revive']})",
                "RELEASE",
                "CANCEL"
            ]
            draw_overworld_menu(item_selected_idx, item_menu_options, text_ren)

        elif state == ST_PARTY_MENU:
            # Vẽ nền overworld phía sau
            draw_overworld(ow_player, text_ren, renderers=renderers)
            # Vẽ Party menu Pokemon đè lên trên
            from game.ui import draw_pokemon_party_menu
            draw_pokemon_party_menu(party_selected_idx, party, text_ren, swap_idx=party_swap_idx, menu_mode=party_menu_mode)

        elif state == ST_MESSAGE:
            # Draw underlying
            if ow_post_message_state == ST_PARTY_MENU:
                draw_overworld(ow_player, text_ren, renderers=renderers)
                from game.ui import draw_pokemon_party_menu
                draw_pokemon_party_menu(party_selected_idx, party, text_ren, swap_idx=party_swap_idx, menu_mode=party_menu_mode)
            elif ow_post_message_state == ST_ITEM_MENU:
                draw_overworld(ow_player, text_ren, renderers=renderers)
                from game.ui import draw_overworld_menu
                item_menu_options = [
                    f"CARROT (x{inventory['Carrot']})",
                    f"REVIVE (x{inventory['Revive']})",
                    "RELEASE",
                    "CANCEL"
                ]
                draw_overworld_menu(item_selected_idx, item_menu_options, text_ren)
            else:
                draw_overworld(ow_player, text_ren, renderers=renderers)
                if ow_menu_active:
                    from game.ui import draw_overworld_menu
                    draw_overworld_menu(ow_menu_selected, ow_menu_options, text_ren)
            
            # Draw message box
            from game.ui import draw_panel
            panel_w = 500
            panel_h = 80
            panel_x = (SCREEN_WIDTH - panel_w) // 2
            panel_y = 40
            draw_panel(panel_x, panel_y, panel_w, panel_h, 230)
            text_ren.draw_text(ow_message, SCREEN_WIDTH // 2, panel_y + panel_h // 2 - 8,
                               size=18, color=(15, 15, 20), center_x=True)
            text_ren.draw_text("Press Z or ENTER to continue...", SCREEN_WIDTH // 2, panel_y + 12,
                               size=12, color=(120, 120, 120), center_x=True)

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
