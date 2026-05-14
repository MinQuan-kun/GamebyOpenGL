from OpenGL.GL import *

class Background:
    def __init__(self, renderer):
        self.renderer = renderer
        self.scroll_x = 0
        self.speed = 1.0 # Di chuyển chậm hơn mặt đất

    def update(self):
        self.scroll_x -= self.speed
        if self.scroll_x <= -1280:
            self.scroll_x = 0

    def draw(self):
        # Vẽ 2 mảnh nền nối đuôi nhau
        self.renderer.draw(self.scroll_x, 0, 1280, 720, 0)
        self.renderer.draw(self.scroll_x + 1280, 0, 1280, 720, 0)
