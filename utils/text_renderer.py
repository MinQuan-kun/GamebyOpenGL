import pygame as pg
from OpenGL.GL import *

class TextRenderer:
    def __init__(self, font_name="consolas"):
        # Khởi tạo font hệ thống, ví dụ: 'consolas', 'arial', 'impact', v.v.
        pg.font.init()
        self.font_name = font_name
        self.fonts = {}
        self.texture_cache = {} # Lưu cache texture để tối ưu hiệu suất

    def get_font(self, size):
        if size not in self.fonts:
            try:
                # Dùng font hệ thống
                self.fonts[size] = pg.font.SysFont(self.font_name, size, bold=True)
            except:
                # Nếu không tìm thấy, dùng font mặc định của Pygame
                self.fonts[size] = pg.font.Font(None, size)
        return self.fonts[size]

    def _get_text_texture(self, text, size, color):
        key = (text, size, color)
        if key in self.texture_cache:
            return self.texture_cache[key]
            
        font = self.get_font(size)
        # Render text lên surface Pygame (với Anti-aliasing = True)
        surface = font.render(text, True, color)
        width, height = surface.get_size()
        
        # Chuyển đổi dữ liệu ảnh để nạp vào OpenGL
        data = pg.image.tostring(surface, "RGBA", True)
        
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        
        self.texture_cache[key] = (texture_id, width, height)
        return texture_id, width, height

    def draw_text(self, text, x, y, size=30, color=(255, 255, 255), center_x=False, center_y=False):
        texture_id, width, height = self._get_text_texture(str(text), size, color)
        
        # Nếu muốn căn giữa thì dịch chuyển x
        if center_x:
            x = x - width / 2
            
        # Nếu muốn căn giữa y thì dịch chuyển y
        if center_y:
            y = y - height / 2
            
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glColor3f(1.0, 1.0, 1.0) # Tránh bị ám màu từ các lệnh vẽ trước
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x, y)
        glTexCoord2f(1, 0); glVertex2f(x + width, y)
        glTexCoord2f(1, 1); glVertex2f(x + width, y + height)
        glTexCoord2f(0, 1); glVertex2f(x, y + height)
        glEnd()
        
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)