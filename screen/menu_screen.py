import math

import pygame

import assets
from constants import SCREEN_HEIGHT, SCREEN_WIDTH


class MenuScreen:
    def __init__(self, game):
        self.game = game
        self.font_large = assets.get_font(48)
        self.font_medium = assets.get_font(28)
        self.font_small = assets.get_font(18)
        self.menu_items = ["PLAY", "GARAGE", "SETTINGS", "QUIT"]
        self.selected_index = 0
        self.time = 0
        self.button_rects = []
        self.game.sound_manager.play_music()
        cx = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 + 20
        spacing = 75
        for i, item in enumerate(self.menu_items):
            text = self.font_medium.render(item, True, (255, 255, 255))
            bw = max(280, text.get_width() + 60)
            bh = 50
            bx = cx - bw // 2
            by = start_y + i * spacing
            self.button_rects.append(pygame.Rect(bx, by, bw, bh))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
                self.game.sound_manager.play_sfx("click")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                self.game.sound_manager.play_sfx("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select_item(self.selected_index)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self._select_item(i)
                    break

    def _select_item(self, index):
        if index == 0:
            self.game.set_screen("stage_select")
        elif index == 1:
            self.game.set_screen("garage")
        elif index == 2:
            self.game.set_screen("settings")
        elif index == 3:
            self.game.running = False
        self.game.sound_manager.play_sfx("click")

    def update(self, dt):
        self.time += dt

    def render(self, surface):
        surface.fill((0, 0, 0))
        self._draw_sky(surface)
        self._draw_sun(surface)
        self._draw_mountains(surface)
        self._draw_title(surface)
        self._draw_buttons(surface)

    def _draw_sky(self, surface):
        for i in range(20):
            t = i / 20
            r = int((0.15 + 0.4 * (1 - t)) * 255)
            g = int((0.2 + 0.55 * (1 - t)) * 255)
            b = int((0.4 + 0.5 * (1 - t)) * 255)
            y0 = int(i * SCREEN_HEIGHT / 20)
            y1 = int((i + 1) * SCREEN_HEIGHT / 20 + 1)
            pygame.draw.rect(surface, (r, g, b), (0, y0, SCREEN_WIDTH, y1 - y0))

    def _draw_sun(self, surface):
        cx = SCREEN_WIDTH // 2 + 100
        cy = SCREEN_HEIGHT // 4
        for i in range(6, -1, -1):
            alpha = 20 + 10 * (6 - i)
            color = (255, 204, 51, alpha)
            s = pygame.Surface((100 + i * 15, 100 + i * 15), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (s.get_width() // 2, s.get_height() // 2), 40 + i * 8)
            surface.blit(s, (cx - s.get_width() // 2, cy - s.get_height() // 2))
        pygame.draw.circle(surface, (255, 230, 77), (cx, cy), 40)

    def _draw_mountains(self, surface):
        base_y = SCREEN_HEIGHT - 180
        mountains = [
            ([4, 4.5, 5, 6, 5.5, 4], 360, 0.6),
            ([7, 8, 7.5, 9, 8, 6, 5], 540, 0.5),
            ([3, 5, 4, 6, 5, 3.5], 420, 0.4),
        ]
        for heights, width, scale in mountains:
            seg_w = width / (len(heights) - 1)
            points = []
            for i, h in enumerate(heights):
                x = int(SCREEN_WIDTH // 2 - width // 2 + i * seg_w)
                y = int(base_y - h * 20 * scale)
                points.append((x, y))
            points.append((points[-1][0], base_y + 50))
            points.append((points[0][0], base_y + 50))
            color = (int(64 * scale), int(77 * scale), int(56 * scale))
            pygame.draw.polygon(surface, color, points)

        ground_color = (64, 102, 38)
        pygame.draw.rect(surface, ground_color, (0, base_y, SCREEN_WIDTH, 50))
        dark_ground = (38, 64, 26)
        pygame.draw.rect(surface, dark_ground, (0, base_y + 50, SCREEN_WIDTH, 50))
        darker_ground = (26, 38, 20)
        pygame.draw.rect(surface, darker_ground, (0, base_y + 100, SCREEN_WIDTH, 80))

        for i in range(30):
            bx = i * (SCREEN_WIDTH / 30)
            bh = 8 + 4 * math.sin(i * 1.7 + self.time * 0.5)
            pygame.draw.line(surface, (51, 128, 26), (bx, base_y), (bx + 2, base_y - bh), 4)

    def _draw_title(self, surface):
        text = self.font_large.render("HILL CLIMB", True, (230, 38, 38))
        shadow = self.font_large.render("HILL CLIMB", True, (0, 0, 0, 128))
        cx = SCREEN_WIDTH // 2
        ty = SCREEN_HEIGHT // 2 - 140
        surface.blit(shadow, (cx - text.get_width() // 2 + 3, ty + 2))
        surface.blit(text, (cx - text.get_width() // 2, ty))

    def _draw_buttons(self, surface):
        for i, item in enumerate(self.menu_items):
            rect = self.button_rects[i]
            if i == self.selected_index:
                pulse = 1 + 0.06 * math.sin(self.time * 3)
                color = (int(217 * pulse), int(64 * pulse), int(38 * pulse))
                pygame.draw.rect(surface, color, rect, border_radius=4)
                pygame.draw.rect(surface, (255, 128, 77), rect, 2, border_radius=4)
            else:
                pygame.draw.rect(surface, (38, 38, 46), rect, border_radius=4)
            color = (255, 255, 255) if i == self.selected_index else (179, 179, 179)
            text = self.font_medium.render(item, True, color)
            tx = rect.x + (rect.width - text.get_width()) // 2
            ty = rect.y + (rect.height - text.get_height()) // 2
            surface.blit(text, (tx, ty))
