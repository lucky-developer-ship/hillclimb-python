
import pygame

from constants import SCREEN_HEIGHT, SCREEN_WIDTH


class ParallaxLayer:
    def __init__(self, surface, scroll_speed, y_offset=0):
        self.surface = surface
        self.scroll_speed = scroll_speed
        self.y_offset = y_offset
        self.width = surface.get_width()

    def draw(self, dest, camera_x, camera_y):
        offset = (-camera_x * self.scroll_speed) % self.width
        dest.blit(self.surface, (offset - self.width, self.y_offset))
        dest.blit(self.surface, (offset, self.y_offset))
        dest.blit(self.surface, (offset + self.width, self.y_offset))


class ParallaxBackground:
    def __init__(self, stage_def):
        self.layers = self._build_layers(stage_def)

    def _build_layers(self, stage_def):
        sky_bottom, sky_top = stage_def.sky_colors

        sky = pygame.Surface((SCREEN_WIDTH * 2, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int((sky_bottom[0] + (sky_top[0] - sky_bottom[0]) * (1 - t)) * 255)
            g = int((sky_bottom[1] + (sky_top[1] - sky_bottom[1]) * (1 - t)) * 255)
            b = int((sky_bottom[2] + (sky_top[2] - sky_bottom[2]) * (1 - t)) * 255)
            pygame.draw.line(sky, (r, g, b), (0, y), (SCREEN_WIDTH * 2 - 1, y))

        sun_cx = int(SCREEN_WIDTH * 0.3)
        sun_cy = int(SCREEN_HEIGHT * 0.2)
        for i in range(5, -1, -1):
            alpha = 15 + 10 * (5 - i)
            s = pygame.Surface((120 + i * 20, 120 + i * 20), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 200, 50, alpha), (s.get_width() // 2, s.get_height() // 2), 50 + i * 10)
            sky.blit(s, (sun_cx - s.get_width() // 2, sun_cy - s.get_height() // 2))
        pygame.draw.circle(sky, (255, 230, 80), (sun_cx, sun_cy), 45)

        return [
            ParallaxLayer(sky, 0.0, 0),
        ]

    def draw(self, dest, camera_x, camera_y):
        for layer in self.layers:
            layer.draw(dest, camera_x, camera_y)
