from OpenGL.GL import *

class FontRenderer:
    SEGMENTS = {
        'a': (0, 1, 0.5, 1),   # Ngang trên
        'b': (0.5, 1, 0.5, 0.5), # Dọc trên phải
        'c': (0.5, 0.5, 0.5, 0), # Dọc dưới phải
        'd': (0, 0, 0.5, 0),   # Ngang dưới
        'e': (0, 0, 0, 0.5), # Dọc dưới trái
        'f': (0, 0.5, 0, 1), # Dọc trên trái
        'g': (0, 0.5, 0.5, 0.5) # Ngang giữa
    }

    # Chữ số nào thì dùng những đoạn nào
    DIGITS = {
        '0': 'abcdef',
        '1': 'bc',
        '2': 'abged',
        '3': 'abgcd',
        '4': 'fgbc',
        '5': 'afgcd',
        '6': 'afedcg',
        '7': 'abc',
        '8': 'abcdefg',
        '9': 'abcdfg'
    }

    @staticmethod
    def draw_digit(digit, x, y, size):
        """Vẽ một chữ số đơn lẻ tại vị trí (x, y) với kích thước size"""
        if digit not in FontRenderer.DIGITS: return
        
        segments_to_draw = FontRenderer.DIGITS[digit]
        
        glPushMatrix()
        glTranslatef(x, y, 0)
        glScalef(size, size, 1)
        
        glBegin(GL_LINES)
        for seg_key in segments_to_draw:
            coords = FontRenderer.SEGMENTS[seg_key]
            glVertex2f(coords[0], coords[1])
            glVertex2f(coords[2], coords[3])
        glEnd()
        
        glPopMatrix()

    @staticmethod
    def draw_number(number, x, y, size, spacing=0.05):
        str_num = str(number)
        current_x = x
        for char in str_num:
            FontRenderer.draw_digit(char, current_x, y, size)
            current_x += size + spacing