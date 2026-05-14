import pygame as pg
from OpenGL.GL import *
from OpenGL.GLU import *
from renderer.sprite_renderer import SpriteRenderer 
from entities.player import Player
from entities.enemies import Enemy
from entities.item import Item
from entities.ground import Ground
from utils.constants import ENEMY_WIDTH, ENEMY_HEIGHT, GROUND_Y_AREA_A
from utils.font_renderer import FontRenderer

# Trạng thái game
STATE_START = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2

def check_collision(rect1, rect2):
    return (rect1.x < rect2.x + rect2.width and
            rect1.x + rect1.width > rect2.x and
            rect1.y < rect2.y + rect2.height and
            rect1.y + rect1.height > rect2.y)

def draw_hearts(hp, renderer):
    # Vẽ 3 vị trí trái tim cố định
    for i in range(3):
        # Nếu chỉ số i < hp thì vẽ tim đầy (frame 1), ngược lại vẽ tim rỗng (frame 0)
        frame = 0 if i < hp else 1
        renderer.draw(50 + i * 50, 650, 40, 40, frame)

def draw_sky():
    glDisable(GL_TEXTURE_2D)
    glBegin(GL_QUADS)
    # Màu xanh đậm phía trên
    glColor3f(0.3, 0.6, 0.9)
    glVertex2f(0, 720)
    glVertex2f(1280, 720)
    # Màu xanh nhạt (hơi trắng) phía dưới chân trời
    glColor3f(0.7, 0.9, 1.0)
    glVertex2f(1280, 0)
    glVertex2f(0, 0)
    glEnd()
    glColor3f(1, 1, 1)
    glEnable(GL_TEXTURE_2D)

def main():
    pg.init()
    display = (1280, 720)
    pg.display.set_mode(display, pg.DOUBLEBUF | pg.OPENGL)
    pg.display.set_caption("Game Platformer 2D - OpenGL")

    glViewport(0, 0, 1280, 720)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, 1280, 0, 720) 
    glMatrixMode(GL_MODELVIEW)

    # Nạp Renderers
    player_renderer = SpriteRenderer("assets/player/Player.png", rows=3, cols=3)
    enemy_renderer = SpriteRenderer("assets/enemies/Enemy.png", rows=2, cols=4)
    item_renderer = SpriteRenderer("assets/item/Carrot.png", rows=1, cols=1)
    heart_renderer = SpriteRenderer("assets/objects/Heart.png", rows=2, cols=1)
    tile_renderer = SpriteRenderer("assets/ground/ground.png", rows=1, cols=1)   
    player = Player(100, GROUND_Y_AREA_A, 64, 64, player_renderer) 
    ground = Ground(tile_renderer)    
    # Khởi tạo một số kẻ địch và vật phẩm tại các vị trí cố định trên map
    enemies = [
        Enemy(800, GROUND_Y_AREA_A, ENEMY_WIDTH, ENEMY_HEIGHT, enemy_renderer),
        Enemy(1500, GROUND_Y_AREA_A, ENEMY_WIDTH, ENEMY_HEIGHT, enemy_renderer),
        Enemy(2500, GROUND_Y_AREA_A, ENEMY_WIDTH, ENEMY_HEIGHT, enemy_renderer)
    ]
    items = [
        Item(500, GROUND_Y_AREA_A + 150, 40, 40, item_renderer),
        Item(1200, GROUND_Y_AREA_A + 200, 40, 40, item_renderer),
        Item(2000, GROUND_Y_AREA_A + 150, 40, 40, item_renderer)
    ]
    
    camera_x = 0
    score = 0
    game_state = STATE_START

    clock = pg.time.Clock()
    
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return
            if event.type == pg.KEYDOWN:
                if game_state == STATE_START:
                    game_state = STATE_PLAYING
                elif game_state == STATE_GAMEOVER:
                    player.hp = 3
                    player.x, player.y = 100, GROUND_Y_AREA_A
                    score = 0
                    game_state = STATE_PLAYING

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if game_state == STATE_START:
            draw_sky()
            player_renderer.draw(600, 360, 128, 128, 0)
            
        elif game_state == STATE_PLAYING:
            keys = pg.key.get_pressed()
            
            # 1. Cập nhật Player
            player.update(keys)
            
            # Giới hạn nhân vật không đi quá map bên trái
            if player.x < 0: player.x = 0
            
            # 2. Cập nhật Camera (Giữ player ở giữa màn hình)
            camera_x = player.x - 640
            # Giới hạn camera không đi quá map bên trái
            if camera_x < 0: camera_x = 0
            # Giới hạn camera không đi quá map bên phải (Map dài 100 tiles * 64 = 6400)
            if camera_x > 6400 - 1280: camera_x = 6400 - 1280

            # --- VẼ THEO THỨ TỰ LỚP ---
            draw_sky()
            
            # Vẽ Ground với Camera offset
            ground.draw(camera_x)
            
            # Vẽ Player với Camera offset
            if player.invincible_timer % 10 < 5:
                player.draw(camera_x)

            # Quản lý Enemies
            for enemy in enemies:
                # Enemy trong chế độ phiêu lưu có thể đứng yên hoặc tuần tra
                # Ở đây chúng ta giữ nguyên update nhưng truyền camera vào draw
                enemy.update() 
                enemy.draw(camera_x)
                
                if player.invincible_timer == 0 and check_collision(player, enemy):
                    player.hp -= 1
                    player.invincible_timer = 60
                    if player.hp <= 0:
                        game_state = STATE_GAMEOVER

            # Quản lý Items
            for item in items[:]:
                item.update()
                item.draw(camera_x)
                if check_collision(player, item):
                    if player.hp < 3: player.hp += 1
                    items.remove(item)
                    score += 10 # Ăn cà rốt được điểm

            # Vẽ UI (Cố định trên màn hình, không bị camera ảnh hưởng)
            draw_hearts(player.hp, heart_renderer)
            glColor3f(1, 1, 1)
            FontRenderer.draw_number(score, 1100, 650, 30)

        elif game_state == STATE_GAMEOVER:
            glClearColor(0.4, 0.0, 0.0, 1.0)
            FontRenderer.draw_number(score, 580, 300, 80)

        pg.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
