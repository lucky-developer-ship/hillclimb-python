import math
import random

import pygame

from constants import PIXELS_PER_METER


class Particle:
    def __init__(self, x, y, vx, vy, life, color, size, decay=1.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.decay = decay

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += -5 * dt
        self.life -= dt * self.decay

    def is_dead(self):
        return self.life <= 0

    def get_alpha(self):
        return max(0, min(1, self.life / self.max_life))


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self._circle_cache = {}

    def _get_circle_surface(self, color, size):
        # Small, bounded cache: only a handful of distinct (color, size)
        # combos ever get requested by the emit_* methods below, so this
        # builds each one once and reuses it for the rest of the game
        # instead of allocating+painting a new Surface every frame.
        size_key = max(1, round(size))
        key = (color, size_key)
        surf = self._circle_cache.get(key)
        if surf is None:
            diameter = size_key * 2
            surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, 255), (size_key, size_key), size_key)
            self._circle_cache[key] = surf
        return surf

    def emit(self, x, y, count, color, speed=2, size=3, life=0.5, spread=1.0, decay=1.0):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(0.5, speed)
            vx = math.cos(angle) * spd * spread
            vy = math.sin(angle) * spd * spread - random.uniform(0, 1)
            self.particles.append(
                Particle(x, y, vx, vy, random.uniform(life * 0.5, life), color, random.uniform(size * 0.5, size), decay)
            )

    def emit_exhaust(self, x, y, speed=0.8):
        count = 2 if speed > 1.5 else 1
        self.emit(x, y, count, (150, 150, 150), speed, 3, 0.4, 0.3, 2.5)

    def emit_dust(self, x, y, speed=1.5, intensity=1.0):
        count = max(1, int(3 * intensity))
        self.emit(x, y, count, (120, 90, 60), speed * intensity, max(1, int(3 * intensity)), 0.5, 0.5 * intensity, 1.5)

    def emit_dirt_trail(self, x, y, speed, traction):
        if traction <= 0 or speed < 1:
            return
        intensity = min(1.0, speed * 0.05) * traction
        count = max(1, int(4 * intensity))
        self.emit(x, y, count, (100, 75, 45), speed * 0.3, max(1, int(3 * intensity)), 0.3, 0.6, 2.0)

    def emit_coin_sparkle(self, x, y):
        self.emit(x, y, 8, (255, 215, 0), 3, 3, 0.4, 1.0, 2)
        self.emit(x, y, 4, (255, 255, 200), 2, 2, 0.3, 0.8, 3)

    def emit_crash(self, x, y):
        self.emit(x, y, 15, (200, 100, 50), 4, 4, 0.6, 1.0, 1.5)
        self.emit(x, y, 8, (255, 200, 100), 3, 3, 0.4, 0.8, 2)

    def update(self, dt, camera_x, camera_y):
        for p in self.particles[:]:
            p.update(dt)
            if p.is_dead():
                self.particles.remove(p)

    def draw(self, surface, camera_x, camera_y):
        from constants import SCREEN_HEIGHT, SCREEN_WIDTH

        for p in self.particles:
            sx = int((p.x - camera_x) * PIXELS_PER_METER + SCREEN_WIDTH // 2)
            sy = int((p.y - camera_y) * PIXELS_PER_METER + SCREEN_HEIGHT // 2)
            alpha = int(p.get_alpha() * 255)
            circle_surf = self._get_circle_surface(p.color, p.size)
            circle_surf.set_alpha(alpha)
            surface.blit(circle_surf, (sx - circle_surf.get_width() // 2, sy - circle_surf.get_height() // 2))
