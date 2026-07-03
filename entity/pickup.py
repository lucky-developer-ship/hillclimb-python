from enum import Enum


class PickupType(Enum):
    COIN = 1
    FUEL = 2


class Pickup:
    def __init__(self, x, y, ptype):
        self.x = x
        self.y = y
        self.type = ptype
        self.active = True
        self.radius = 0.2 if ptype == PickupType.COIN else 0.25

    def is_active(self):
        return self.active

    def collect(self):
        self.active = False

    def get_position(self):
        return self.x, self.y
