import os
import sys

import pygame

from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from data.game_data import STAGES
from save_data import SaveData
from screen.game_screen import GameScreen
from screen.garage_screen import GarageScreen
from screen.menu_screen import MenuScreen
from screen.settings_screen import SettingsScreen
from screen.stage_select_screen import StageSelectScreen
from screen.credits_screen import CreditsScreen
from screen.upgrade_screen import UpgradeScreen
from sound_manager import SoundManager


def is_android():
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ


class Game:
    def __init__(self):
        pygame.init()
        self.android = is_android()
        if self.android:
            self.screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN | pygame.SCALED
            )
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hill Climb Racing Clone")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fullscreen = False
        self.save_data = SaveData()
        self.sound_manager = SoundManager()
        sd = self.save_data
        self.sound_manager.set_volumes(sd.settings["music_volume"], sd.settings["sfx_volume"])
        self.current_screen = None
        self.set_screen("menu")

    def set_screen(self, name, **kwargs):
        if name == "menu":
            self.current_screen = MenuScreen(self)
        elif name == "stage_select":
            self.current_screen = StageSelectScreen(self)
        elif name == "garage":
            self.current_screen = GarageScreen(self)
        elif name == "upgrade":
            vehicle_id = kwargs.get("vehicle_id", "jeep")
            self.current_screen = UpgradeScreen(self, vehicle_id)
        elif name == "game":
            stage = kwargs.get("stage", STAGES[0])
            seed = kwargs.get("seed", None)
            daily = kwargs.get("daily", False)
            self.current_screen = GameScreen(self, stage, seed=seed, daily=daily)
        elif name == "credits":
            self.current_screen = CreditsScreen(self)
        elif name == "settings":
            self.current_screen = SettingsScreen(self)

    def run(self):
        dt = 1.0 / 60.0
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                        if not self.android:
                            self.fullscreen = not self.fullscreen
                            if self.fullscreen:
                                self.screen = pygame.display.set_mode(
                                    (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED
                                )
                            else:
                                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                    elif self.current_screen:
                        self.current_screen.handle_event(event)
                if self.current_screen:
                    self.current_screen.update(dt)
                    self.current_screen.render(self.screen)
                pygame.display.flip()
                dt = self.clock.tick(60) / 1000.0
                if dt > 0.05:
                    dt = 0.05
        finally:
            self.save_data.save()
            pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
