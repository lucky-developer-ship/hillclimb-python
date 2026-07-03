import pygame


class InputManager:
    def __init__(self):
        self.keys = None
        self.joystick = None
        try:
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
        except pygame.error:
            self.joystick = None

    def update(self):
        self.keys = pygame.key.get_pressed()
        if self.joystick:
            try:
                self.joystick.rumble(0, 0, 0) if hasattr(self.joystick, "rumble") else None
            except pygame.error:
                pass
            pygame.event.pump()

    def _key(self, k):
        if self.keys is None:
            return False
        try:
            return bool(self.keys[k])
        except (IndexError, TypeError):
            return False

    def _axis(self, axis, deadzone=0.3):
        if not self.joystick:
            return 0.0
        try:
            val = self.joystick.get_axis(axis)
            if abs(val) < deadzone:
                return 0.0
            return val
        except (pygame.error, ValueError):
            return 0.0

    def _button(self, btn):
        if not self.joystick:
            return False
        try:
            return bool(self.joystick.get_button(btn))
        except (pygame.error, ValueError):
            return False

    def _hat(self, axis):
        if not self.joystick:
            return 0
        try:
            hat = self.joystick.get_hat(0)
            if axis == 0:
                return hat[0]
            return hat[1]
        except (pygame.error, ValueError, IndexError):
            return 0

    def is_gas_pressed(self):
        if self._key(pygame.K_RIGHT) or self._key(pygame.K_d):
            return True
        if self._axis(5) > 0.5:
            return True
        return self._button(7) or self._button(5)

    def is_brake_pressed(self):
        if self._key(pygame.K_LEFT) or self._key(pygame.K_a):
            return True
        if self._axis(2) > 0.5:
            return True
        if self._axis(4) > 0.5:
            return True
        return self._button(6) or self._button(4)

    def is_lean_left(self):
        if self._key(pygame.K_UP) or self._key(pygame.K_w):
            return True
        return self._hat(1) > 0

    def is_lean_right(self):
        if self._key(pygame.K_DOWN) or self._key(pygame.K_s):
            return True
        return self._hat(1) < 0

    def is_pause_pressed(self):
        if self._key(pygame.K_ESCAPE):
            return True
        return self._button(9) or self._button(7)
