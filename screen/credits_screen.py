import pygame

import assets
from constants import SCREEN_HEIGHT, SCREEN_WIDTH


class CreditsScreen:
    def __init__(self, game):
        self.game = game
        self.font_large = assets.get_font(32)
        self.font_medium = assets.get_font(20)
        self.font_small = assets.get_font(16)
        self.time = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE, pygame.K_q):
                self.game.set_screen("menu")

    def update(self, dt):
        self.time += dt

    def render(self, surface):
        surface.fill((10, 10, 15))
        w, h = surface.get_size()
        cx = w // 2

        title = self.font_large.render("HILL CLIMB RACING", True, (230, 38, 38))
        surface.blit(title, (cx - title.get_width() // 2, 60))

        subtitle = self.font_small.render("A Pygame / Pymunk Clone", True, (150, 150, 170))
        surface.blit(subtitle, (cx - subtitle.get_width() // 2, 105))

        lines = [
            "",
            "Created with Python, Pygame CE & Pymunk",
            "",
            "Physics Engine: Pymunk (Chipmunk2D)",
            "Graphics: Pygame CE",
            "Sound: Procedurally generated WAV",
            "",
            "Controls:",
            "  Arrow Keys / WASD - Drive & Lean",
            "  ESC - Pause  |  F11 - Fullscreen",
            "",
            "Inspired by Hill Climb Racing (Fingersoft)",
            "",
            "",
            "Press ESC or ENTER to return",
        ]
        y = 150
        for line in lines:
            if line == "":
                y += 12
                continue
            txt = self.font_small.render(line, True, (200, 200, 200))
            surface.blit(txt, (cx - txt.get_width() // 2, y))
            y += 28 if "Controls:" in line or "Inspired" in line else 24
