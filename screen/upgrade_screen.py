import math

import pygame

import assets
from constants import SCREEN_WIDTH
from data.game_data import get_upgrades, get_vehicle


class UpgradeScreen:
    def __init__(self, game, vehicle_id):
        self.game = game
        self.vehicle_id = vehicle_id
        self.upgrades = get_upgrades(vehicle_id)
        self.font = assets.get_font(20)
        self.font_small = assets.get_font(16)
        self.selected_index = 0
        self.upgrade_rects = []
        cx = SCREEN_WIDTH // 2
        for i in range(len(self.upgrades)):
            self.upgrade_rects.append(pygame.Rect(cx - 200, 60 + i * 80, 400, 65))
        self.back_rect = pygame.Rect(cx - 60, 380, 120, 45)
        self.confirming = False
        self.confirm_choice = 0

    def handle_event(self, event):
        if self.confirming and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_q):
                self.confirming = False
                self.game.sound_manager.play_sfx("click")
            elif event.key == pygame.K_LEFT:
                self.confirm_choice = 0
                self.game.sound_manager.play_sfx("click")
            elif event.key == pygame.K_RIGHT:
                self.confirm_choice = 1
                self.game.sound_manager.play_sfx("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.confirm_choice == 0:
                    self._complete_purchase()
                self.confirming = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.upgrades)
                self.game.sound_manager.play_sfx("click")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.upgrades)
                self.game.sound_manager.play_sfx("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._purchase_upgrade()
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_q):
                self.game.set_screen("garage")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(event.pos):
                self.game.set_screen("garage")
                return
            for i, rect in enumerate(self.upgrade_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = i
                    self._purchase_upgrade()
                    break

    def _purchase_upgrade(self):
        u = self.upgrades[self.selected_index]
        level = self.game.save_data.get_upgrade_level(self.vehicle_id, u.id)
        if level < u.max_level:
            cost = u.costs[level]
            if self.game.save_data.get_coins() >= cost:
                self.confirming = True
                self.confirm_choice = 0
                self.game.sound_manager.play_sfx("click")

    def _complete_purchase(self):
        u = self.upgrades[self.selected_index]
        level = self.game.save_data.get_upgrade_level(self.vehicle_id, u.id)
        if level < u.max_level:
            cost = u.costs[level]
            if self.game.save_data.spend_coins(cost):
                self.game.save_data.set_upgrade_level(self.vehicle_id, u.id, level + 1)
                self.game.save_data.save()
                self.game.sound_manager.play_sfx("buy")

    def update(self, dt):
        if not self.confirming:
            self.time = getattr(self, "time", 0) + dt

    def _draw_vehicle_preview(self, surface, x, y, v_def, angle=0):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        hw = v_def.chassis_width * 8
        hh = v_def.chassis_height * 8
        verts = []
        for lx, ly in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
            rx = lx * cos_a - ly * sin_a
            ry = lx * sin_a + ly * cos_a
            verts.append((int(x + rx), int(y + ry)))
        if len(verts) == 4:
            pygame.draw.polygon(surface, (200, 50, 50), [verts[0], verts[1], verts[2]])
            pygame.draw.polygon(surface, (200, 50, 50), [verts[0], verts[2], verts[3]])
        wr = int(v_def.wheel_radius * 8)
        pygame.draw.circle(surface, (60, 60, 60), (x - int(v_def.wheel_base * 4), y + int(hh * 2)), wr)
        pygame.draw.circle(surface, (60, 60, 60), (x + int(v_def.wheel_base * 4), y + int(hh * 2)), wr)

    def render(self, surface):
        surface.fill((26, 26, 33))
        w, h = surface.get_size()
        cx = w // 2

        pygame.draw.rect(surface, (31, 31, 46), (0, 0, w, 50))
        v = get_vehicle(self.vehicle_id)
        title = self.font.render(f"{v.name} UPGRADES", True, (255, 255, 255))
        surface.blit(title, (cx - title.get_width() // 2, 12))

        preview_angle = 0.06 * math.sin(getattr(self, "time", 0) * 1.5)
        self._draw_vehicle_preview(surface, cx - 80, 35, v, preview_angle)

        for i, u in enumerate(self.upgrades):
            rect = self.upgrade_rects[i]
            level = self.game.save_data.get_upgrade_level(self.vehicle_id, u.id)
            maxed = level >= u.max_level
            if i == self.selected_index:
                bg = (64, 115, 64)
            elif maxed:
                bg = (51, 56, 38)
            else:
                bg = (41, 46, 56)
            pygame.draw.rect(surface, bg, rect, border_radius=4)
            if i == self.selected_index:
                pygame.draw.rect(surface, (77, 179, 77), rect, 2, border_radius=4)

            name = self.font.render(u.name, True, (255, 255, 255))
            surface.blit(name, (rect.x + 10, rect.y + 6))

            lvl = self.font_small.render(f"Lv.{level}/{u.max_level}", True, (153, 153, 179))
            surface.blit(lvl, (rect.x + 120, rect.y + 10))

            bar_w = 160
            bar_h = 14
            bar_x = rect.x + rect.width - bar_w - 50
            bar_y = rect.y + rect.height // 2 - bar_h // 2
            pygame.draw.rect(surface, (46, 46, 51), (bar_x, bar_y, bar_w, bar_h))
            fill = 1.0 if maxed else level / u.max_level
            fw = int(bar_w * fill)
            fc = (255, 204, 51) if maxed else (51, 179, 51)
            pygame.draw.rect(surface, fc, (bar_x, bar_y, fw, bar_h))

            if not maxed:
                cost = u.costs[level]
                cost_text = self.font_small.render(f"{cost}", True, (255, 204, 0))
                surface.blit(cost_text, (bar_x + bar_w + 10, bar_y - 2))
            else:
                max_text = self.font_small.render("MAXED", True, (0, 255, 77))
                surface.blit(max_text, (bar_x + bar_w + 10, bar_y - 2))

        pygame.draw.rect(surface, (102, 64, 64), self.back_rect, border_radius=4)
        back_text = self.font_small.render("BACK", True, (255, 255, 255))
        surface.blit(back_text, (self.back_rect.x + 40, self.back_rect.y + 10))

        coins_text = self.font_small.render(f"Coins: {self.game.save_data.get_coins()}", True, (255, 230, 0))
        surface.blit(coins_text, (w - coins_text.get_width() - 20, 15))

        if self.confirming:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            u = self.upgrades[self.selected_index]
            level = self.game.save_data.get_upgrade_level(self.vehicle_id, u.id)
            cost = u.costs[level]
            msg = self.font.render(f"Upgrade {u.name} for {cost} coins?", True, (255, 255, 255))
            surface.blit(msg, (cx - msg.get_width() // 2, h // 2 - 60))
            for ci, label in enumerate(["YES", "NO"]):
                c = (255, 255, 255) if ci == self.confirm_choice else (150, 150, 150)
                opt = self.font_small.render(label, True, c)
                ox = cx - 40 + ci * 80
                surface.blit(opt, (ox, h // 2))
