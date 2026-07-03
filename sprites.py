import math

import pygame

from constants import PIXELS_PER_METER


class SpriteCache:
    def __init__(self):
        self._cache = {}

    def _make_key(self, name, *args):
        return (name,) + args

    def get(self, name, *args, factory=None):
        key = self._make_key(name, *args)
        surf = self._cache.get(key)
        if surf is None and factory is not None:
            surf = factory(*args)
            self._cache[key] = surf
        return surf

    def clear(self):
        self._cache.clear()


_sprite_cache = SpriteCache()


def _build_car_body(width, height, color=(200, 50, 50), dark_color=(140, 30, 30)):
    pw = max(1, int(width * PIXELS_PER_METER))
    ph = max(1, int(height * PIXELS_PER_METER))
    surf = pygame.Surface((pw, ph), pygame.SRCALPHA)

    body_rect = pygame.Rect(0, int(ph * 0.3), pw, int(ph * 0.7))
    pygame.draw.ellipse(surf, color, body_rect)
    pygame.draw.ellipse(surf, dark_color, body_rect, 2)

    cab_rect = pygame.Rect(int(pw * 0.55), int(ph * 0.0), int(pw * 0.35), int(ph * 0.7))
    pygame.draw.ellipse(surf, (70, 70, 100), cab_rect)
    pygame.draw.ellipse(surf, (50, 50, 80), cab_rect, 2)

    windshield_rect = pygame.Rect(int(pw * 0.6), int(ph * 0.08), int(pw * 0.25), int(ph * 0.45))
    pygame.draw.ellipse(surf, (140, 170, 220), windshield_rect)
    pygame.draw.ellipse(surf, (100, 130, 180), windshield_rect, 1)

    pygame.draw.circle(surf, (255, 230, 100), (int(pw * 0.92), int(ph * 0.55)), max(1, int(pw * 0.06)))
    pygame.draw.circle(surf, (200, 180, 50), (int(pw * 0.92), int(ph * 0.55)), max(1, int(pw * 0.03)))

    return surf


def _build_wheel(radius, color=(50, 50, 50)):
    pr = max(1, int(radius * PIXELS_PER_METER))
    d = pr * 2
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    center = (pr, pr)

    pygame.draw.circle(surf, color, center, pr)
    pygame.draw.circle(surf, (80, 80, 80), center, int(pr * 0.75))
    pygame.draw.circle(surf, (60, 60, 60), center, int(pr * 0.15))

    for i in range(5):
        a = i * math.pi * 2 / 5
        inner = int(pr * 0.2)
        outer = int(pr * 0.7)
        sx = center[0] + int(math.cos(a) * inner)
        sy = center[1] + int(math.sin(a) * inner)
        ex = center[0] + int(math.cos(a) * outer)
        ey = center[1] + int(math.sin(a) * outer)
        pygame.draw.line(surf, (70, 70, 70), (sx, sy), (ex, ey), max(1, int(pr * 0.08)))

    return surf


def _build_coin_sprite(radius):
    pr = max(1, int(radius * PIXELS_PER_METER))
    d = pr * 2 + 4
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    center = (d // 2, d // 2)

    pygame.draw.circle(surf, (255, 215, 0), center, pr)
    pygame.draw.circle(surf, (200, 170, 0), center, pr, 2)
    pygame.draw.circle(surf, (255, 240, 100), (center[0] - int(pr * 0.2), center[1] - int(pr * 0.2)), int(pr * 0.4))
    pygame.draw.circle(surf, (255, 255, 150), (center[0] - int(pr * 0.15), center[1] - int(pr * 0.15)), int(pr * 0.2))

    return surf


def _build_fuel_sprite(radius):
    pr = max(1, int(radius * PIXELS_PER_METER))
    d = int(pr * 2.5)
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    cx, cy = d // 2, d // 2
    hw = max(1, int(pr * 0.7))
    hh = max(1, int(pr * 0.9))

    can_rect = pygame.Rect(cx - hw, cy - hh, hw * 2, hh * 2)
    pygame.draw.ellipse(surf, (0, 150, 60), can_rect)
    pygame.draw.ellipse(surf, (0, 100, 40), can_rect, 2)

    neck_rect = pygame.Rect(cx - int(hw * 0.3), cy - hh - int(pr * 0.3), int(hw * 0.6), int(pr * 0.4))
    pygame.draw.rect(surf, (0, 130, 50), neck_rect)
    pygame.draw.rect(surf, (0, 80, 30), neck_rect, 1)

    fill_rect = pygame.Rect(cx - int(hw * 0.5), cy - int(hh * 0.4), int(hw), int(hh * 0.5))
    pygame.draw.rect(surf, (0, 220, 100), fill_rect)

    return surf


def _build_terrain_tile(width, height, base_color, grass_color):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for x in range(width):
        for y in range(height):
            n = (math.sin(x * 0.3) * math.cos(y * 0.5) + math.sin(x * 0.7 + y * 0.9) * 0.5) * 0.5 + 0.5
            r = int(base_color[0] * (0.85 + n * 0.15))
            g = int(base_color[1] * (0.85 + n * 0.15))
            b = int(base_color[2] * (0.85 + n * 0.15))
            surf.set_at((x, y), (min(255, r), min(255, g), min(255, b)))
    grass_h = max(1, height // 6)
    for x in range(width):
        for y in range(grass_h):
            gh = (math.sin(x * 0.5 + y * 1.2) + 1) * 0.5
            r = int(grass_color[0] * (0.7 + gh * 0.3))
            g = int(grass_color[1] * (0.7 + gh * 0.3))
            b = int(grass_color[2] * (0.7 + gh * 0.3))
            surf.set_at((x, y), (min(255, r), min(255, g), min(255, b)))
    return surf


def get_car_body(vehicle_def):
    return _sprite_cache.get("car_body", vehicle_def.chassis_width, vehicle_def.chassis_height,
                             factory=lambda w, h: _build_car_body(w, h))


def get_wheel(radius):
    return _sprite_cache.get("wheel", radius, factory=_build_wheel)


def get_coin_sprite():
    return _sprite_cache.get("coin", factory=lambda: _build_coin_sprite(0.2))


def get_fuel_sprite():
    return _sprite_cache.get("fuel", factory=lambda: _build_fuel_sprite(0.25))


def get_terrain_tile(stage_def):
    key = ("terrain_tile", stage_def.id)
    return _sprite_cache.get(*key, factory=lambda: _build_terrain_tile(64, 64, stage_def.terrain_color, stage_def.grass_color))


def clear_cache():
    _sprite_cache.clear()
