from entities.base_entity import BaseEntity
from OpenGL.GL import *
import math

class Item(BaseEntity):
    def __init__(self, x, y, width, height, renderer):
        super().__init__(x, y, width, height)
        self.renderer = renderer
        self.start_y = y
        self.timer = 0

    def update(self):
        # Hiệu ứng lơ lửng (Floating effect)
        self.timer += 0.1
        self.y = self.start_y + math.sin(self.timer) * 10

    def draw(self, camera_x):
        draw_x = self.x - camera_x
        self.renderer.draw(draw_x, self.y, self.width, self.height, 0)
