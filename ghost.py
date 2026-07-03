import json
import os
from pathlib import Path

from constants import GHOST_RECORD_INTERVAL as _GRI

GHOST_DIR = str(Path(__file__).resolve().parent / "ghosts")


class GhostRecorder:
    def __init__(self, stage_id):
        self.stage_id = stage_id
        self._frames = []
        self._counter = 0

    def record(self, x, y, angle):
        self._counter += 1
        if self._counter % _GRI == 0:
            self._frames.append([round(x, 2), round(y, 2), round(angle, 4)])

    def save(self):
        if not self._frames:
            return
        os.makedirs(GHOST_DIR, exist_ok=True)
        path = os.path.join(GHOST_DIR, f"{self.stage_id}.json")
        with open(path, "w") as f:
            json.dump(self._frames, f)


class GhostPlayer:
    def __init__(self, stage_id):
        self._frames = []
        path = os.path.join(GHOST_DIR, f"{stage_id}.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    raw = json.load(f)
                self._frames = raw
            except (json.JSONDecodeError, IOError):
                self._frames = []

    def get_state(self, frame_counter):
        idx = frame_counter // _GRI
        if not self._frames or idx >= len(self._frames):
            return None
        data = self._frames[idx]
        return {"x": data[0], "y": data[1], "angle": data[2]}

    def has_data(self):
        return len(self._frames) > 0
