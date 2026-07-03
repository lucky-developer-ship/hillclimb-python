import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.path.insert(0, os.path.dirname(__file__))

from data.game_data import COUNTRYSIDE, JEEP
from entity.terrain import TerrainManager
from entity.vehicle import Vehicle
from physics.world import PhysicsWorld

world = PhysicsWorld()
terrain = TerrainManager(COUNTRYSIDE, world.space)
terrain.update(3, world.space)

ground_height = terrain.get_height_at(3)
spawn_y = (ground_height if ground_height is not None else 2.0) + 2.0
v = Vehicle(world, JEEP, (3, spawn_y))
print(f"Car spawned at (3, {spawn_y:.2f})")

for frame in range(200):
    gas = frame < 100
    brake = False
    v.update(1/60, gas, brake, False, False, terrain)
    world.step(1/60)
    pos = v.chassis.position
    vel = v.chassis.velocity
    if frame % 20 == 0:
        print(f"frame {frame:3d}: pos=({pos.x:.2f}, {pos.y:.2f}) vel=({vel.x:.2f}, {vel.y:.2f}) rate={v.right_motor.rate:.1f} max_f={v.right_motor.max_force:.1f}")

print(f"\nFinal: pos=({v.chassis.position.x:.2f}, {v.chassis.position.y:.2f})")
print(f"Wheels contacting: L={v.terrain_contact_left} R={v.terrain_contact_right}")
print(f"Arbiters in space: {len(world.space._get_arbiters()) if hasattr(world.space, '_get_arbiters') else 'unknown'}")
