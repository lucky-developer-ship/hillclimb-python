class VehicleDef:
    def __init__(
        self,
        id,
        name,
        description,
        base_price,
        chassis_mass,
        wheel_radius,
        suspension_freq,
        suspension_damping,
        max_torque,
        chassis_width,
        chassis_height,
        wheel_base,
        com_offset,
        max_lean_angle,
        lean_torque,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.base_price = base_price
        self.chassis_mass = chassis_mass
        self.wheel_radius = wheel_radius
        self.suspension_freq = suspension_freq
        self.suspension_damping = suspension_damping
        self.max_torque = max_torque
        self.chassis_width = chassis_width
        self.chassis_height = chassis_height
        self.wheel_base = wheel_base
        self.com_offset = com_offset
        self.max_lean_angle = max_lean_angle
        self.lean_torque = lean_torque


class StageDef:
    def __init__(
        self, id, name, unlock_cost, base_height, amplitude, hill_frequency, roughness, octaves,
        completion_distance=500, terrain_color=None, grass_color=None, mountain_color=None,
        sky_colors=None, ground_fill_color=None,
    ):
        self.id = id
        self.name = name
        self.unlock_cost = unlock_cost
        self.base_height = base_height
        self.amplitude = amplitude
        self.hill_frequency = hill_frequency
        self.roughness = roughness
        self.octaves = octaves
        self.completion_distance = completion_distance
        self.terrain_color = terrain_color or (51, 38, 26)
        self.grass_color = grass_color or (77, 128, 46)
        self.grass_line_color = grass_color or (51, 115, 38)
        self.mountain_color = mountain_color or (64, 89, 77)
        self.sky_colors = sky_colors or ((0.3, 0.5, 0.7), (0.7, 0.95, 0.95))
        self.ground_fill_color = ground_fill_color or (51, 38, 26)


class UpgradeDef:
    def __init__(self, id, name, vehicle_id, max_level, costs, values):
        self.id = id
        self.name = name
        self.vehicle_id = vehicle_id
        self.max_level = max_level
        self.costs = costs
        self.values = values


JEEP = VehicleDef(
    id="jeep",
    name="Jeep",
    description="Balanced all-rounder",
    base_price=0,
    chassis_mass=80,
    wheel_radius=0.4,
    suspension_freq=5.0,
    suspension_damping=0.7,
    max_torque=60,
    chassis_width=2.4,
    chassis_height=0.8,
    wheel_base=1.6,
    com_offset=0.1,
    max_lean_angle=15,
    lean_torque=50,
)

TRUCK = VehicleDef(
    id="truck",
    name="Truck",
    description="Heavy duty with big wheels",
    base_price=50000,
    chassis_mass=150,
    wheel_radius=0.55,
    suspension_freq=4.0,
    suspension_damping=0.8,
    max_torque=90,
    chassis_width=2.8,
    chassis_height=0.9,
    wheel_base=2.0,
    com_offset=0.1,
    max_lean_angle=12,
    lean_torque=60,
)

SPORTS_CAR = VehicleDef(
    id="sports",
    name="Sports Car",
    description="Fast and lightweight",
    base_price=150000,
    chassis_mass=60,
    wheel_radius=0.35,
    suspension_freq=6.0,
    suspension_damping=0.6,
    max_torque=120,
    chassis_width=2.2,
    chassis_height=0.6,
    wheel_base=1.8,
    com_offset=0.05,
    max_lean_angle=20,
    lean_torque=40,
)

VEHICLES = [JEEP, TRUCK, SPORTS_CAR]

COUNTRYSIDE = StageDef(
    id="countryside",
    name="Countryside",
    unlock_cost=0,
    base_height=2.0,
    amplitude=4.0,
    hill_frequency=0.04,
    roughness=0.5,
    octaves=4,
    completion_distance=500,
    terrain_color=(51, 38, 26),
    grass_color=(77, 128, 46),
    mountain_color=(64, 89, 77),
    sky_colors=((0.3, 0.5, 0.7), (0.7, 0.95, 0.95)),
    ground_fill_color=(51, 38, 26),
)

DESERT = StageDef(
    id="desert",
    name="Desert",
    unlock_cost=100000,
    base_height=1.0,
    amplitude=6.0,
    hill_frequency=0.03,
    roughness=0.6,
    octaves=5,
    completion_distance=800,
    terrain_color=(110, 90, 50),
    grass_color=(160, 140, 70),
    mountain_color=(120, 90, 60),
    sky_colors=((0.9, 0.7, 0.4), (1.0, 0.9, 0.7)),
    ground_fill_color=(90, 70, 40),
)

ARCTIC = StageDef(
    id="arctic",
    name="Arctic",
    unlock_cost=250000,
    base_height=2.5,
    amplitude=5.0,
    hill_frequency=0.05,
    roughness=0.4,
    octaves=3,
    completion_distance=1000,
    terrain_color=(160, 180, 200),
    grass_color=(200, 220, 240),
    mountain_color=(140, 160, 190),
    sky_colors=((0.5, 0.6, 0.8), (0.8, 0.85, 0.95)),
    ground_fill_color=(140, 160, 180),
)

STAGES = [COUNTRYSIDE, DESERT, ARCTIC]


def _make_upgrades(vehicle_id):
    return [
        UpgradeDef("engine", "Engine", vehicle_id, 5, [5000, 15000, 30000, 60000, 100000], [1.25, 1.5, 1.8, 2.2, 2.5]),
        UpgradeDef("suspension", "Suspension", vehicle_id, 4, [4000, 12000, 25000, 40000], [1.15, 1.3, 1.5, 1.7]),
        UpgradeDef("tires", "Tires", vehicle_id, 4, [3000, 10000, 22000, 35000], [1.2, 1.4, 1.7, 2.0]),
        UpgradeDef("fourwd", "4WD", vehicle_id, 2, [15000, 30000], [1.0, 1.3]),
        UpgradeDef("fuel_cap", "Fuel Cap", vehicle_id, 4, [3000, 8000, 18000, 30000], [1, 2, 3, 4]),
        UpgradeDef("heavy_chassis", "Heavy Chassis", vehicle_id, 3, [10000, 25000, 50000], [0.7, 0.5, 0.3]),
        UpgradeDef("lightweight", "Light Frame", vehicle_id, 3, [12000, 28000, 55000], [0.85, 0.7, 0.55]),
    ]


_upgrade_cache = {}
_MAX_CACHE_SIZE = 16


def get_upgrades(vehicle_id):
    if vehicle_id not in _upgrade_cache:
        if len(_upgrade_cache) >= _MAX_CACHE_SIZE:
            _upgrade_cache.pop(next(iter(_upgrade_cache)))
        _upgrade_cache[vehicle_id] = _make_upgrades(vehicle_id)
    return _upgrade_cache[vehicle_id]


def get_vehicle(vehicle_id):
    for v in VEHICLES:
        if v.id == vehicle_id:
            return v
    return VEHICLES[0]
