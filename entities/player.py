from OpenGL.GL import *
import pygame as pg
from utils.constants import PLAYER_SPEED, JUMP_FORCE, GRAVITY, GROUND_Y_AREA_A
import time

class Player:
    def __init__(self, x, y, width, height, renderer):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.renderer = renderer
        
        # Trạng thái game
        self.hp = 3
        self.invincible_timer = 0
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        
        # Hướng nhìn
        self.flip = False
        
        # Animation
        self.anim_timer = 0
        self.frame = 0

    def update(self, keys):
        # Giảm thời gian bất tử
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # 1. Xử lý di chuyển ngang (Mũi tên hoặc A/D)
        self.vel_x = 0
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.flip = True
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.vel_x = PLAYER_SPEED
            self.flip = False
            
        # 2. Xử lý nhảy (Space hoặc W hoặc Mũi tên lên)
        if (keys[pg.K_SPACE] or keys[pg.K_w] or keys[pg.K_UP]) and not self.is_jumping:
            self.vel_y = JUMP_FORCE
            self.is_jumping = True
            
        self.vel_y -= GRAVITY
        
        # Cập nhật vị trí
        self.x += self.vel_x
        self.y += self.vel_y
        
        # 4. Va chạm
        if self.y <= GROUND_Y_AREA_A:
            self.y = GROUND_Y_AREA_A
            self.vel_y = 0
            self.is_jumping = False
            
        # 5. Logic Animation
        self.anim_timer += 1
        if self.is_jumping:
            self.frame = 7 # Giả sử frame nhảy là index 7
        elif self.vel_x != 0:
            # Animation chạy (Frame 3-6)
            if self.anim_timer % 10 == 0:
                self.frame = 3 + (self.frame - 3 + 1) % 4
        else:
            # Animation Idle (Frame 0-1)
            if self.anim_timer % 30 == 0:
                self.frame = (self.frame + 1) % 2

    def draw(self, camera_x):
        # Tọa độ vẽ = Tọa độ thế giới - Camera offset
        draw_x = self.x - camera_x
        self.renderer.draw(draw_x, self.y, self.width, self.height, self.frame, self.flip)