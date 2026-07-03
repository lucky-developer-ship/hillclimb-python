import math
import random
import struct
from io import BytesIO

import pygame


def _gen_wav(freq, duration, volume=0.5, wave_type="sine"):
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    data = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        if wave_type == "sine":
            val = math.sin(2 * math.pi * freq * t)
        elif wave_type == "square":
            val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
        elif wave_type == "noise":
            val = random.uniform(-1.0, 1.0)
        elif wave_type == "sweep":
            f = freq + (t / duration) * 2000
            val = math.sin(2 * math.pi * f * t)
        else:
            val = 0
        envelope = max(0, 1 - t / duration)
        val *= volume * envelope * 0.8
        val = max(-1, min(1, val))
        sample = int(val * 32767)
        data.extend(struct.pack("<h", sample))
    wav_data = bytearray()
    data_size = len(data)
    wav_data.extend(b"RIFF")
    wav_data.extend(struct.pack("<I", 36 + data_size))
    wav_data.extend(b"WAVE")
    wav_data.extend(b"fmt ")
    wav_data.extend(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    wav_data.extend(b"data")
    wav_data.extend(struct.pack("<I", data_size))
    wav_data.extend(data)
    return BytesIO(wav_data)


def _gen_music_wav(duration=8.0):
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    data = bytearray()
    notes = [130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94, 261.63]
    note_len = n_samples // len(notes)
    for i in range(n_samples):
        t = i / sample_rate
        note_idx = i // note_len
        freq = notes[note_idx % len(notes)]
        val = math.sin(2 * math.pi * freq * t) * 0.15
        val += math.sin(2 * math.pi * freq * 2 * t) * 0.05
        val += math.sin(2 * math.pi * (freq * 0.5) * t) * 0.08
        envelope = max(0, 1 - (i % note_len) / note_len)
        crossfade = min(1, (i % note_len) / (note_len * 0.1))
        fade_out = max(0, 1 - max(0, i - n_samples + int(sample_rate * 0.5)) / int(sample_rate * 0.5))
        val *= envelope * crossfade * fade_out * 0.8
        val = max(-1, min(1, val))
        sample = int(val * 32767)
        data.extend(struct.pack("<h", sample))
    wav_data = bytearray()
    data_size = len(data)
    wav_data.extend(b"RIFF")
    wav_data.extend(struct.pack("<I", 36 + data_size))
    wav_data.extend(b"WAVE")
    wav_data.extend(b"fmt ")
    wav_data.extend(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    wav_data.extend(b"data")
    wav_data.extend(struct.pack("<I", data_size))
    wav_data.extend(data)
    return BytesIO(wav_data)


class SoundManager:
    def __init__(self):
        self.enabled = True
        self.muted = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except pygame.error:
            # No audio device/driver available (headless box, some CI
            # runners, misconfigured drivers). Game should still run,
            # just silently.
            self.enabled = False
        self.sounds = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        if self.enabled:
            self._load_sounds()

    def _load_sounds(self):
        try:
            self.sounds["engine"] = pygame.mixer.Sound(_gen_wav(80, 0.5, 0.15, "square"))
            self.sounds["engine"].set_volume(0)
            self.sounds["coin"] = pygame.mixer.Sound(_gen_wav(880, 0.12, 0.5, "sine"))
            self.sounds["fuel"] = pygame.mixer.Sound(_gen_wav(440, 0.15, 0.5, "sine"))
            self.sounds["crash"] = pygame.mixer.Sound(_gen_wav(60, 0.3, 0.6, "noise"))
            self.sounds["click"] = pygame.mixer.Sound(_gen_wav(600, 0.08, 0.4, "sine"))
            self.sounds["buy"] = pygame.mixer.Sound(_gen_wav(523, 0.1, 0.5, "sine"))
            self.sounds["stage_complete"] = pygame.mixer.Sound(_gen_wav(1047, 0.5, 0.5, "sweep"))
            self.sounds["game_over"] = pygame.mixer.Sound(_gen_wav(200, 0.4, 0.5, "sweep"))
        except Exception:
            self.enabled = False
            self.sounds = {}

    def set_volumes(self, music_vol, sfx_vol):
        self.music_volume = music_vol
        self.sfx_volume = sfx_vol

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.stop_engine()
            self.stop_music()
        else:
            self.play_music()

    def play_sfx(self, name):
        if self.muted or not self.enabled or name not in self.sounds or self.sfx_volume <= 0:
            return
        self.sounds[name].set_volume(self.sfx_volume)
        self.sounds[name].play()

    def start_engine(self):
        if self.muted or not self.enabled or "engine" not in self.sounds:
            return
        self.sounds["engine"].set_volume(self.sfx_volume * 0.3)
        self.sounds["engine"].play(-1)
        self._current_engine_freq = 80

    def stop_engine(self):
        if self.enabled and "engine" in self.sounds:
            self.sounds["engine"].stop()

    def update_engine(self, gas_or_brake):
        if not self.enabled or "engine" not in self.sounds:
            return
        if gas_or_brake:
            vol = self.sfx_volume * 0.4
            self.sounds["engine"].set_volume(vol)
        else:
            vol = self.sfx_volume * 0.08
            self.sounds["engine"].set_volume(vol)

    def update_engine_pitch(self, wheel_rpm, gas_or_brake):
        if not self.enabled or "engine" not in self.sounds:
            return
        if not gas_or_brake:
            return
        target_freq = 55 + min(200, abs(wheel_rpm) * 2)
        target_freq = max(55, min(300, target_freq))
        threshold = 25 if hasattr(self, "_current_engine_freq") else 0
        if abs(getattr(self, "_current_engine_freq", 0) - target_freq) > threshold:
            self._current_engine_freq = target_freq
            old_vol = self.sounds["engine"].get_volume()
            self.sounds["engine"].stop()
            self.sounds["engine"] = pygame.mixer.Sound(_gen_wav(target_freq, 0.3, 0.15, "square"))
            self.sounds["engine"].set_volume(old_vol)
            self.sounds["engine"].play(-1)

    def play_music(self):
        if self.muted or not self.enabled:
            return
        self.stop_music()
        try:
            music_wav = _gen_music_wav()
            self._music_sound = pygame.mixer.Sound(music_wav)
            self._music_sound.set_volume(self.music_volume * 0.3)
            self._music_sound.play(-1)
        except Exception:
            pass

    def stop_music(self):
        if hasattr(self, "_music_sound") and self._music_sound:
            self._music_sound.stop()
            self._music_sound = None

    def update_music_volume(self):
        if hasattr(self, "_music_sound") and self._music_sound:
            self._music_sound.set_volume(self.music_volume * 0.3)
