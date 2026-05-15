import pygame as pg
from OpenGL.GL import *
import os

class SpriteFontRenderer:
    def __init__(self, image_path, cols=13, rows=8, top_offset_ratio=0.0):
        self.texture_id = self.load_texture(image_path)
        self.cols = cols
        self.rows = rows
        self.top_offset_ratio = top_offset_ratio # Dùng để bỏ qua phần tiêu đề (nếu có)
        
        self.char_map = {}
        # Bảng chữ cái tương ứng với lưới 13 cột x 8 hàng
        layout = [
            "ABCDEFGHIJKLM",
            "NOPQRSTUVWXYZ",
            "abcdefghijklm",
            "nopqrstuvwxyz",
            "1234567890   ",
            "1234567890   ",
            "?!.,:;\"()'   ",
            "/%-+={<>@#_  "
        ]
        
        for r, row_str in enumerate(layout):
            for c, char in enumerate(row_str):
                if char != ' ':
                    self.char_map[char] = (c, r)

    def load_texture(self, path):
        if not os.path.exists(path):
            print(f"WARNING: Không tìm thấy font tại {path}!")
            return 0
            
        surface = pg.image.load(path).convert_alpha()
        
        # Chọn màu ở góc (0,0) làm màu nền và biến thành trong suốt
        bg_color = surface.get_at((0, 0))
        surface.set_colorkey(bg_color)
        
        width, height = surface.get_size()
        data = pg.image.tostring(surface, "RGBA", True)
        
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        return texture_id

    def draw_text(self, text, x, y, size, spacing=2):
        if self.texture_id == 0:
            return
            
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Kích thước một ô chữ (UV)
        u_step = 1.0 / self.cols
        v_step = (1.0 - self.top_offset_ratio) / self.rows
        
        current_x = x
        for char in text:
            if char == ' ':
                current_x += size * 0.5
                continue
                
            if char in self.char_map:
                col, row = self.char_map[char]
                
                u = col * u_step
                # Tính v từ dưới lên do tostring lật ảnh
                v = 1.0 - self.top_offset_ratio - (row + 1) * v_step
                
                # Điều chỉnh một chút offset để tránh lem màu viền (nếu có)
                eps = 0.005 
                
                glBegin(GL_QUADS)
                glTexCoord2f(u + eps, v + eps);                     glVertex2f(current_x, y)
                glTexCoord2f(u + u_step - eps, v + eps);            glVertex2f(current_x + size, y)
                glTexCoord2f(u + u_step - eps, v + v_step - eps);   glVertex2f(current_x + size, y + size)
                glTexCoord2f(u + eps, v + v_step - eps);            glVertex2f(current_x, y + size)
                glEnd()
                
            current_x += size + spacing
            
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
