import math
import pygame
from pyarpg.assets import SPRITE_DICT
from pyarpg.skills import FireballProjectile
from pyarpg.skills import ShortFireballProjectile

class _BaseEnemy(pygame.sprite.Sprite):
    def __init__(
            self,
            image,
            flash_image,
            start_pos,
            max_hp=100,
            attack=None,
            aggro_range=300,
            aggro_time=5,
            atk_speed=0.5,
            move_speed=250
        ):
        super().__init__()
        self.max_hp = max_hp
        self.current_hp = max_hp

        self.base_image = image
        self.image = image
        self.flash_image = flash_image
        self.rect = self.base_image.get_rect(center=start_pos)

        # Hit Feedback
        self.play_damage_feedback = False
        self.hit_fx_time = 0.0
        self.hit_fx_duration = 0.10  # seconds 

        self.time_since_last_attack = 1000

        # enemy stats
        self.attack = attack
        self.aggro_range = aggro_range
        self.atk_speed = atk_speed

        self.is_aggro = False


    @property
    def hp_percent(self):
        return self.current_hp / self.max_hp
    
    @property
    def cooldown_time(self):
        return 1 / self.atk_speed


    def take_damage(self, n_dmg):
        new_hp = self.current_hp - n_dmg
        self.current_hp = max(0, new_hp)

        # trigger feedback
        self.hit_fx_time = self.hit_fx_duration
        self.play_damage_feedback = True

        if self.current_hp <= 0:
            self.kill()
            return True

        return False
    
    def _set_aggro(self, player_pos):
        if self.is_aggro:
            return
        
        distance = (self.rect.center - player_pos).length()

        if distance <= self.aggro_range:
            self.is_aggro = True

    def update(self, dt, world):
        self._set_aggro(world.get_player().pos)

        if self.is_aggro:
            self._launch_attack(dt, world)

        if self.play_damage_feedback:
            self._damage_feedback(dt)


    def _launch_attack(self, dt, world):
        if self.attack is None:
            return
        
        self.time_since_last_attack += dt

        if self.time_since_last_attack < self.cooldown_time:
            return

        dist = (self.rect.center - world.get_player().pos).length()

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


class RangedEnemy(_BaseEnemy):
    def __init__(self, start_pos):
        super().__init__(
            image=SPRITE_DICT["dummy"],
            flash_image=SPRITE_DICT["dummy_flash"],
            start_pos=start_pos,
            attack=FireballProjectile
        )

class MeleeEnemy(_BaseEnemy):
    def __init__(self, start_pos):
        super().__init__(
            image=SPRITE_DICT["melee"],
            flash_image=SPRITE_DICT["melee_flash"],
            start_pos=start_pos,
            attack=ShortFireballProjectile
        )
