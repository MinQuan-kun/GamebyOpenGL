from OpenGL.GL import *
from utils.constants import TILE_SIZE

class Ground:
    def __init__(self, map_data, renderer):
        self.map_data = map_data
        self.renderer = renderer
        self.map_cols = len(map_data[0])
        self.map_rows = len(map_data)

    def draw(self, camera_x):
        # Chỉ vẽ các tiles nằm trong tầm nhìn của Camera để tối ưu hiệu năng
        start_col = max(0, int(camera_x // TILE_SIZE))
        end_col = min(self.map_cols, int((camera_x + 1280) // TILE_SIZE) + 1)

        for r in range(self.map_rows):
            for c in range(start_col, end_col):
                tile_id = self.map_data[r][c]
                if tile_id != 0:
                    # Tọa độ vẽ = Tọa độ thế giới - Tọa độ Camera
                    draw_x = c * TILE_SIZE - camera_x
                    draw_y = (self.map_rows - 1 - r) * TILE_SIZE
                    self.renderer.draw(draw_x, draw_y, TILE_SIZE, TILE_SIZE, tile_id)
