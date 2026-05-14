import PIL.Image as Image
from OpenGL.GL import *

class TextureLoader:
    @staticmethod
    def load_texture(path):
        img = Image.open(path).transpose(Image.FLIP_TOP_BOTTOM)
        img_data = img.convert("RGBA").tobytes()
        
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        # GL_NEAREST giúp Pixel Art không bị mờ khi phóng to
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        
        # Nạp dữ liệu vào GPU
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 
                     0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        
        return texture_id, img.width, img.height