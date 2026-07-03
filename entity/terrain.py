import math
import random

import pymunk

from constants import (
    FRICTION_ZONE_LENGTH,
    FUEL_PICKUP_INTERVAL,
    ICE_FRICTION,
    MUD_FRICTION,
    TERRAIN_CHUNK_WIDTH,
    TERRAIN_POINTS_PER_CHUNK,
)
from entity.physics_object import PhysicsObject, PhysicsObjectType
from entity.pickup import Pickup, PickupType
from physics.world import CollisionCategories


def layered_noise(x, amplitude, frequency, roughness, octaves, seed=0):
    value = 0.0
    amp = amplitude
    freq = frequency
    phase = seed * 0.137
    for _ in range(octaves):
        value += amp * (math.sin(x * freq + phase) + math.sin(x * freq * 2.17 + 1.3 + phase * 0.7)) * 0.5
        amp *= roughness
        freq *= 2.0
        phase *= 1.3
    return value


class TerrainChunk:
    def __init__(self, index, stage_def, seed, space):
        self.index = index
        self.start_x = index * TERRAIN_CHUNK_WIDTH
        self.end_x = self.start_x + TERRAIN_CHUNK_WIDTH
        self.space = space
        self.points = []
        self.bodies = []
        self.shapes = []
        num_points = TERRAIN_POINTS_PER_CHUNK
        for i in range(num_points):
            t = i / (num_points - 1)
            wx = self.start_x + t * TERRAIN_CHUNK_WIDTH
            noise_val = layered_noise(
                wx, stage_def.amplitude, stage_def.hill_frequency, stage_def.roughness, stage_def.octaves, seed
            )
            wy = stage_def.base_height + noise_val
            self.points.append((wx, wy))
        self._create_static_bodies(space)

    def _get_friction_at(self, x):
        zone_index = int(x / FRICTION_ZONE_LENGTH)
        rng = random.Random(self.index * 10000 + zone_index * 7 + 999)
        zone_type = rng.randint(0, 20)
        if zone_type < 2:
            return ICE_FRICTION, "ice"
        elif zone_type < 5:
            return MUD_FRICTION, "mud"
        return 0.8, "normal"

    def _create_static_bodies(self, space):
        if len(self.points) < 2:
            return
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.terrain_index = self.index
        self.bodies.append(body)
        space.add(body)
        self.segment_frictions = []
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            mid_x = (x1 + x2) / 2
            friction, zone_type = self._get_friction_at(mid_x)
            seg = pymunk.Segment(body, (x1, y1), (x2, y2), 0.15)
            seg.friction = friction
            seg.elasticity = 0.1
            seg.collision_type = 1
            seg.zone_type = zone_type
            seg.filter = pymunk.ShapeFilter(
                categories=CollisionCategories.TERRAIN, mask=CollisionCategories.CHASSIS | CollisionCategories.WHEEL
            )
            space.add(seg)
            self.shapes.append(seg)
            self.segment_frictions.append((mid_x, friction, zone_type))

    def get_zone_type_at(self, x):
        for mid_x, fric, ztype in self.segment_frictions:
            if abs(x - mid_x) < 0.5:
                return ztype
        return "normal"

    def get_zone_color(self, x):
        ztype = self.get_zone_type_at(x)
        if ztype == "ice":
            return (180, 210, 240)
        elif ztype == "mud":
            return (90, 60, 30)
        return None

    def get_surface_points(self):
        return self.points

    def get_height_at(self, x):
        pts = self.points
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= x <= x1:
                t = (x - x0) / (x1 - x0) if x1 != x0 else 0
                return y0 + t * (y1 - y0)
        return None

    def dispose(self, space):
        for s in self.shapes:
            space.remove(s)
        for b in self.bodies:
            space.remove(b)
        self.shapes.clear()
        self.bodies.clear()


class TerrainManager:
    def __init__(self, stage_def, space, seed=None):
        self.stage_def = stage_def
        self.seed = seed if seed is not None else random.randint(0, 99999)
        self.space = space
        self.chunks = {}
        self.pickups = []
        self._chunk_pickups = {}
        self.objects = []
        self._chunk_objects = {}
        self._next_fuel_x = FUEL_PICKUP_INTERVAL

    def get_chunks(self):
        return list(self.chunks.values())

    def get_pickups(self):
        return self.pickups

    def get_objects(self):
        return self.objects

    def get_zone_type_at(self, x):
        chunk_index = int(math.floor(x / TERRAIN_CHUNK_WIDTH))
        chunk = self.chunks.get(chunk_index)
        if chunk is None:
            return "normal"
        return chunk.get_zone_type_at(x)

    def _generate_chunk(self, index):
        chunk = TerrainChunk(index, self.stage_def, self.seed, self.space)
        self.chunks[index] = chunk
        rng = random.Random(self.seed + index * 1000 + 999)

        for _ in range(3):
            t = rng.uniform(0.1, 0.9)
            px = chunk.start_x + t * TERRAIN_CHUNK_WIDTH
            terrain_y = chunk.get_height_at(px)
            if terrain_y is None:
                continue
            height_offset = 0.5 + rng.random() * 1.5
            py = terrain_y + height_offset
            ptype = PickupType.COIN if rng.random() < 0.7 else PickupType.FUEL
            pickup = Pickup(px, py, ptype)
            self.pickups.append(pickup)
            self._chunk_pickups.setdefault(index, []).append(pickup)

        for _ in range(rng.randint(0, 2)):
            t = rng.uniform(0.1, 0.9)
            ox = chunk.start_x + t * TERRAIN_CHUNK_WIDTH
            terrain_y = chunk.get_height_at(ox)
            if terrain_y is None:
                continue
            oy = terrain_y + 0.3
            obj_type = rng.choice([PhysicsObjectType.CRATE, PhysicsObjectType.LOG, PhysicsObjectType.ROCK])
            obj = PhysicsObject(ox, oy, obj_type, self.space)
            self.objects.append(obj)
            self._chunk_objects.setdefault(index, []).append(obj)

    def get_height_at(self, x):
        chunk_index = int(math.floor(x / TERRAIN_CHUNK_WIDTH))
        chunk = self.chunks.get(chunk_index)
        if chunk is None:
            return None
        return chunk.get_height_at(x)

    def _spawn_interval_fuel(self, camera_x):
        while self._next_fuel_x < camera_x + 20:
            chunk_index = int(math.floor(self._next_fuel_x / TERRAIN_CHUNK_WIDTH))
            chunk = self.chunks.get(chunk_index)
            if chunk:
                terrain_y = chunk.get_height_at(self._next_fuel_x)
                if terrain_y is not None:
                    fuel = Pickup(self._next_fuel_x, terrain_y + 1.0, PickupType.FUEL)
                    self.pickups.append(fuel)
                    self._chunk_pickups.setdefault(chunk_index, []).append(fuel)
            self._next_fuel_x += FUEL_PICKUP_INTERVAL

    def update(self, camera_x, space):
        view_left = camera_x - 12
        view_right = camera_x + 12
        chunk_size = TERRAIN_CHUNK_WIDTH
        start_idx = int(math.floor(view_left / chunk_size)) - 1
        end_idx = int(math.ceil(view_right / chunk_size)) + 1
        existing = set(self.chunks.keys())
        needed = set(range(start_idx, end_idx + 1))
        for idx in needed - existing:
            self._generate_chunk(idx)
        for idx in existing - needed:
            self.chunks[idx].dispose(self.space)
            del self.chunks[idx]
            if idx in self._chunk_pickups:
                for p in self._chunk_pickups[idx]:
                    self.pickups.remove(p)
                del self._chunk_pickups[idx]
            if idx in self._chunk_objects:
                for o in self._chunk_objects[idx]:
                    o.dispose(self.space)
                    self.objects.remove(o)
                del self._chunk_objects[idx]
        self._spawn_interval_fuel(camera_x)
