from utils.constants import GRAVITY, APEX_THRESHOLD, AIR_RESISTANCE, TIME_STEP, GROUND_Y

class Physics:
    @staticmethod
    def calculate_jump_velocity(mass, jump_force):
        res = abs(jump_force) / mass
        if res == 1 :
            return 0
        return jump_force / mass

    @staticmethod
    def apply_gravity(velocity, is_jumping):
        if is_jumping and abs(velocity) < APEX_THRESHOLD:
            return velocity + (GRAVITY * 0.3) * TIME_STEP
        return velocity + GRAVITY * TIME_STEP

    @staticmethod
    def apply_air_resistance(velocity):
        return velocity * (1 - AIR_RESISTANCE * TIME_STEP)

    @staticmethod
    def check_ground_collision(y_position):
        if y_position <= GROUND_Y:
            return GROUND_Y, True
        return y_position, False

    @staticmethod
    def get_next_state(y, velocity, is_jumping, dt):
        # 1. Tính vận tốc mới
        v_next = Physics.apply_gravity(velocity, is_jumping)
        v_next = Physics.apply_air_resistance(v_next)
        
        # 2. Tính vị trí y mới (y = y - v * dt)
        y_next = y - v_next * dt
        
        # 3. Kiểm tra va chạm sàn
        y_final, grounded = Physics.check_ground_collision(y_next)
        
        # Reset vận tốc nếu đã chạm sàn
        v_final = 0 if grounded else v_next
        
        return y_final, v_final, grounded