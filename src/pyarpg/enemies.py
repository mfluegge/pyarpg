import math
import pygame
from pyarpg.assets import SPRITE_DICT
from pyarpg.assets import SOUNDS_DICT
from pyarpg.skills import FireballProjectile
from pyarpg.skills import ShortFireballProjectile
from pyarpg.pickups import DropGlobe

class _BaseEnemy(pygame.sprite.Sprite):
    def __init__(
            self,
            image,
            flash_image,
            start_pos,
            max_hp=100,
            attack=None,
            aggro_range=300,
            aggro_time=3,
            atk_speed=0.5,
            move_speed=250,
            back_off_move_speed=100,
            min_distance_to_player=0,
            max_distance_to_player=100,
        ):
        super().__init__()
        self.max_hp = max_hp
        self.current_hp = max_hp

        self.base_image = image
        self.image = image
        self.flash_image = flash_image
        self.rect = self.base_image.get_rect(center=start_pos)
        self.pos = pygame.Vector2(self.rect.center)

        # Hit Feedback
        self.play_damage_feedback = False
        self.hit_fx_time = 0.0
        self.hit_fx_duration = 0.10  # seconds 

        self.time_since_last_attack = 1000

        # enemy stats
        self.attack = attack
        self.aggro_range = aggro_range
        self.aggro_time = aggro_time
        self.atk_speed = atk_speed
        self.move_speed = move_speed
        self.backoff_move_speed = back_off_move_speed
        self.min_distance_to_player = min_distance_to_player
        self.max_distance_to_player = max_distance_to_player

        self.is_aggro = False
        self.remaining_aggro_duration = 0

    @property
    def hp_percent(self):
        return self.current_hp / self.max_hp
    
    @property
    def cooldown_time(self):
        return 1 / self.atk_speed


    def take_damage(self, n_dmg, world):
        SOUNDS_DICT["enemy_hit_sound"].play()
        self.is_aggro = True
        self.remaining_aggro_duration = self.aggro_time
        new_hp = self.current_hp - n_dmg
        self.current_hp = max(0, new_hp)

        # trigger feedback
        self.hit_fx_time = self.hit_fx_duration
        self.play_damage_feedback = True

        if self.current_hp <= 0:
            world.add_pickup(DropGlobe(self.rect.center))
            self.kill()
            return True

        return False
    
    def _set_aggro(self, player_pos):
        distance = (self.rect.center - player_pos).length()

        if distance <= self.aggro_range:
            self.is_aggro = True
            self.remaining_aggro_duration = self.aggro_time

        if self.remaining_aggro_duration <= 0:
            self.is_aggro = False

    def update(self, dt, world):
        self._set_aggro(world.get_player().pos)

        if self.is_aggro:
            self._launch_attack(dt, world)
            self._move_into_player_range(dt, world)
            self.remaining_aggro_duration -= dt

        if self.play_damage_feedback:
            self._damage_feedback(dt)

    def _update_pos(self, new_pos, world):
        max_w = world.max_width - self.rect.width // 2
        max_h = world.max_height - self.rect.height // 2

        if new_pos[0] > max_w:
            new_pos[0] = max_w

        elif new_pos[0] < self.rect.width // 2:
            new_pos[0] = self.rect.width // 2


        if new_pos[1] > max_h:
            new_pos[1] = max_h

        elif new_pos[1] < self.rect.height // 2:
            new_pos[1] = self.rect.height // 2


        self.pos = new_pos
        self.rect.center = new_pos


    def _move_into_player_range_old(self, dt, world):
        player_pos = world.get_player().pos

        diff = self.pos - player_pos
        direction_from_player = diff.normalize()
        direction_towards_player = -direction_from_player
        distance = diff.length()
        coverable_distance = self.move_speed * dt

        if distance < self.min_distance_to_player:
            step = coverable_distance * direction_from_player
            self._update_pos(self.pos + step)
        
        elif distance > self.max_distance_to_player:
            step = coverable_distance * direction_towards_player
            self._update_pos(self.pos + step)


    def _move_into_player_range(self, dt, world):
        player_pos = world.get_player().pos

        diff = player_pos - self.pos
        dist = diff.length()
        if dist == 0:
            return

        dir_to_player = diff / dist
        dir_from_player = -dir_to_player

        # Base behavior: keep within [min, max]
        desired = pygame.Vector2(0, 0)
        if dist < self.min_distance_to_player:
            desired = dir_from_player
            ms = self.backoff_move_speed
        elif dist > self.max_distance_to_player:
            desired = dir_to_player
            ms = self.move_speed
        else:
            # Inside the band: don't force movement (or optionally orbit / mild noise)
            desired = pygame.Vector2(0, 0)
            ms = self.move_speed

        # Separation behavior: always applied (or only when inside the band)
        sep = self._separation_vec(world, radius=35, strength=0.7)

        steer = desired + sep

        if steer.length_squared() == 0:
            return

        steer = steer.normalize()
        step = steer * (ms * dt)
        self._update_pos(self.pos + step, world)


    def _launch_attack(self, dt, world):
        if self.attack is None:
            return
        
        self.time_since_last_attack += dt

        if self.time_since_last_attack < self.cooldown_time:
            return

        dist = (self.pos - world.get_player().pos).length()

        if dist < self.attack.target_range:
            self.time_since_last_attack = 0
            world.add_active_enemy_skill(self.attack(self.rect.center, world.get_player().pos))
        
    def _damage_feedback(self, dt):
        if self.hit_fx_time > 0:
            self.hit_fx_time = max(0.0, self.hit_fx_time - dt)
            t = 1.0 - (self.hit_fx_time / self.hit_fx_duration)  # 0..1

            # zoom curve: up then back (sine)
            zoom = 1.0 + math.sin(t * math.pi) * 0.12

            # choose flash half the time (or entire time if you want)
            use_flash = t < 0.6
            src = self.flash_image if use_flash else self.base_image

            # scale around center
            center = self.rect.center
            w = max(1, int(src.get_width() * zoom))
            h = max(1, int(src.get_height() * zoom))

            # for pixel art use pygame.transform.scale instead
            self.image = pygame.transform.scale(src, (w, h))
            self.rect = self.image.get_rect(center=center)
        else:
            self.play_damage_feedback = False
            # restore
            if self.image is not self.base_image:
                center = self.rect.center
                self.image = self.base_image
                self.rect = self.image.get_rect(center=center)

    def _separation_vec_old(self, world, radius=40, strength=1.0):
        """Boids-style separation: push away from nearby enemies."""
        neighbors = world.enemies  # SpriteGroup
        r2 = radius * radius

        sep = pygame.Vector2(0, 0)
        count = 0

        for other in neighbors:
            if other is self:
                continue

            # Use pos if available, else rect center
            offset = self.pos - other.pos
            d2 = offset.x * offset.x + offset.y * offset.y

            if 0 < d2 < r2:
                # Weight by inverse distance squared: very strong when too close
                sep += offset / d2
                count += 1

        if count:
            sep /= count  # average

        if sep.length_squared() > 0:
            sep = sep.normalize() * strength

        return sep
    
    def _separation_vec(self, world, radius=40, strength=1.0, edge_margin=60, edge_strength=1.0):
        """Boids-style separation + soft screen-edge avoidance."""
        neighbors = world.enemies
        r2 = radius * radius

        sep = pygame.Vector2(0, 0)
        count = 0

        # --- Enemy separation ---
        for other in neighbors:
            if other is self:
                continue

            offset = self.pos - other.pos
            d2 = offset.x * offset.x + offset.y * offset.y

            if 0 < d2 < r2:
                sep += offset / d2
                count += 1

        if count:
            sep /= count

        # --- Screen edge avoidance ---
        x, y = self.pos
        w = world.max_width
        h = world.max_height

        edge = pygame.Vector2(0, 0)

        # Left edge
        if x < edge_margin:
            d = max(x, 1)
            edge.x += 1.0 / d

        # Right edge
        if x > w - edge_margin:
            d = max(w - x, 1)
            edge.x -= 1.0 / d

        # Top edge
        if y < edge_margin:
            d = max(y, 1)
            edge.y += 1.0 / d

        # Bottom edge
        if y > h - edge_margin:
            d = max(h - y, 1)
            edge.y -= 1.0 / d

        if edge.length_squared() > 0:
            edge = edge.normalize() * edge_strength

        # Combine forces
        sep += edge

        # Final normalize & scale
        if sep.length_squared() > 0:
            sep = sep.normalize() * strength

        return sep



class RangedEnemy(_BaseEnemy):
    def __init__(self, start_pos):
        super().__init__(
            image=SPRITE_DICT["dummy"],
            flash_image=SPRITE_DICT["dummy_flash"],
            start_pos=start_pos,
            attack=FireballProjectile,
            min_distance_to_player=200,
            max_distance_to_player=FireballProjectile.target_range - 5 
        )

class MeleeEnemy(_BaseEnemy):
    def __init__(self, start_pos):
        super().__init__(
            image=SPRITE_DICT["melee"],
            flash_image=SPRITE_DICT["melee_flash"],
            start_pos=start_pos,
            attack=ShortFireballProjectile,
            min_distance_to_player=5,
            max_distance_to_player=30
        )
