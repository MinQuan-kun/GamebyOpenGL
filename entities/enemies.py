from entities.base_entity import BaseEntity
from utils.constants import ENEMY_SPEED
from OpenGL.GL import *

class Enemy(BaseEntity):
    def __init__(self, x, y, width, height, renderer):
        super().__init__(x, y, width, height)
        self.renderer = renderer
        self.speed = ENEMY_SPEED
        self.frame = 0
        self.anim_timer = 0

    def update(self):
        self.x -= self.speed
        self.anim_timer += 1
        if self.anim_timer % 15 == 0:
            self.frame = (self.frame + 1) % 4

    def draw(self, camera_x):
        draw_x = self.x - camera_x
        self.renderer.draw(draw_x, self.y, self.width, self.height, self.frame)