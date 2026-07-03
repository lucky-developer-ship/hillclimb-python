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
        self.items = ["Music Volume", "SFX Volume", "MUTE ALL", "RESET SAVE DATA", "BACK"]
        self.confirming_reset = False
        self.item_rects = []
        w = SCREEN_WIDTH
        h = SCREEN_HEIGHT
        cx = w // 2
        start_y = h // 2 - 140
        for i, item in enumerate(self.items):
            self.item_rects.append(pygame.Rect(cx - 150, start_y + i * 65, 300, 50))

    def handle_event(self, event):
        if self.confirming_reset and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_q):
                self.confirming_reset = False
            elif event.key == pygame.K_LEFT:
                self.confirm_choice = 0
            elif event.key == pygame.K_RIGHT:
                self.confirm_choice = 1
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if getattr(self, "confirm_choice", 0) == 0:
                    self._do_reset()
                self.confirming_reset = False
            return

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
            self.game.sound_manager.toggle_mute()
            self.game.sound_manager.play_sfx("click")
        elif index == 3:
            self.confirming_reset = True
            self.confirm_choice = 0
        elif index == 4:
            self.game.set_screen("menu")

    def _do_reset(self):
        sd = self.game.save_data
        sd.total_coins = 0
        sd.selected_vehicle_id = "jeep"
        sd.unlocked_vehicles = [True, False, False]
        sd.unlocked_stages = [True, False, False]
        sd.upgrade_levels = {}
        sd.settings = {"music_volume": 0.5, "sfx_volume": 0.7}
        sd.best_distances = {}
        sd.trophies = 0
        sd.last_daily_date = ""
        sd.save()
        self.game.sound_manager.set_volumes(0.5, 0.7)
        self.game.sound_manager.muted = False

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
        sm = self.game.sound_manager

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
            elif i == 2:
                label = self.font_small.render(item, True, (200, 200, 200))
                surface.blit(label, (rect.x + 10, rect.y + 8))
                state = "ON" if sm.muted else "OFF"
                state_color = (255, 80, 80) if sm.muted else (80, 200, 80)
                state_text = self.font_small.render(state, True, state_color)
                surface.blit(state_text, (rect.x + rect.width - state_text.get_width() - 15, rect.y + 8))
            elif i == 3:
                label_text = "RESET ALL DATA" if not self.confirming_reset else "ARE YOU SURE?"
                label = self.font_small.render(label_text, True, (220, 100, 100) if not self.confirming_reset else (255, 200, 100))
                surface.blit(label, (cx - label.get_width() // 2, rect.y + 8))
            else:
                label = self.font.render(item, True, (200, 200, 200))
                surface.blit(label, (cx - label.get_width() // 2, rect.y + 8))

        if self.confirming_reset:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            msg = self.font.render("Reset all progress? This cannot be undone!", True, (255, 255, 255))
            surface.blit(msg, (cx - msg.get_width() // 2, h // 2 - 60))
            for ci, label in enumerate(["YES", "NO"]):
                c = (255, 255, 255) if ci == getattr(self, "confirm_choice", 0) else (150, 150, 150)
                opt = self.font_small.render(label, True, c)
                ox = cx - 40 + ci * 80
                surface.blit(opt, (ox, h // 2))
