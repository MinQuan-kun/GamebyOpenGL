from OpenGL.GL import *
from utils.texture_loader import TextureLoader
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class TextRenderer:
    def __init__(self, texture_path):
        self.tex_id, self.w, self.h = TextureLoader.load_texture(texture_path)
        # Ảnh OCR-A-Extended.png của Quân có 13 cột và 6 hàng
        self.cols = 13
        self.rows = 6
        # Tính tỉ lệ màn hình để chống méo chữ (1200x600 -> ratio = 0.5)
        self.aspect_ratio = SCREEN_HEIGHT / SCREEN_WIDTH 

    def draw_text(self, text, x, y, size):
        # BẢNG MÃ CHUẨN: Khớp chính xác với vị trí các chữ trong ảnh của bạn
        CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*() "
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.tex_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBegin(GL_QUADS)
        current_x = x
        for char in text:
            if char == " ": # Nếu là dấu cách, chỉ di chuyển vị trí vẽ tiếp theo
                current_x += size * 0.4 * self.aspect_ratio
                continue
                
            index = CHARS.find(char)
            if index == -1: continue # Bỏ qua ký tự không có trong ảnh
            
            # Tính tọa độ hàng/cột trong lưới 13 cột
            c = index % self.cols
            r = index // self.cols
            
            # Tính tọa độ Texture (UV)
            u = c / self.cols
            v = 1.0 - (r / self.rows)
            u_step = 1.0 / self.cols
            v_step = 1.0 / self.rows

            # Chiều ngang chữ cần nhân với aspect_ratio để không bị "béo"
            char_width = size * self.aspect_ratio
            
            glTexCoord2f(u, v - v_step);          glVertex2f(current_x, y)
            glTexCoord2f(u + u_step, v - v_step); glVertex2f(current_x + char_width, y)
            glTexCoord2f(u + u_step, v);          glVertex2f(current_x + char_width, y + size)
            glTexCoord2f(u, v);                   glVertex2f(current_x, y + size)
            
            # Khoảng cách giữa các chữ (Kerning)
            current_x += char_width * 0.8 
            
        glEnd()
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)