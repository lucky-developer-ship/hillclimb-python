import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.game_data import (
    ARCTIC,
    COUNTRYSIDE,
    DESERT,
    JEEP,
    SPORTS_CAR,
    STAGES,
    TRUCK,
    VEHICLES,
    get_upgrades,
    get_vehicle,
)


def test_vehicles_count():
    assert len(VEHICLES) == 3


def test_vehicles_defined():
    assert VEHICLES[0].id == "jeep"
    assert VEHICLES[1].id == "truck"
    assert VEHICLES[2].id == "sports"


def test_stages_count():
    assert len(STAGES) == 3


def test_get_vehicle():
    v = get_vehicle("truck")
    assert v.id == "truck"
    assert v.name == "Truck"


def test_get_vehicle_default():
    v = get_vehicle("nonexistent")
    assert v.id == "jeep"


def test_get_upgrades():
    upgrades = get_upgrades("jeep")
    assert len(upgrades) == 7
    ids = [u.id for u in upgrades]
    assert "engine" in ids
    assert "suspension" in ids
    assert "tires" in ids
    assert "fourwd" in ids
    assert "fuel_cap" in ids
    assert "heavy_chassis" in ids
    assert "lightweight" in ids


def test_upgrade_cache():
    cache_before = get_upgrades("jeep")
    cache_after = get_upgrades("jeep")
    assert cache_before is cache_after


def test_upgrade_values():
    upgrades = get_upgrades("jeep")
    engine = [u for u in upgrades if u.id == "engine"][0]
    assert engine.max_level == 5
    assert len(engine.costs) == 5
    assert len(engine.values) == 5


def test_vehicle_prices():
    assert JEEP.base_price == 0
    assert TRUCK.base_price == 50000
    assert SPORTS_CAR.base_price == 150000


def test_stage_completion_distances():
    assert COUNTRYSIDE.completion_distance == 500
    assert DESERT.completion_distance == 800
    assert ARCTIC.completion_distance == 1000
