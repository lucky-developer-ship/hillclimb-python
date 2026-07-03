import pygame

import assets
from constants import SCREEN_HEIGHT, SCREEN_WIDTH


class SettingsScreen:
    def __init__(self, game):
        self.game = game
        self.font = assets.get_font(22)
        self.font_small = assets.get_font(18)
        self.font_title = assets.get_font(32)
        self.selected_index = 0
        self.items = ["Music Volume", "SFX Volume", "BACK"]
        self.item_rects = []
        w = SCREEN_WIDTH
        h = SCREEN_HEIGHT
        cx = w // 2
        start_y = h // 2 - 80
        for i, item in enumerate(self.items):
            self.item_rects.append(pygame.Rect(cx - 150, start_y + i * 70, 300, 50))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.items)
                self.game.sound_manager.play_sfx("click")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.items)
                self.game.sound_manager.play_sfx("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select(self.selected_index)
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_q):
                self.game.set_screen("menu")
            elif event.key == pygame.K_LEFT:
                self._adjust(-0.1, self.selected_index)
            elif event.key == pygame.K_RIGHT:
                self._adjust(0.1, self.selected_index)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.item_rects):
                if rect.collidepoint(event.pos):
                    self._select(i)
                    break

    def _adjust(self, delta, index):
        sd = self.game.save_data
        if index == 0:
            sd.settings["music_volume"] = max(0, min(1, sd.settings["music_volume"] + delta))
            self.game.sound_manager.set_volumes(sd.settings["music_volume"], sd.settings["sfx_volume"])
            self.game.sound_manager.update_music_volume()
        elif index == 1:
            sd.settings["sfx_volume"] = max(0, min(1, sd.settings["sfx_volume"] + delta))
            self.game.sound_manager.set_volumes(sd.settings["music_volume"], sd.settings["sfx_volume"])
        sd.save()

    def _select(self, index):
        if index == 2:
            self.game.set_screen("menu")

    def update(self, dt):
        pass

    def render(self, surface):
        surface.fill((20, 20, 26))
        w, h = surface.get_size()
        cx = w // 2

        title = self.font_title.render("SETTINGS", True, (200, 200, 220))
        surface.blit(title, (cx - title.get_width() // 2, 40))

        sd = self.game.save_data
        volumes = [sd.settings["music_volume"], sd.settings["sfx_volume"]]

        for i, item in enumerate(self.items):
            rect = self.item_rects[i]
            if i == self.selected_index:
                pygame.draw.rect(surface, (60, 60, 80), rect, border_radius=4)
                pygame.draw.rect(surface, (100, 100, 150), rect, 2, border_radius=4)
            else:
                pygame.draw.rect(surface, (35, 35, 45), rect, border_radius=4)

            if i < 2:
                label = self.font_small.render(item, True, (200, 200, 200))
                surface.blit(label, (rect.x + 10, rect.y + 8))
                bar_x = rect.x + 140
                bar_y = rect.y + 15
                bar_w = 120
                bar_h = 18
                pygame.draw.rect(surface, (50, 50, 60), (bar_x, bar_y, bar_w, bar_h))
                fw = int(bar_w * volumes[i])
                pygame.draw.rect(surface, (80, 180, 80), (bar_x, bar_y, fw, bar_h))
                pct = self.font_small.render(f"{int(volumes[i] * 100)}%", True, (200, 200, 200))
                surface.blit(pct, (bar_x + bar_w + 10, bar_y - 2))
            else:
                label = self.font.render(item, True, (200, 200, 200))
                surface.blit(label, (cx - label.get_width() // 2, rect.y + 8))
