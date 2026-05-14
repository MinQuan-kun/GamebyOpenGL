from OpenGL.GL import *

class SpriteRenderer:
    def __init__(self, image_path_or_id, rows, cols):
        # Nếu truyền vào path (string), ta nạp texture. Nếu là int, đó là texture_id đã nạp.
        if isinstance(image_path_or_id, str):
            from utils.texture_loader import TextureLoader
            self.texture_id, self.w, self.h = TextureLoader.load_texture(image_path_or_id)
        else:
            self.texture_id = image_path_or_id
            self.w, self.h = 0, 0 # Nếu truyền ID trực tiếp thì không biết size gốc
            
        self.rows = rows
        self.cols = cols
        self.u_step = 1.0 / cols
        self.v_step = 1.0 / rows

    def draw(self, x, y, width, height, frame_index, flip_x=False):
        # Tính toán tọa độ UV từ index
        col = frame_index % self.cols
        row = (self.rows - 1) - (frame_index // self.cols) 

        u = col * self.u_step
        v = row * self.v_step

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        u_start, u_end = u, u + self.u_step
        if flip_x: u_start, u_end = u_end, u_start

        eps = 0.0
        
        glBegin(GL_QUADS)
        glTexCoord2f(u_start + eps, v + eps);                   glVertex2f(x, y)
        glTexCoord2f(u_end - eps, v + eps);                     glVertex2f(x + width, y)
        glTexCoord2f(u_end - eps, v + self.v_step - eps);       glVertex2f(x + width, y + height)
        glTexCoord2f(u_start + eps, v + self.v_step - eps);     glVertex2f(x, y + height)
        glEnd()

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)