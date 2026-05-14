# Cấu hình màn hình
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
GROUND_Y_AREA_A = 128 # Nâng cao lên một chút để thấy đất sâu hơn

# Thông số vật lý
GRAVITY = 0.8
JUMP_FORCE = 15
PLAYER_SPEED = 5.0

# Thông số nhân vật
PLAYER_WIDTH = 64
PLAYER_HEIGHT = 64

# Thông số kẻ thù
ENEMY_SPEED = 2.0
ENEMY_WIDTH = 50
ENEMY_HEIGHT = 50

# Thông số Map
TILE_SIZE = 64
# Tạo map dài 100 cột
_row_sky = [0] * 100
_row_ground = [1] * 100
_row_dirt = [5] * 100
_row_deep_dirt = [9] * 100

GAME_MAP_A = [
    _row_sky[:], # Row 0
    _row_sky[:], # Row 1
    _row_sky[:], # Row 2
    [0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,1,1,1,0,0] + [0]*80, # Row 3 (Bục)
    [0,0,0,0,0,5,5,5,0,0,0,1,1,1,0,5,5,5,0,0] + [0]*80, # Row 4 (Bục)
    _row_ground, # Row 5 (Mặt đất)
    _row_dirt,   # Row 6
    _row_deep_dirt, # Row 7
]
GAME_MAP = GAME_MAP_A
