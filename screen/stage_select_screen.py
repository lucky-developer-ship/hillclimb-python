import datetime

import pygame

import assets
from constants import SCREEN_WIDTH
from data.game_data import STAGES
from save_data import LEAGUE_REWARDS, get_daily_seed, get_league


class StageSelectScreen:
    def __init__(self, game):
        self.game = game
        self.font = assets.get_font(22)
        self.font_small = assets.get_font(16)
        self.font_title = assets.get_font(28)
        self.selected_index = 0
        self.stage_rects = []
        cx = SCREEN_WIDTH // 2
        for i in range(len(STAGES)):
            self.stage_rects.append(pygame.Rect(cx - 200, 120 + i * 100, 400, 80))
        self.back_rect = pygame.Rect(cx - 80, 440, 160, 50)
        self.daily_rect = pygame.Rect(cx - 200, 60, 400, 50)
        self.league_rect = pygame.Rect(cx + 80, 400, 200, 40)
        self._seed_input = ""
        self._seed_active = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % (len(STAGES)) if not self._seed_active else self.selected_index
                if not self._seed_active:
                    self.game.sound_manager.play_sfx("click")
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % (len(STAGES)) if not self._seed_active else self.selected_index
                if not self._seed_active:
                    self.game.sound_manager.play_sfx("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self._seed_active and self._seed_input:
                    seed_hash = hash(self._seed_input)
                    self.game.set_screen("game", stage=STAGES[self.selected_index], seed=seed_hash)
                    return
                self._select_stage(self.selected_index)
            elif event.key == pygame.K_BACKSPACE:
                if self._seed_active and self._seed_input:
                    self._seed_input = self._seed_input[:-1]
                else:
                    self._seed_active = False
                    self.game.set_screen("menu")
            elif event.key == pygame.K_q:
                self._seed_active = False
                self.game.set_screen("menu")
            elif self._seed_active and event.key != pygame.K_TAB:
                if event.unicode.isprintable() and len(self._seed_input) < 20:
                    self._seed_input += event.unicode
            elif event.key == pygame.K_TAB:
                self._seed_active = not self._seed_active
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(event.pos):
                self._seed_active = False
                self.game.set_screen("menu")
                return
            if self.daily_rect.collidepoint(event.pos):
                self._start_daily()
                return
            if self._seed_input_rect and self._seed_input_rect.collidepoint(event.pos):
                self._seed_active = True
                return
            self._seed_active = False
            for i, rect in enumerate(self.stage_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = i
                    self._select_stage(i)
                    break

    def _start_daily(self):
        today = datetime.date.today().isoformat()
        if self.game.save_data.last_daily_date == today:
            return
        seed_val = get_daily_seed()
        self.game.set_screen("game", stage=STAGES[0], seed=seed_val, daily=True)

    def _select_stage(self, index):
        stage = STAGES[index]
        if self.game.save_data.is_stage_unlocked(index):
            self.game.set_screen("game", stage=stage)
        elif self.game.save_data.spend_coins(stage.unlock_cost):
            self.game.save_data.unlock_stage(index)
            self.game.save_data.save()
            self.game.set_screen("game", stage=stage)

    def update(self, dt):
        pass

    def render(self, surface):
        surface.fill((26, 26, 33))
        w, h = surface.get_size()
        cx = w // 2

        pygame.draw.rect(surface, (31, 31, 46), (0, 0, w, 50))
        title = self.font_title.render("SELECT STAGE", True, (179, 179, 204))
        surface.blit(title, (cx - title.get_width() // 2, 8))

        trophies = self.game.save_data.trophies
        league = get_league(trophies)
        league_info = self.font_small.render(f"{league} League ({trophies} trophies)", True, (255, 215, 0))
        surface.blit(league_info, (cx - league_info.get_width() // 2, 36))

        daily_color = (100, 180, 100)
        today = datetime.date.today().isoformat()
        if self.game.save_data.last_daily_date == today:
            daily_color = (80, 80, 80)
            daily_label = "DAILY CHALLENGE - DONE"
        else:
            daily_label = "DAILY CHALLENGE"
        pygame.draw.rect(surface, daily_color, self.daily_rect, border_radius=4)
        if daily_color != (80, 80, 80):
            pygame.draw.rect(surface, (120, 255, 120), self.daily_rect, 2, border_radius=4)
        d_text = self.font_small.render(daily_label, True, (255, 255, 255))
        surface.blit(d_text, (cx - d_text.get_width() // 2, self.daily_rect.y + 14))

        bonus = LEAGUE_REWARDS.get(league, 100)
        bonus_text = self.font_small.render(f"Reward: +{bonus} coins", True, (255, 230, 0))
        surface.blit(bonus_text, (cx - bonus_text.get_width() // 2, self.daily_rect.y + 30))

        for i, stage in enumerate(STAGES):
            rect = self.stage_rects[i]
            unlocked = self.game.save_data.is_stage_unlocked(i)
            if i == self.selected_index:
                bg = (64, 115, 89)
            elif not unlocked:
                bg = (46, 46, 56)
            else:
                bg = (56, 64, 71)
            pygame.draw.rect(surface, bg, rect, border_radius=4)
            if i == self.selected_index:
                pygame.draw.rect(surface, (77, 179, 77), rect, 2, border_radius=4)

            name_text = self.font.render(stage.name, True, (255, 255, 255))
            surface.blit(name_text, (rect.x + 15, rect.y + 10))

            if unlocked:
                status = self.font_small.render("UNLOCKED", True, (77, 230, 77))
            else:
                status = self.font_small.render(f"{stage.unlock_cost} coins", True, (255, 204, 0))
            surface.blit(status, (rect.x + rect.width - status.get_width() - 15, rect.y + 12))

            best = self.game.save_data.get_best_distance(stage.id)
            if best > 0:
                best_text = self.font_small.render(f"BEST: {best}m", True, (153, 153, 179))
                surface.blit(best_text, (rect.x + 15, rect.y + 45))

        pygame.draw.rect(surface, (102, 64, 64), self.back_rect, border_radius=4)
        back_text = self.font_small.render("BACK", True, (255, 255, 255))
        surface.blit(back_text, (self.back_rect.x + 60, self.back_rect.y + 12))

        coin_text = self.font_small.render(f"Coins: {self.game.save_data.get_coins()}", True, (255, 230, 0))
        surface.blit(coin_text, (w - coin_text.get_width() - 20, 15))

        self._seed_input_rect = pygame.Rect(cx - 100, 500, 200, 36)
        seed_label = self.font_small.render("Seed:", True, (179, 179, 204))
        surface.blit(seed_label, (cx - seed_label.get_width() // 2, 480))
        border_col = (100, 200, 100) if self._seed_active else (80, 80, 80)
        pygame.draw.rect(surface, (40, 40, 50), self._seed_input_rect, border_radius=3)
        pygame.draw.rect(surface, border_col, self._seed_input_rect, 2, border_radius=3)
        s_text = self.font_small.render(self._seed_input or "enter seed...", True, (200, 200, 200) if self._seed_input else (100, 100, 100))
        surface.blit(s_text, (self._seed_input_rect.x + 8, self._seed_input_rect.y + 8))
        hint = self.font_small.render("TAB to focus, type seed, ENTER to race", True, (120, 120, 120))
        surface.blit(hint, (cx - hint.get_width() // 2, 540))
