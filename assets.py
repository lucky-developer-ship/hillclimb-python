import os

import pygame

_FONT_PATH = os.path.join(os.path.dirname(__file__), "PressStart2P-Regular.ttf")
_font_cache = {}


def get_font(size):
    key = size
    font = _font_cache.get(key)
    if font is None:
        try:
            if os.path.exists(_FONT_PATH):
                font = pygame.font.Font(_FONT_PATH, size)
            else:
                font = pygame.font.Font(None, size)
        except pygame.error:
            font = pygame.font.Font(None, size)
        _font_cache[key] = font
    return font


def clear_font_cache():
    _font_cache.clear()
