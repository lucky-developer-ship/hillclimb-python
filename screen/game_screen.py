import datetime
import math

import pygame

import assets
import sprites as sp
from background import ParallaxBackground
from constants import (
    FUEL_CAN_RESTORE,
    FUEL_CONSUMPTION_RATE,
    FUEL_IDLE_CONSUMPTION,
    MAX_PHYSICS_STEPS,
    PHYSICS_DT,
    PIXELS_PER_METER,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
)
from data.game_data import STAGES, get_upgrades, get_vehicle
from entity.pickup import PickupType
from entity.terrain import TerrainManager
from entity.vehicle import Vehicle
from ghost import GhostPlayer, GhostRecorder
from particle_system import ParticleSystem
from physics.world import PhysicsWorld
from save_data import LEAGUE_REWARDS, get_daily_seed, get_league
from system.camera import GameCamera
from system.input_manager import InputManager


def _to_screen(world_x, world_y, camera_x, camera_y):
    sx = (world_x - camera_x) * PIXELS_PER_METER + SCREEN_WIDTH // 2
    sy = (camera_y - world_y) * PIXELS_PER_METER + SCREEN_HEIGHT // 2
    return int(sx), int(sy)


class GameScreen:
    def __init__(self, game, stage, seed=None, daily=False):
        self.game = game
        self.stage = stage
        self.daily = daily
        self.physics_world = PhysicsWorld()
        self.input_manager = InputManager()
        self.camera = GameCamera()
        self.hud_font = assets.get_font(20)
        self.hud_font_small = assets.get_font(16)
        self.particles = ParticleSystem()
        self.parallax = ParallaxBackground(stage)
        actual_seed = get_daily_seed() if daily else seed
        self.terrain_manager = TerrainManager(stage, self.physics_world.space, seed=actual_seed)
        if seed:
            self.terrain_manager.seed = seed
        self.terrain_manager.update(3, self.physics_world.space)
        self.ghost_recorder = GhostRecorder(stage.id)
        self.ghost_player = GhostPlayer(stage.id)
        spawn_y = max(
            (self.terrain_manager.get_height_at(3) or 2.0) + 2.0,
            5.0,
        )

        vehicle_id = game.save_data.get_selected_vehicle_id()
        v_def = get_vehicle(vehicle_id)
        self.vehicle = Vehicle(self.physics_world, v_def, (3, spawn_y))
        upgrades = get_upgrades(vehicle_id)
        levels = [game.save_data.get_upgrade_level(vehicle_id, u.id) for u in upgrades]
        self.vehicle.apply_upgrades(upgrades, levels)
        self.camera.reset()
        self.fuel = self.vehicle.get_fuel_max()
        self.coins = 0
        self.distance = 0.0
        self.paused = False
        self.game_over = False
        self.game_over_timer = 0.0
        self.time = 0.0
        self.stage_complete = False
        self.stage_complete_timer = 0.0
        self.results_choice = 0
        self.results_options = self._compute_results_options()
        self.pause_choice = 0
        self.pause_options = ["Resume", "Restart", "Quit to Menu"]
        self.collect_animations = []

        self.tutorial_timer = 4.0
        self._was_in_air = False
        self.game.sound_manager.stop_music()
        self.game.sound_manager.start_engine()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.stage_complete:
                    self.game.sound_manager.stop_engine()
                    self.ghost_recorder.save()
                    self._apply_daily_rewards()
                    self.game.save_data.add_coins(self.coins)
                    self.game.save_data.update_best_distance(self.stage.id, int(self.distance))
                    self.game.save_data.save()
                    self.game.set_screen("menu")
                    return
                if self.game_over:
                    self._quick_restart()
                    return
                self.paused = not self.paused
                if self.paused:
                    self.game.sound_manager.play_sfx("click")
            if self.paused:
                if event.key == pygame.K_UP:
                    self.pause_choice = (self.pause_choice - 1) % len(self.pause_options)
                    self.game.sound_manager.play_sfx("click")
                elif event.key == pygame.K_DOWN:
                    self.pause_choice = (self.pause_choice + 1) % len(self.pause_options)
                    self.game.sound_manager.play_sfx("click")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._handle_pause_choice()
            if self.game_over and not self.paused:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                    self._quick_restart()
                    return
            if self.stage_complete:
                opts = self._compute_results_options()
                if event.key == pygame.K_UP:
                    self.results_choice = (self.results_choice - 1) % len(opts)
                    self.game.sound_manager.play_sfx("click")
                elif event.key == pygame.K_DOWN:
                    self.results_choice = (self.results_choice + 1) % len(opts)
                    self.game.sound_manager.play_sfx("click")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._handle_results_choice()

    def _quick_restart(self):
        self.game.sound_manager.stop_engine()
        self.game.save_data.add_coins(self.coins)
        self.game.save_data.update_best_distance(self.stage.id, int(self.distance))
        self.game.save_data.save()
        self.game.set_screen("game", stage=self.stage, seed=getattr(self.terrain_manager, "seed", None))

    def _handle_pause_choice(self):
        if self.pause_choice == 0:
            self.paused = False
        elif self.pause_choice == 1:
            self.game.sound_manager.stop_engine()
            self.game.save_data.add_coins(self.coins)
            self.game.save_data.save()
            self.game.set_screen("game", stage=self.stage)
        elif self.pause_choice == 2:
            self.game.sound_manager.stop_engine()
            self.game.save_data.add_coins(self.coins)
            self.game.save_data.save()
            self.game.set_screen("menu")

    def _apply_daily_rewards(self):
        if not self.daily:
            return
        trophies = max(10, int(self.distance) * 2)
        self.game.save_data.trophies += trophies
        league = get_league(self.game.save_data.trophies)
        daily_bonus = LEAGUE_REWARDS.get(league, 100)
        self.game.save_data.add_coins(daily_bonus)
        self.game.save_data.last_daily_date = datetime.date.today().isoformat()

    def _compute_results_options(self):
        next_idx = 0
        for i, s in enumerate(STAGES):
            if s.id == self.stage.id and i + 1 < len(STAGES):
                next_idx = i + 1
                break
        return ["NEXT STAGE", "MENU"] if next_idx > 0 else ["MENU"]

    def _handle_results_choice(self):
        self.game.sound_manager.stop_engine()
        self.ghost_recorder.save()
        self._apply_daily_rewards()
        self.game.save_data.save()
        options = self._compute_results_options()
        choice = self.results_choice if self.results_choice < len(options) else 0
        if choice == 0 and len(options) > 1:
            next_idx = 0
            for i, s in enumerate(STAGES):
                if s.id == self.stage.id and i + 1 < len(STAGES):
                    next_idx = i + 1
                    break
            if next_idx > 0:
                self.game.set_screen("game", stage=STAGES[next_idx])
            else:
                self.game.set_screen("stage_select")
        else:
            self.game.set_screen("menu")

    def update(self, dt):
        self.input_manager.update()
        if self.stage_complete:
            self.stage_complete_timer += dt
            return
        if self.game_over and not self.paused:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.sound_manager.stop_engine()
                self.game.save_data.add_coins(self.coins)
                self.game.save_data.update_best_distance(self.stage.id, int(self.distance))
                self.ghost_recorder.save()
                self._apply_daily_rewards()
                self.game.save_data.save()
                self.game.set_screen("menu")
            return
        if self.paused:
            return
        if self.tutorial_timer > 0:
            self.tutorial_timer -= dt
        self.time += dt
        steps = min(int(dt / PHYSICS_DT) + 1, MAX_PHYSICS_STEPS)
        sub_dt = dt / steps
        for _ in range(steps):
            self._update_physics(sub_dt)
        self._update_game_state(dt)
        self.particles.update(dt, self.camera.x, self.camera.y)
        for anim in self.collect_animations:
            anim["timer"] -= dt
        self.collect_animations = [a for a in self.collect_animations if a["timer"] > 0]

    def _update_physics(self, dt):
        gas = self.input_manager.is_gas_pressed()
        brake = self.input_manager.is_brake_pressed()
        ll = self.input_manager.is_lean_left()
        lr = self.input_manager.is_lean_right()
        self.vehicle.update(dt, gas, brake, ll, lr, self.terrain_manager)
        self.physics_world.step(dt)

    def _update_game_state(self, dt):
        v_pos = self.vehicle.get_position()
        new_dist = v_pos.position.x - 3
        if new_dist > self.distance:
            self.distance = new_dist
        gas = self.input_manager.is_gas_pressed()
        brake = self.input_manager.is_brake_pressed()
        fuel_mult = self.vehicle.get_fuel_consumption_mult()
        if gas or brake:
            self.fuel -= FUEL_CONSUMPTION_RATE * dt * fuel_mult
        else:
            self.fuel -= FUEL_IDLE_CONSUMPTION * dt * fuel_mult
        if self.fuel <= 0:
            self.fuel = 0
            self.game_over = True
            self.game_over_timer = 0
        self.vehicle.check_game_over(dt)
        if self.vehicle.is_game_over():
            self.game_over = True
            self.game_over_timer = 0
        collected_coins, collected_fuel, collected_positions = self.vehicle.collect_pickups(
            self.terrain_manager.get_pickups()
        )
        if collected_coins > 0:
            self.game.sound_manager.play_sfx("coin")
            for px, py, ptype in collected_positions:
                if ptype == PickupType.COIN:
                    self.particles.emit_coin_sparkle(px, py)
                    self.collect_animations.append({
                        "x": px, "y": py, "timer": 0.8, "type": "coin"
                    })
        if collected_fuel > 0:
            self.game.sound_manager.play_sfx("fuel")
            for px, py, ptype in collected_positions:
                if ptype == PickupType.FUEL:
                    self.collect_animations.append({
                        "x": px, "y": py, "timer": 0.8, "type": "fuel"
                    })
        self.coins += collected_coins
        self.fuel = min(self.vehicle.get_fuel_max(), self.fuel + collected_fuel * FUEL_CAN_RESTORE)
        vel_x = self.vehicle.get_position().velocity.x
        self.ghost_recorder.record(v_pos.position.x, v_pos.position.y, v_pos.angle)
        self.terrain_manager.update(v_pos.position.x, self.physics_world.space, dt)
        self.camera.update(dt, v_pos, vel_x)

        self.game.sound_manager.update_engine(gas or brake)
        left_rpm = abs(self.vehicle.left_wheel.angular_velocity) if hasattr(self.vehicle, "left_wheel") else 0
        right_rpm = abs(self.vehicle.right_wheel.angular_velocity) if hasattr(self.vehicle, "right_wheel") else 0
        avg_rpm = (left_rpm + right_rpm) / 2
        self.game.sound_manager.update_engine_pitch(avg_rpm, gas or brake)

        if self.distance >= self.stage.completion_distance and not self.stage_complete:
            self.stage_complete = True
            self.stage_complete_timer = 0.0
            self.results_choice = 0
            self.game.sound_manager.play_sfx("stage_complete")
            self.game.save_data.update_best_distance(self.stage.id, int(self.distance))
            next_idx = 0
            for i, s in enumerate(STAGES):
                if s.id == self.stage.id and i + 1 < len(STAGES):
                    next_idx = i + 1
                    break
            if next_idx > 0:
                self.game.save_data.unlock_stage(next_idx)
                self.game.save_data.save()

        if self.game_over and self.game_over_timer < 0.1:
            self.game.sound_manager.play_sfx("crash")
            self.camera.shake(0.3, 0.6)

        in_air_now = not (self.vehicle.terrain_contact_left or self.vehicle.terrain_contact_right)
        if self._was_in_air and not in_air_now:
            vel_y = abs(self.vehicle.chassis.velocity.y)
            if vel_y > 3.0:
                intensity = min(0.5, vel_y * 0.03)
                self.camera.shake(intensity, max(0.15, vel_y * 0.02))
        self._was_in_air = in_air_now

    def render(self, surface):
        surface.fill((0, 0, 0))
        cam = self.camera
        half_w = VIEWPORT_WIDTH / 2
        half_h = VIEWPORT_HEIGHT / 2
        left = cam.x - half_w
        right = cam.x + half_w
        top = cam.y + half_h
        bottom = cam.y - half_h

        self.parallax.draw(surface, self.camera.x, self.camera.y)
        self._draw_mountains(surface, left, top, right, bottom)
        self._draw_terrain(surface, left, top, right, bottom)
        self._draw_terrain_zones(surface, left, top, right, bottom)
        self._draw_objects(surface, left, top, right, bottom)
        self._draw_pickups(surface, left, top, right, bottom)
        self._draw_ghost(surface)
        self._draw_vehicle(surface)
        self.particles.draw(surface, self.camera.x, self.camera.y)
        self._draw_collect_animations(surface)
        self._draw_hud(surface)
        self._draw_tutorial(surface)
        if self.stage_complete:
            self._draw_results(surface)

    def _draw_mountains(self, surface, left, top, right, bottom):
        m_base = self.stage.base_height + 1
        m_heights = [3, 5, 4, 6, 3.5, 7, 4, 5, 3, 6, 4.5, 5, 3]
        seg_w = 6.0
        m_offset = (self.camera.x * 0.1) % (seg_w * (len(m_heights) - 1))
        for i in range(len(m_heights) - 1):
            x0 = left + i * seg_w - m_offset
            x1 = x0 + seg_w
            y0 = m_base + m_heights[i]
            y1 = m_base + m_heights[i + 1]
            if x1 < left - 2 or x0 > right + 2:
                continue
            pts = [
                _to_screen(x0, m_base, self.camera.x, self.camera.y),
                _to_screen(x1, m_base, self.camera.x, self.camera.y),
                _to_screen(x0, y0, self.camera.x, self.camera.y),
            ]
            if len(pts) == 3:
                pygame.draw.polygon(surface, self.stage.mountain_color, pts)
            pts2 = [
                _to_screen(x1, m_base, self.camera.x, self.camera.y),
                _to_screen(x1, y1, self.camera.x, self.camera.y),
                _to_screen(x0, y0, self.camera.x, self.camera.y),
            ]
            if len(pts2) == 3:
                pygame.draw.polygon(surface, self.stage.mountain_color, pts2)

    def _draw_terrain(self, surface, left, top, right, bottom):
        ground_fill_y = self.stage.base_height - 8
        for chunk in self.terrain_manager.get_chunks():
            pts = chunk.get_surface_points()
            if not pts or len(pts) < 2:
                continue
            if pts[0][0] > right + 1 or pts[-1][0] < left - 1:
                continue
            for i in range(len(pts) - 1):
                x0, y0 = pts[i]
                x1, y1 = pts[i + 1]
                p0 = _to_screen(x0, y0, self.camera.x, self.camera.y)
                p1 = _to_screen(x1, y1, self.camera.x, self.camera.y)
                p_bottom = _to_screen(x1, ground_fill_y, self.camera.x, self.camera.y)
                p_bottom2 = _to_screen(x0, ground_fill_y, self.camera.x, self.camera.y)
                pygame.draw.polygon(surface, self.stage.terrain_color, [p0, p1, p_bottom, p_bottom2])
                pygame.draw.line(surface, self.stage.grass_color, p0, p1, 3)
                gn_y = _to_screen(x0, y0 + 0.12, self.camera.x, self.camera.y)
                gn_y2 = _to_screen(x1, y1 + 0.12, self.camera.x, self.camera.y)
                pygame.draw.line(surface, self.stage.grass_line_color, gn_y, gn_y2, 2)

    def _draw_terrain_zones(self, surface, left, top, right, bottom):
        if not hasattr(self, "_zone_cache"):
            self._zone_cache = {}
        chunks = self.terrain_manager.get_chunks()
        for chunk in chunks:
            pts = chunk.get_surface_points()
            if not pts or len(pts) < 2:
                continue
            if pts[0][0] > right + 1 or pts[-1][0] < left - 1:
                continue
            if not hasattr(chunk, "segment_frictions"):
                continue
            for mid_x, fric, ztype in chunk.segment_frictions:
                if mid_x < left - 2 or mid_x > right + 2:
                    continue
                for i in range(len(pts) - 1):
                    x0, y0 = pts[i]
                    x1, y1 = pts[i + 1]
                    if x0 <= mid_x <= x1:
                        p0 = _to_screen(x0, y0, self.camera.x, self.camera.y)
                        p1 = _to_screen(x1, y1, self.camera.x, self.camera.y)
                        w = p1[0] - p0[0] + 4
                        cache_key = (ztype, w)
                        overlay = self._zone_cache.get(cache_key)
                        if overlay is None:
                            overlay = pygame.Surface((max(1, w), 8), pygame.SRCALPHA)
                            if ztype == "ice":
                                overlay.fill((180, 210, 240, 80))
                            else:
                                overlay.fill((90, 60, 30, 100))
                            self._zone_cache[cache_key] = overlay
                        surface.blit(overlay, (p0[0], p0[1] - 4))
                        break

    def _draw_objects(self, surface, left, top, right, bottom):
        for obj in self.terrain_manager.get_objects():
            if not obj.is_active() or obj.body is None:
                continue
            px, py = obj.body.position.x, obj.body.position.y
            if px < left - 2 or px > right + 2:
                continue
            sp = _to_screen(px, py, self.camera.x, self.camera.y)
            angle = obj.body.angle if obj.body else 0
            if obj.type == "crate":
                hw = int(obj.width * PIXELS_PER_METER / 2)
                hh = int(obj.height * PIXELS_PER_METER / 2)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                verts = []
                for lx, ly in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
                    rx = lx * cos_a - ly * sin_a
                    ry = lx * sin_a + ly * cos_a
                    verts.append((sp[0] + int(rx), sp[1] + int(ry)))
                if len(verts) == 4:
                    pygame.draw.polygon(surface, (140, 90, 50), verts)
                    pygame.draw.polygon(surface, (100, 60, 30), verts, 2)
                    pygame.draw.line(surface, (80, 50, 20), (verts[0][0], verts[0][1]), (verts[2][0], verts[2][1]), 2)
            elif obj.type == "log":
                hw = int(obj.width * PIXELS_PER_METER / 2)
                hh = int(obj.height * PIXELS_PER_METER / 2)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                verts = []
                for lx, ly in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
                    rx = lx * cos_a - ly * sin_a
                    ry = lx * sin_a + ly * cos_a
                    verts.append((sp[0] + int(rx), sp[1] + int(ry)))
                if len(verts) == 4:
                    pygame.draw.polygon(surface, (100, 70, 40), verts)
                    pygame.draw.polygon(surface, (70, 45, 20), verts, 2)
                    y_pos = (verts[0][1] + verts[1][1] + verts[2][1] + verts[3][1]) // 4
                    pygame.draw.ellipse(surface, (80, 55, 30), (sp[0] - hw, y_pos - 2, hw * 2, 4), 1)
            elif obj.type == "rock":
                r = int(obj.width / 2 * PIXELS_PER_METER)
                gray = 100 + int(50 * math.sin(px * 3 + py * 2))
                pygame.draw.circle(surface, (gray, gray - 10, gray - 20), sp, r)
                pygame.draw.circle(surface, (gray - 30, gray - 35, gray - 40), sp, r, 2)
                hl = (sp[0] - int(r * 0.3), sp[1] - int(r * 0.3))
                pygame.draw.circle(surface, (gray + 40, gray + 35, gray + 30), hl, int(r * 0.3))

    def _draw_pickups(self, surface, left, top, right, bottom):
        coin_surf = sp.get_coin_sprite()
        fuel_surf = sp.get_fuel_sprite()
        if not hasattr(self, "_coin_alpha_cache"):
            self._coin_alpha_cache = {}
        for pickup in self.terrain_manager.get_pickups():
            if not pickup.is_active():
                continue
            px, py = pickup.get_position()
            if px < left - 1 or px > right + 1:
                continue
            bob = math.sin(self.time * 3 + px * 2) * 0.08
            screen_pos = _to_screen(px, py + bob, self.camera.x, self.camera.y)
            if pickup.type == PickupType.COIN:
                shimmer = 0.8 + 0.2 * math.sin(px * 2 + self.time * 3)
                alpha = int(shimmer * 255)
                cr = coin_surf.get_width() // 2
                if alpha >= 254:
                    surface.blit(coin_surf, (screen_pos[0] - cr, screen_pos[1] - cr))
                else:
                    coin_draw = self._coin_alpha_cache.get(alpha)
                    if coin_draw is None:
                        coin_draw = coin_surf.copy()
                        coin_draw.set_alpha(alpha)
                        self._coin_alpha_cache[alpha] = coin_draw
                    surface.blit(coin_draw, (screen_pos[0] - cr, screen_pos[1] - cr))
            else:
                fr = fuel_surf.get_width() // 2
                surface.blit(fuel_surf, (screen_pos[0] - fr, screen_pos[1] - fr))

    def _draw_ghost(self, surface):
        if not self.ghost_player.has_data():
            return
        ghost = self.ghost_player.get_state(self.time * 60)
        if ghost is None:
            return
        if not hasattr(self, "_ghost_surf"):
            gw = 1.6 * PIXELS_PER_METER
            gh = 0.4 * PIXELS_PER_METER
            self._ghost_surf = pygame.Surface((int(gw) + 4, int(gh) + 4), pygame.SRCALPHA)
            cx, cy = self._ghost_surf.get_width() // 2, self._ghost_surf.get_height() // 2
            rect = pygame.Rect(0, 0, int(gw), int(gh))
            rect.center = (cx, cy)
            pygame.draw.rect(self._ghost_surf, (100, 180, 255, 80), rect, border_radius=4)
        sp_x = int((ghost["x"] - self.camera.x) * PIXELS_PER_METER + SCREEN_WIDTH // 2)
        sp_y = int((self.camera.y - ghost["y"]) * PIXELS_PER_METER + SCREEN_HEIGHT // 2)
        rot = pygame.transform.rotate(self._ghost_surf, math.degrees(ghost["angle"]))
        r = rot.get_rect(center=(sp_x, sp_y))
        surface.blit(rot, r)

    def _draw_vehicle(self, surface):
        v = self.vehicle
        d = v.defn
        ch = v.chassis

        body_surf = sp.get_car_body(d)
        bw, bh = body_surf.get_size()
        sp_x = int((ch.position.x - self.camera.x) * PIXELS_PER_METER + SCREEN_WIDTH // 2 - bw // 2)
        sp_y = int((self.camera.y - ch.position.y) * PIXELS_PER_METER + SCREEN_HEIGHT // 2 - bh // 2)
        rot_body = pygame.transform.rotate(body_surf, math.degrees(ch.angle))
        rot_rect = rot_body.get_rect(center=(sp_x + bw // 2, sp_y + bh // 2))
        surface.blit(rot_body, rot_rect)

        self._draw_wheel(surface, v.left_wheel, d.wheel_radius)
        self._draw_wheel(surface, v.right_wheel, d.wheel_radius)

        gas = self.input_manager.is_gas_pressed() or self.input_manager.is_brake_pressed()
        speed = abs(v.chassis.velocity.length)
        if gas:
            for w in [v.left_wheel, v.right_wheel]:
                wx = w.position.x - math.cos(w.angle) * d.wheel_radius * 1.1
                wy = w.position.y - math.sin(w.angle) * d.wheel_radius * 1.1
                self.particles.emit_exhaust(wx, wy, min(3.0, speed * 0.1 + 0.5))

        if v.terrain_contact_left or v.terrain_contact_right:
            for w in [v.left_wheel, v.right_wheel]:
                if (w is v.left_wheel and v.terrain_contact_left) or (w is v.right_wheel and v.terrain_contact_right):
                    wx = w.position.x + math.cos(w.angle) * d.wheel_radius
                    wy = w.position.y + math.sin(w.angle) * d.wheel_radius
                    spd = abs(w.angular_velocity) * d.wheel_radius
                    self.particles.emit_dust(wx, wy, speed=spd + 0.5, intensity=min(2.0, abs(v.chassis.velocity.x) * 0.05))
                    self.particles.emit_dirt_trail(wx, wy, spd, 0.5 + 0.5 * (v.terrain_contact_left or v.terrain_contact_right))

    def _draw_wheel(self, surface, wheel, radius):
        wheel_surf = sp.get_wheel(radius)
        ww, wh = wheel_surf.get_size()
        sp_x = int((wheel.position.x - self.camera.x) * PIXELS_PER_METER + SCREEN_WIDTH // 2 - ww // 2)
        sp_y = int((self.camera.y - wheel.position.y) * PIXELS_PER_METER + SCREEN_HEIGHT // 2 - wh // 2)
        rot_wheel = pygame.transform.rotate(wheel_surf, math.degrees(wheel.angle))
        rot_rect = rot_wheel.get_rect(center=(sp_x + ww // 2, sp_y + wh // 2))
        surface.blit(rot_wheel, rot_rect)

    def _draw_collect_animations(self, surface):
        for anim in self.collect_animations:
            progress = 1 - anim["timer"] / 0.8
            alpha = int((1 - progress) * 255)
            y_offset = -progress * 30
            sp = _to_screen(anim["x"], anim["y"] + y_offset / PIXELS_PER_METER, self.camera.x, self.camera.y)
            color = (255, 215, 0) if anim["type"] == "coin" else (0, 255, 100)
            txt = self.hud_font_small.render("+1" if anim["type"] == "coin" else "+F", True, color)
            txt.set_alpha(max(0, alpha))
            surface.blit(txt, (sp[0] - txt.get_width() // 2, sp[1] - 20))

    def _draw_hud(self, surface):
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT

        hud_bg = pygame.Surface((w, 56), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 160))
        surface.blit(hud_bg, (0, h - 56))

        line_y = h - 56
        pygame.draw.line(surface, (255, 255, 255, 40), (0, line_y), (w, line_y), 1)

        col1_x = 12
        col2_x = w // 2 - 60
        col3_x = w // 2 + 40

        fuel_label = self.hud_font_small.render("FUEL", True, (180, 180, 200))
        surface.blit(fuel_label, (col1_x, h - 50))
        bar_x = col1_x + 50
        bar_y = h - 46
        bar_w = 120
        bar_h = 14
        ratio = self.fuel / self.vehicle.get_fuel_max()
        low_fuel = ratio < 0.2
        flash = low_fuel and int(self.time * 4) % 2 == 0
        border_color = (255, 50, 50) if flash else (40, 40, 50)
        pygame.draw.rect(surface, border_color, (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=3)
        pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fw = int(bar_w * ratio)
        if ratio > 0.3:
            fc = (0, 210, 70)
        else:
            fc = (220, 50, 50)
        if fw > 0:
            pygame.draw.rect(surface, fc, (bar_x, bar_y, fw, bar_h), border_radius=3)
        pct_text = self.hud_font_small.render(f"{int(self.fuel)}%", True, (255, 255, 255))
        surface.blit(pct_text, (bar_x + bar_w + 6, h - 50))
        if low_fuel:
            warn = self.hud_font_small.render("LOW FUEL!", True, (255, 80, 80) if flash else (180, 40, 40))
            surface.blit(warn, (col1_x, h - 30))

        coins_text = self.hud_font.render(f"{self.coins}", True, (255, 215, 0))
        surface.blit(coins_text, (col2_x, h - 44))
        coin_label = self.hud_font_small.render("COINS", True, (180, 180, 200))
        surface.blit(coin_label, (col2_x, h - 26))

        dist_text = self.hud_font.render(f"{int(self.distance)}m", True, (255, 255, 255))
        surface.blit(dist_text, (col3_x, h - 44))
        dist_label = self.hud_font_small.render("DIST", True, (180, 180, 200))
        surface.blit(dist_label, (col3_x, h - 26))

        speed = abs(self.vehicle.chassis.velocity.length) if hasattr(self.vehicle, "chassis") else 0
        speed_text = self.hud_font_small.render(f"{speed:.0f} m/s", True, (200, 200, 255))
        surface.blit(speed_text, (col3_x + 120, h - 44))

        goal_text = self.hud_font_small.render(f"GOAL: {self.stage.completion_distance}m", True, (180, 180, 100))
        surface.blit(goal_text, (col3_x, h - 12))

        if self.vehicle.get_flips() > 0:
            flip_text = self.hud_font_small.render(f"FLIPS: {self.vehicle.get_flips()}", True, (255, 200, 100))
            surface.blit(flip_text, (col3_x + 180, h - 44))

        if self.paused:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            surface.blit(overlay, (0, 0))
            panel_w, panel_h = 300, 220
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((20, 20, 35, 230))
            surface.blit(panel, (w // 2 - panel_w // 2, h // 2 - panel_h // 2))
            pygame.draw.rect(surface, (60, 60, 80), (w // 2 - panel_w // 2, h // 2 - panel_h // 2, panel_w, panel_h), 2, border_radius=4)
            pt = self.hud_font.render("PAUSED", True, (255, 255, 255))
            surface.blit(pt, (w // 2 - pt.get_width() // 2, h // 2 - 80))
            for i, opt in enumerate(self.pause_options):
                c = (255, 255, 255) if i == self.pause_choice else (140, 140, 160)
                ot = self.hud_font.render(opt, True, c)
                ox = w // 2 - ot.get_width() // 2
                surface.blit(ot, (ox, h // 2 - 30 + i * 45))

        if self.game_over:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            surface.blit(overlay, (0, 0))
            panel_w, panel_h = 320, 220
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((30, 10, 10, 230))
            surface.blit(panel, (w // 2 - panel_w // 2, h // 2 - panel_h // 2))
            pygame.draw.rect(surface, (80, 30, 30), (w // 2 - panel_w // 2, h // 2 - panel_h // 2, panel_w, panel_h), 2, border_radius=4)
            gt = self.hud_font.render("GAME OVER", True, (255, 70, 70))
            surface.blit(gt, (w // 2 - gt.get_width() // 2, h // 2 - 80))
            d_text = self.hud_font_small.render(f"Distance: {int(self.distance)}m", True, (200, 200, 200))
            surface.blit(d_text, (w // 2 - 80, h // 2 - 30))
            c_text = self.hud_font_small.render(f"Coins: {self.coins}", True, (200, 200, 200))
            surface.blit(c_text, (w // 2 - 80, h // 2))
            restart_text = self.hud_font_small.render("Press R / ENTER to Restart", True, (180, 180, 100))
            surface.blit(restart_text, (w // 2 - restart_text.get_width() // 2, h // 2 + 40))
            esc_text = self.hud_font_small.render("Press ESC to Quit", True, (150, 150, 150))
            surface.blit(esc_text, (w // 2 - esc_text.get_width() // 2, h // 2 + 65))

    def _draw_tutorial(self, surface):
        if self.tutorial_timer <= 0:
            return
        alpha = min(255, int(self.tutorial_timer / 1.0 * 255))
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, int(100 * alpha / 255)))
        surface.blit(s, (0, 0))
        controls = [
            "RIGHT / D   -  Accelerate",
            "LEFT / A     -  Brake",
            "UP / W        -  Lean Forward",
            "DOWN / S     -  Lean Backward",
            "ESC             -  Pause",
        ]
        y_start = SCREEN_HEIGHT // 2 - 60
        pygame.draw.rect(surface, (0, 0, 0, int(120 * alpha / 255)), (0, y_start - 30, SCREEN_WIDTH, len(controls) * 30 + 40))
        for i, line in enumerate(controls):
            txt = self.hud_font_small.render(line, True, (255, 255, 255))
            txt.set_alpha(alpha)
            surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, y_start + i * 25))

    def _draw_results(self, surface):
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        panel_w, panel_h = 340, 260
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 30, 10, 230))
        surface.blit(panel, (w // 2 - panel_w // 2, h // 2 - panel_h // 2))
        pygame.draw.rect(surface, (40, 100, 40), (w // 2 - panel_w // 2, h // 2 - panel_h // 2, panel_w, panel_h), 2, border_radius=4)

        ct = self.hud_font.render("STAGE COMPLETE!", True, (0, 255, 100))
        surface.blit(ct, (w // 2 - ct.get_width() // 2, h // 2 - 100))

        d_text = self.hud_font_small.render(f"Distance: {int(self.distance)}m", True, (220, 220, 220))
        surface.blit(d_text, (w // 2 - 70, h // 2 - 50))
        c_text = self.hud_font_small.render(f"Coins: {self.coins}", True, (220, 220, 220))
        surface.blit(c_text, (w // 2 - 70, h // 2 - 20))

        options = self._compute_results_options()
        if self.results_choice >= len(options):
            self.results_choice = 0
        for i, opt in enumerate(options):
            c = (255, 255, 255) if i == self.results_choice else (140, 140, 160)
            ot = self.hud_font.render(opt, True, c)
            surface.blit(ot, (w // 2 - ot.get_width() // 2, h // 2 + 20 + i * 45))

    def dispose(self):
        self.game.sound_manager.stop_engine()
        if not self.game.sound_manager.muted:
            self.game.sound_manager.play_music()
        if hasattr(self, "_coin_alpha_cache"):
            self._coin_alpha_cache.clear()
        if hasattr(self, "_zone_cache"):
            self._zone_cache.clear()
        sp.clear_cache()
        assets.clear_font_cache()
