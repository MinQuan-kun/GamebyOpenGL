# utils/animation.py

class Animation:
    def __init__(self, frames, speed=6, loop=True):
        self.frames = frames
        self.speed = max(1, int(speed))
        self.loop = loop

        self.timer = 0
        self.frame_index = 0
        self.finished = False

    def reset(self):
        self.timer = 0
        self.frame_index = 0
        self.finished = False

    def update(self):
        if self.finished:
            return

        self.timer += 1

        if self.timer >= self.speed:
            self.timer = 0
            self.frame_index += 1

            if self.frame_index >= len(self.frames):
                if self.loop:
                    self.frame_index = 0
                else:
                    self.frame_index = len(self.frames) - 1
                    self.finished = True

    def get_frame(self):
        if not self.frames:
            return 0

        return self.frames[self.frame_index]