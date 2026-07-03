import json
import os
from pathlib import Path

from data.game_data import STAGES, VEHICLES

# On Android, save to the app's private data directory provided by p4a.
# On desktop, anchor to this file's folder for consistency across launch methods.
if "ANDROID_PRIVATE" in os.environ:
    SAVE_PATH = str(Path(os.environ["ANDROID_PRIVATE"]) / "hillclimb_save.json")
else:
    SAVE_PATH = str(Path(__file__).resolve().parent / "hillclimb_save.json")
SAVE_VERSION = 1


BRONZE = "Bronze"
SILVER = "Silver"
GOLD = "Gold"
CHAMPION = "Champion"

LEAGUE_THRESHOLDS = {BRONZE: 0, SILVER: 100, GOLD: 300, CHAMPION: 600}
LEAGUE_REWARDS = {BRONZE: 100, SILVER: 500, GOLD: 2000, CHAMPION: 8000}


def get_league(trophies):
    for league, threshold in reversed(list(LEAGUE_THRESHOLDS.items())):
        if trophies >= threshold:
            return league
    return BRONZE


def get_daily_seed():
    import datetime
    import zlib

    return zlib.adler32(datetime.date.today().isoformat().encode())


class SaveData:
    def __init__(self):
        self.total_coins = 0
        self.selected_vehicle_id = "jeep"
        self.unlocked_vehicles = [True, False, False]
        self.unlocked_stages = [True, False, False]
        self.upgrade_levels = {}
        self.settings = {"music_volume": 0.5, "sfx_volume": 0.7}
        self.best_distances = {}
        self.trophies = 0
        self.last_daily_date = ""
        self.load()

    def load(self):
        if not os.path.exists(SAVE_PATH):
            return
        try:
            with open(SAVE_PATH, "r") as f:
                data = json.load(f)

            self.total_coins = data.get("total_coins", 0)
            self.selected_vehicle_id = data.get("selected_vehicle", "jeep")
            self.unlocked_vehicles = [True] + [False] * (len(VEHICLES) - 1)
            uv = data.get("unlocked_vehicles", "")
            if uv:
                for v_name in uv.split(","):
                    v_name = v_name.strip()
                    if not v_name:
                        continue
                    for i, v_def in enumerate(VEHICLES):
                        if v_def.id == v_name:
                            self.unlocked_vehicles[i] = True
                            break
            self.unlocked_stages = [True] + [False] * (len(STAGES) - 1)
            us = data.get("unlocked_stages", "")
            if us:
                for s_name in us.split(","):
                    s_name = s_name.strip()
                    if not s_name:
                        continue
                    for i, s_def in enumerate(STAGES):
                        if s_def.id == s_name:
                            self.unlocked_stages[i] = True
                            break
            self.upgrade_levels = data.get("upgrade_levels", {})
            self.settings = data.get("settings", {"music_volume": 0.5, "sfx_volume": 0.7})
            self.best_distances = data.get("best_distances", {})
            self.trophies = data.get("trophies", 0)
            self.last_daily_date = data.get("last_daily_date", "")
        except (json.JSONDecodeError, IOError):
            pass

    def save(self):
        uv_parts = []
        for i, v in enumerate(VEHICLES):
            if self.unlocked_vehicles[i]:
                uv_parts.append(v.id)

        us_parts = []
        for i, s in enumerate(STAGES):
            if self.unlocked_stages[i]:
                us_parts.append(s.id)

        data = {
            "version": SAVE_VERSION,
            "total_coins": self.total_coins,
            "selected_vehicle": self.selected_vehicle_id,
            "unlocked_vehicles": ",".join(uv_parts),
            "unlocked_stages": ",".join(us_parts),
            "upgrade_levels": self.upgrade_levels,
            "settings": self.settings,
            "best_distances": self.best_distances,
            "trophies": self.trophies,
            "last_daily_date": self.last_daily_date,
        }
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def add_coins(self, amount):
        self.total_coins += amount

    def spend_coins(self, amount):
        if self.total_coins >= amount:
            self.total_coins -= amount
            return True
        return False

    def get_coins(self):
        return self.total_coins

    def set_selected_vehicle(self, vehicle_id):
        self.selected_vehicle_id = vehicle_id

    def get_selected_vehicle_id(self):
        return self.selected_vehicle_id

    def is_vehicle_unlocked(self, index):
        return self.unlocked_vehicles[index]

    def unlock_vehicle(self, index):
        if 0 <= index < len(self.unlocked_vehicles):
            self.unlocked_vehicles[index] = True

    def is_stage_unlocked(self, index):
        return self.unlocked_stages[index]

    def unlock_stage(self, index):
        if 0 <= index < len(self.unlocked_stages):
            self.unlocked_stages[index] = True

    def is_vehicle_purchased(self, vehicle_id):
        if vehicle_id == "jeep":
            return True
        for i, v in enumerate(VEHICLES):
            if v.id == vehicle_id:
                return i < len(self.unlocked_vehicles) and self.unlocked_vehicles[i]
        return False

    def purchase_vehicle(self, vehicle_id):
        for i, v in enumerate(VEHICLES):
            if v.id == vehicle_id:
                self.unlock_vehicle(i)
                self.save()
                break

    def get_upgrade_level(self, vehicle_id, upgrade_id):
        key = f"{upgrade_id}_{vehicle_id}"
        return self.upgrade_levels.get(key, 0)

    def set_upgrade_level(self, vehicle_id, upgrade_id, level):
        key = f"{upgrade_id}_{vehicle_id}"
        self.upgrade_levels[key] = level

    def get_best_distance(self, stage_id):
        return self.best_distances.get(stage_id, 0)

    def update_best_distance(self, stage_id, distance):
        current = self.best_distances.get(stage_id, 0)
        if distance > current:
            self.best_distances[stage_id] = distance
            return True
        return False
