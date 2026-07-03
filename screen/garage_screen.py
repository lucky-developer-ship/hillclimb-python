import math

import pygame

import assets
from constants import SCREEN_WIDTH
from data.game_data import VEHICLES


class GarageScreen:
    def __init__(self, game):
        self.game = game
        self.font = assets.get_font(22)
        self.font_small = assets.get_font(16)
        self.selected_index = 0
        self.vehicle_rects = []
        cx = SCREEN_WIDTH // 2
        for i in range(len(VEHICLES)):
            self.vehicle_rects.append(pygame.Rect(cx - 280, 60 + i * 90, 560, 75))
        self.back_rect = pygame.Rect(cx - 80, 380, 160, 50)
        self.upgrade_rect = pygame.Rect(cx + 120, 380, 160, 50)
        self.confirming = False
        self.confirm_index = 0
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
                    self._complete_purchase(self.confirm_index)
                self.confirming = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(VEHICLES)
                self.game.sound_manager.play_sfx("click")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(VEHICLES)
                self.game.sound_manager.play_sfx("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select_vehicle(self.selected_index)
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_q):
                self.game.set_screen("menu")
            elif event.key == pygame.K_u:
                self._open_upgrades()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(event.pos):
                self.game.set_screen("menu")
                return
            if self.upgrade_rect.collidepoint(event.pos):
                self._open_upgrades()
                return
            for i, rect in enumerate(self.vehicle_rects):
                if rect.collidepoint(event.pos):
                    self._select_vehicle(i)
                    break

    def _select_vehicle(self, index):
        self.selected_index = index
        d = VEHICLES[index]
        if self.game.save_data.is_vehicle_purchased(d.id):
            self.game.save_data.set_selected_vehicle(d.id)
            self.game.save_data.save()
            self.game.sound_manager.play_sfx("click")
        elif self.game.save_data.get_coins() >= d.base_price:
            self.confirming = True
            self.confirm_index = index
            self.confirm_choice = 0
            self.game.sound_manager.play_sfx("click")

    def _complete_purchase(self, index):
        d = VEHICLES[index]
        if self.game.save_data.spend_coins(d.base_price):
            self.game.save_data.purchase_vehicle(d.id)
            self.game.save_data.set_selected_vehicle(d.id)
            self.game.save_data.save()
            self.game.sound_manager.play_sfx("buy")

    def _open_upgrades(self):
        d = VEHICLES[self.selected_index]
        if self.game.save_data.is_vehicle_purchased(d.id):
            self.game.set_screen("upgrade", vehicle_id=d.id)
            self.game.sound_manager.play_sfx("click")

    def update(self, dt):
        if not self.confirming:
            self.time = getattr(self, "time", 0) + dt

    def _draw_vehicle_preview(self, surface, x, y, v_def, angle=0):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        hw = v_def.chassis_width * 10
        hh = v_def.chassis_height * 10
        verts = []
        for lx, ly in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
            rx = lx * cos_a - ly * sin_a
            ry = lx * sin_a + ly * cos_a
            verts.append((int(x + rx), int(y + ry)))
        if len(verts) == 4:
            pygame.draw.polygon(surface, (200, 50, 50), [verts[0], verts[1], verts[2]])
            pygame.draw.polygon(surface, (200, 50, 50), [verts[0], verts[2], verts[3]])
        cab_hw = hw * 0.55
        cab_hh = hh * 0.7
        cab_verts = []
        for lx, ly in [(-cab_hw, hh), (cab_hw, hh), (cab_hw, hh + cab_hh * 2), (-cab_hw, hh + cab_hh * 2)]:
            rx = lx * cos_a - ly * sin_a
            ry = lx * sin_a + ly * cos_a
            cab_verts.append((int(x + rx), int(y + ry)))
        if len(cab_verts) == 4:
            pygame.draw.polygon(surface, (80, 80, 110), [cab_verts[0], cab_verts[1], cab_verts[2]])
            pygame.draw.polygon(surface, (80, 80, 110), [cab_verts[0], cab_verts[2], cab_verts[3]])
        wr = int(v_def.wheel_radius * 10)
        pygame.draw.circle(surface, (60, 60, 60), (x - int(v_def.wheel_base * 5), y + int(hh * 2)), wr)
        pygame.draw.circle(surface, (60, 60, 60), (x + int(v_def.wheel_base * 5), y + int(hh * 2)), wr)

    def render(self, surface):
        surface.fill((26, 26, 33))
        w, h = surface.get_size()
        cx = w // 2

        pygame.draw.rect(surface, (31, 31, 46), (0, 0, w, 50))
        title = self.font.render("GARAGE", True, (179, 179, 204))
        surface.blit(title, (cx - title.get_width() // 2, 10))

        for i, d in enumerate(VEHICLES):
            rect = self.vehicle_rects[i]
            purchased = self.game.save_data.is_vehicle_purchased(d.id)
            is_selected = self.game.save_data.get_selected_vehicle_id() == d.id
            if is_selected:
                bg = (51, 128, 51)
            elif i == self.selected_index:
                bg = (89, 89, 115)
            elif not purchased:
                bg = (46, 46, 56)
            else:
                bg = (56, 56, 71)
            pygame.draw.rect(surface, bg, rect, border_radius=4)

            preview_angle = 0.05 * math.sin(getattr(self, "time", 0) * 1.5 + i)
            self._draw_vehicle_preview(surface, rect.x + 40, rect.y + 38, d, preview_angle)

            name = self.font.render(d.name, True, (255, 255, 255))
            surface.blit(name, (rect.x + 75, rect.y + 8))

            desc = self.font_small.render(d.description, True, (102, 102, 128))
            surface.blit(desc, (rect.x + 75, rect.y + 40))

            if is_selected:
                sel = self.font_small.render("SELECTED", True, (77, 230, 77))
                surface.blit(sel, (rect.x + rect.width - sel.get_width() - 15, rect.y + 10))
            elif purchased:
                owned = self.font_small.render("OWNED", True, (128, 128, 153))
                surface.blit(owned, (rect.x + rect.width - owned.get_width() - 15, rect.y + 10))
            else:
                price_text = self.font_small.render(f"{d.base_price} coins", True, (255, 204, 0))
                surface.blit(price_text, (rect.x + rect.width - price_text.get_width() - 15, rect.y + 10))

            if i == self.selected_index:
                pygame.draw.rect(surface, (153, 153, 204), rect, 2, border_radius=4)

        pygame.draw.rect(surface, (102, 64, 64), self.back_rect, border_radius=4)
        back_text = self.font_small.render("BACK", True, (255, 255, 255))
        surface.blit(back_text, (self.back_rect.x + 60, self.back_rect.y + 12))

        pygame.draw.rect(surface, (77, 77, 51), self.upgrade_rect, border_radius=4)
        up_text = self.font_small.render("UPGRADE", True, (255, 255, 255))
        surface.blit(up_text, (self.upgrade_rect.x + 45, self.upgrade_rect.y + 12))

        coins_text = self.font_small.render(f"Coins: {self.game.save_data.get_coins()}", True, (255, 230, 0))
        surface.blit(coins_text, (w - coins_text.get_width() - 20, 15))

        if self.confirming:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            d = VEHICLES[self.confirm_index]
            msg = self.font.render(f"Buy {d.name} for {d.base_price} coins?", True, (255, 255, 255))
            surface.blit(msg, (cx - msg.get_width() // 2, h // 2 - 60))
            for ci, label in enumerate(["YES", "NO"]):
                c = (255, 255, 255) if ci == self.confirm_choice else (150, 150, 150)
                opt = self.font_small.render(label, True, c)
                ox = cx - 40 + ci * 80
                surface.blit(opt, (ox, h // 2))
