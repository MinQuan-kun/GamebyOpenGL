from OpenGL.GL import *

class SpriteRenderer:
    def __init__(self, texture_id, rows, cols):
        self.texture_id = texture_id
        self.rows = rows
        self.cols = cols
        self.u_step = 1.0 / cols
        self.v_step = 1.0 / rows

    def draw(self, x, y, width, height, frame_index, flip_x=False):
        # Tính toán tọa độ UV từ index
        col = frame_index % self.cols
        row = (self.rows - 1) - (frame_index // self.cols) # Lật Y vì OpenGL

        u = col * self.u_step
        v = row * self.v_step

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        u_start, u_end = u, u + self.u_step
        if flip_x: u_start, u_end = u_end, u_start

        glBegin(GL_QUADS)
        glTexCoord2f(u_start, v);          glVertex2f(x, y)
        glTexCoord2f(u_end, v);            glVertex2f(x + width, y)
        glTexCoord2f(u_end, v + self.v_step); glVertex2f(x + width, y + height)
        glTexCoord2f(u_start, v + self.v_step); glVertex2f(x, y + height)
        glEnd()

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)