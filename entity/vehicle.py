import math

import pymunk

from constants import AIR_CONTROL_TORQUE, LANDING_DAMPING_BOOST, LANDING_DAMPING_DECAY, STEEP_SLOPE_ANGLE
from entity.pickup import PickupType
from physics.world import CollisionCategories


class Vehicle:
    def __init__(self, world, vehicle_def, start_pos):
        self.defn = vehicle_def
        d = vehicle_def
        self.world = world
        x, y = start_pos

        chassis_moment = pymunk.moment_for_box(d.chassis_mass, (d.chassis_width, d.chassis_height))
        self.chassis = pymunk.Body(d.chassis_mass, chassis_moment)
        self.chassis.position = (x, y)
        world.add_body(self.chassis)
        chassis_shape = pymunk.Poly.create_box(self.chassis, (d.chassis_width, d.chassis_height))
        chassis_shape.friction = 0.5
        chassis_shape.elasticity = 0.1
        chassis_shape.collision_type = 2
        chassis_shape.filter = pymunk.ShapeFilter(
            categories=CollisionCategories.CHASSIS, mask=CollisionCategories.TERRAIN | CollisionCategories.PICKUP
        )
        world.add_shape(chassis_shape)

        wheel_mass = 15.0
        wheel_moment = pymunk.moment_for_circle(wheel_mass, 0, d.wheel_radius)
        self.left_wheel = pymunk.Body(wheel_mass, wheel_moment)
        self.left_wheel.position = (x - d.wheel_base / 2, y - 0.3)
        world.add_body(self.left_wheel)
        lw_shape = pymunk.Circle(self.left_wheel, d.wheel_radius)
        lw_shape.friction = 0.9
        lw_shape.elasticity = 0.2
        lw_shape.collision_type = CollisionCategories.WHEEL
        lw_shape.filter = pymunk.ShapeFilter(
            categories=CollisionCategories.WHEEL, mask=CollisionCategories.TERRAIN | CollisionCategories.PICKUP
        )
        world.add_shape(lw_shape)

        self.right_wheel = pymunk.Body(wheel_mass, wheel_moment)
        self.right_wheel.position = (x + d.wheel_base / 2, y - 0.3)
        world.add_body(self.right_wheel)
        rw_shape = pymunk.Circle(self.right_wheel, d.wheel_radius)
        rw_shape.friction = 0.9
        rw_shape.elasticity = 0.2
        rw_shape.collision_type = CollisionCategories.WHEEL
        rw_shape.filter = pymunk.ShapeFilter(
            categories=CollisionCategories.WHEEL, mask=CollisionCategories.TERRAIN | CollisionCategories.PICKUP
        )
        world.add_shape(rw_shape)

        rest_len = d.wheel_radius + 0.1
        stiff = d.suspension_freq**2 * wheel_mass * 4
        damp = 2.0 * d.suspension_damping * math.sqrt(stiff * wheel_mass)
        att_y = -d.chassis_height * 0.5 + 0.1
        self.left_spring = pymunk.DampedSpring(
            self.chassis, self.left_wheel, (-d.wheel_base / 2, att_y), (0, 0), rest_len, stiff, damp
        )
        world.add_constraint(self.left_spring)
        self.right_spring = pymunk.DampedSpring(
            self.chassis, self.right_wheel, (d.wheel_base / 2, att_y), (0, 0), rest_len, stiff, damp
        )
        world.add_constraint(self.right_spring)

        self.left_motor = pymunk.SimpleMotor(self.chassis, self.left_wheel, 0)
        self.left_motor.max_force = 0
        world.add_constraint(self.left_motor)
        self.right_motor = pymunk.SimpleMotor(self.chassis, self.right_wheel, 0)
        self.right_motor.max_force = 0
        world.add_constraint(self.right_motor)

        self.game_over_flag = False
        self.flips = 0
        self.prev_up = (0, 1)
        self.upside_down_time = 0
        self.terrain_contact_left = False
        self.terrain_contact_right = False
        self.upgrade_values = {}
        self._suspension_force_mult = 1.0
        self._torque_mult = 1.0
        self._traction_mult = 1.0
        self._four_wd = False
        self._fuel_cap_mult = 1.0
        self.chassis_shape = chassis_shape
        self.left_wheel_shape = lw_shape
        self.right_wheel_shape = rw_shape
        self._air_torque = 0.0
        self._landing_damping_boost = 0.0
        self._prev_terrain_contact_left = False
        self._prev_terrain_contact_right = False
        self._wheel_ground_friction = 0.9
        self._fuel_consumption_mult = 1.0
        self._mass_mult = 1.0
        self._com_offset_mod = 0.0

    def get_fuel_max(self):
        from constants import FUEL_CAP_UPGRADE_BONUS, FUEL_MAX

        bonus = (self._fuel_cap_mult - 1.0) * FUEL_CAP_UPGRADE_BONUS
        return FUEL_MAX + bonus

    def get_fuel_consumption_mult(self):
        return self._fuel_consumption_mult

    def apply_upgrades(self, upgrades, levels):
        self.upgrade_values = {}
        for i, u in enumerate(upgrades):
            level = levels[i] if i < len(levels) else 0
            if level > 0 and u.values:
                val = u.values[min(level - 1, len(u.values) - 1)]
                self.upgrade_values[u.id] = val
            else:
                self.upgrade_values[u.id] = 1.0
        self._suspension_force_mult = self.upgrade_values.get("suspension", 1.0)
        self._torque_mult = self.upgrade_values.get("engine", 1.0)
        self._traction_mult = self.upgrade_values.get("tires", 1.0)
        self._four_wd = self.upgrade_values.get("fourwd", 1.0) > 1.0
        self._fuel_cap_mult = self.upgrade_values.get("fuel_cap", 1.0)

        self._mass_mult = 1.0
        self._fuel_consumption_mult = 1.0
        self._com_offset_mod = 0.0
        hc_val = self.upgrade_values.get("heavy_chassis", 1.0)
        if hc_val < 1.0:
            self._mass_mult = 1.0 + (1.0 - hc_val) * 1.5
            self._fuel_consumption_mult = 1.0 + (1.0 - hc_val) * 0.4
            self._com_offset_mod = -0.08 * (1.0 - hc_val) * 3
        lw_val = self.upgrade_values.get("lightweight", 1.0)
        if lw_val < 1.0:
            self._mass_mult = 1.0 - (1.0 - lw_val) * 0.6
            self._fuel_consumption_mult = 1.0 - (1.0 - lw_val) * 0.2
            self._com_offset_mod = 0.05 * (1.0 - lw_val) * 3

        d = self.defn
        rest_len = d.wheel_radius + 0.1
        stiff = d.suspension_freq**2 * 15.0 * 4 * self._suspension_force_mult
        damp = 2.0 * d.suspension_damping * math.sqrt(stiff * 15.0)
        damp_boosted = damp + self._landing_damping_boost * 10.0
        self.left_spring.stiffness = stiff
        self.left_spring.damping = damp_boosted
        self.left_spring.rest_length = rest_len
        self.right_spring.stiffness = stiff
        self.right_spring.damping = damp_boosted
        self.right_spring.rest_length = rest_len

        new_mass = d.chassis_mass * self._mass_mult
        chassis_moment = pymunk.moment_for_box(new_mass, (d.chassis_width, d.chassis_height))
        self.chassis.mass = new_mass
        self.chassis.moment = chassis_moment
        self.chassis.center_of_gravity = (0, self._com_offset_mod)

    def get_position(self):
        return self.chassis

    def get_angle(self):
        return self.chassis.angle

    def get_left_wheel(self):
        return self.left_wheel

    def get_right_wheel(self):
        return self.right_wheel

    def get_flips(self):
        return self.flips

    def is_game_over(self):
        return self.game_over_flag

    def check_game_over(self, dt):
        up_y = math.cos(self.chassis.angle)
        if up_y < -0.3:
            self.upside_down_time += dt
            if self.prev_up[1] >= -0.3:
                self.flips += 1
        else:
            self.upside_down_time = 0
        self.prev_up = (0 if abs(math.sin(self.chassis.angle)) < 0.01 else -math.sin(self.chassis.angle), up_y)
        if self.upside_down_time > 3.0:
            self.game_over_flag = True

    def update(self, dt, gas, brake, lean_left, lean_right, terrain_manager):
        d = self.defn

        self.terrain_contact_left = self.world.body_has_contacts(self.left_wheel)
        self.terrain_contact_right = self.world.body_has_contacts(self.right_wheel)

        in_air = not (self.terrain_contact_left or self.terrain_contact_right)

        left_landed = self.terrain_contact_left and not self._prev_terrain_contact_left
        right_landed = self.terrain_contact_right and not self._prev_terrain_contact_right
        if left_landed or right_landed:
            self._landing_damping_boost = LANDING_DAMPING_BOOST

        if self._landing_damping_boost > 0:
            self._landing_damping_boost = max(0, self._landing_damping_boost - LANDING_DAMPING_DECAY * dt)
            wheel_mass = 15.0
            stiff = d.suspension_freq**2 * wheel_mass * 4 * self._suspension_force_mult
            damp = 2.0 * d.suspension_damping * math.sqrt(stiff * wheel_mass)
            boosted = damp + self._landing_damping_boost * 10.0
            self.left_spring.damping = boosted
            self.right_spring.damping = boosted
        else:
            wheel_mass = 15.0
            stiff = d.suspension_freq**2 * wheel_mass * 4 * self._suspension_force_mult
            damp = 2.0 * d.suspension_damping * math.sqrt(stiff * wheel_mass)
            self.left_spring.damping = damp
            self.right_spring.damping = damp

        torque_mult = self._torque_mult * (1.5 if self._four_wd else 1.0)
        traction_mult = self._traction_mult
        self._wheel_ground_friction = 0.9 * traction_mult

        if in_air:
            self.left_motor.rate = 0
            self.left_motor.max_force = 0
            self.right_motor.rate = 0
            self.right_motor.max_force = 0
            if gas:
                self.chassis.torque += AIR_CONTROL_TORQUE * 10
            if brake:
                self.chassis.torque -= AIR_CONTROL_TORQUE * 10
        else:
            contact_x_pos = (self.left_wheel.position.x + self.right_wheel.position.x) / 2
            zone_type = terrain_manager.get_zone_type_at(contact_x_pos)
            slope_factor = 1.0
            if zone_type == "ice":
                slope_factor = 0.2
            elif zone_type == "mud":
                slope_factor = 0.5

            slope_angle = abs(math.asin(max(-1, min(1, self.chassis.velocity.y / max(0.1, abs(self.chassis.velocity.x) + 0.01)))))
            if slope_angle > STEEP_SLOPE_ANGLE:
                slope_factor *= max(0.1, 1.0 - (slope_angle - STEEP_SLOPE_ANGLE) * 1.5)

            base_force = d.max_torque * torque_mult * 10
            base_rate = d.max_torque * torque_mult * 30
            force_mult = slope_factor
            if gas:
                self.left_motor.rate = base_rate * force_mult
                self.left_motor.max_force = base_force * force_mult
                self.right_motor.rate = base_rate * force_mult
                self.right_motor.max_force = base_force * force_mult
            elif brake:
                self.left_motor.rate = -base_rate * 0.3 * force_mult
                self.left_motor.max_force = base_force * 0.5 * force_mult
                self.right_motor.rate = -base_rate * 0.3 * force_mult
                self.right_motor.max_force = base_force * 0.5 * force_mult
            else:
                self.left_motor.rate = 0
                self.left_motor.max_force = 0
                self.right_motor.rate = 0
                self.right_motor.max_force = 0

        if lean_left:
            self.chassis.torque += d.lean_torque * 15
        if lean_right:
            self.chassis.torque -= d.lean_torque * 15

        self._prev_terrain_contact_left = self.terrain_contact_left
        self._prev_terrain_contact_right = self.terrain_contact_right

    def collect_pickups(self, pickups):
        collected_coins = 0
        collected_fuel = 0
        collected_positions = []
        cp = self.chassis.position
        for pickup in pickups:
            if not pickup.is_active():
                continue
            pp = pymunk.Vec2d(pickup.x, pickup.y)
            dist_w = min(
                (self.left_wheel.position - pp).length,
                (self.right_wheel.position - pp).length,
            )
            if dist_w < self.defn.wheel_radius + pickup.radius + 0.1:
                pickup.collect()
                collected_positions.append((pickup.x, pickup.y, pickup.type))
            elif (cp - pp).length < 0.6:
                pickup.collect()
                collected_positions.append((pickup.x, pickup.y, pickup.type))
            else:
                continue
            if pickup.type == PickupType.COIN:
                collected_coins += 1
            else:
                collected_fuel += pickup.radius
        return collected_coins, collected_fuel, collected_positions

    def dispose(self, world):
        world.remove_constraint(self.left_spring)
        world.remove_constraint(self.right_spring)
        world.remove_constraint(self.left_motor)
        world.remove_constraint(self.right_motor)
        world.remove_shape(self.chassis_shape)
        world.remove_shape(self.left_wheel_shape)
        world.remove_shape(self.right_wheel_shape)
        world.remove_body(self.chassis)
        world.remove_body(self.left_wheel)
        world.remove_body(self.right_wheel)
