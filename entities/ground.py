from utils.constants import GROUND_DISPLAY_Y

class Ground:
    def __init__(self, renderer):
        self.renderer = renderer
        self.img_w = renderer.w
        self.img_h = renderer.h

    def draw(self, camera_x):
        start_x = (camera_x // self.img_w) * self.img_w
        
        current_x = start_x
        while current_x < camera_x + 1280:
            draw_x = int(current_x - camera_x)
            
            self.renderer.draw(draw_x, GROUND_DISPLAY_Y, self.img_w, self.img_h, 0)
            
            current_x += self.img_w