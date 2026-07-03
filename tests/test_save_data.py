from data.game_data import STAGES, VEHICLES
from save_data import BRONZE, CHAMPION, GOLD, SILVER, SaveData, get_league


def test_default_save_data():
    sd = SaveData()
    assert sd.total_coins == 0
    assert sd.selected_vehicle_id == "jeep"
    assert sd.unlocked_vehicles == [True, False, False]
    assert sd.unlocked_stages == [True, False, False]
    assert sd.upgrade_levels == {}
    assert sd.settings == {"music_volume": 0.5, "sfx_volume": 0.7}
    assert sd.trophies == 0
    assert sd.last_daily_date == ""


def test_get_league():
    assert get_league(0) == BRONZE
    assert get_league(50) == BRONZE
    assert get_league(100) == SILVER
    assert get_league(200) == SILVER
    assert get_league(300) == GOLD
    assert get_league(500) == GOLD
    assert get_league(600) == CHAMPION
    assert get_league(1000) == CHAMPION


def test_add_and_spend_coins():
    sd = SaveData()
    sd.add_coins(100)
    assert sd.get_coins() == 100
    assert sd.spend_coins(30) is True
    assert sd.get_coins() == 70
    assert sd.spend_coins(100) is False
    assert sd.get_coins() == 70


def test_vehicle_unlock():
    sd = SaveData()
    assert sd.is_vehicle_unlocked(0) is True
    assert sd.is_vehicle_unlocked(1) is False
    sd.unlock_vehicle(1)
    assert sd.is_vehicle_unlocked(1) is True


def test_stage_unlock():
    sd = SaveData()
    assert sd.is_stage_unlocked(0) is True
    assert sd.is_stage_unlocked(1) is False
    sd.unlock_stage(1)
    assert sd.is_stage_unlocked(1) is True


def test_upgrade_levels():
    sd = SaveData()
    assert sd.get_upgrade_level("jeep", "engine") == 0
    sd.set_upgrade_level("jeep", "engine", 2)
    assert sd.get_upgrade_level("jeep", "engine") == 2


def test_save_and_load():
    sd = SaveData()
    sd.add_coins(500)
    sd.unlock_vehicle(1)
    sd.set_upgrade_level("jeep", "engine", 1)
    sd.save()

    sd2 = SaveData()
    assert sd2.get_coins() == 500
    assert sd2.is_vehicle_unlocked(1) is True
    assert sd2.get_upgrade_level("jeep", "engine") == 1


def test_empty_string_split():
    sd = SaveData()
    sd.load()
    assert sd.unlocked_vehicles == [True] + [False] * (len(VEHICLES) - 1)
    assert sd.unlocked_stages == [True] + [False] * (len(STAGES) - 1)


def test_invalid_json(tmp_path, monkeypatch):
    import save_data as sd_module

    bad_path = tmp_path / "bad_save.json"
    bad_path.write_text("invalid json{{{")
    monkeypatch.setattr(sd_module, "SAVE_PATH", str(bad_path))

    sd = SaveData()
    assert sd.get_coins() == 0
    assert sd.selected_vehicle_id == "jeep"
