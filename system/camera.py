import math
import random


class GameCamera:
    def __init__(self):
        self.x = 0
        self.y = 5
        self.target_x = 0
        self.target_y = 5
        self.smooth_speed = 2.0
        self.look_ahead = 3.0
        self.shake_intensity = 0.0
        self.shake_duration = 0.0

    def reset(self, x=0, y=5):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.shake_intensity = 0.0
        self.shake_duration = 0.0

    def shake(self, intensity, duration):
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_duration = max(self.shake_duration, duration)

    def update(self, dt, target_body, target_vel_x):
        px = target_body.position.x
        py = target_body.position.y
        self.target_x = px + self.look_ahead * min(max(target_vel_x / 10, -1), 1)
        self.target_y = max(py + 2, 5)

        self.x += (self.target_x - self.x) * min(1, self.smooth_speed * dt * 3)
        self.y += (self.target_y - self.y) * min(1, self.smooth_speed * dt * 3)

        if self.shake_duration > 0:
            self.shake_duration -= dt
            angle = random.uniform(0, math.pi * 2)
            mag = self.shake_intensity * (self.shake_duration / max(self.shake_duration, dt))
            self.x += math.cos(angle) * mag
            self.y += math.sin(angle) * mag
        else:
            self.shake_intensity = 0.0
