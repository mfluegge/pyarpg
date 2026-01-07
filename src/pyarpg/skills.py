import pygame
from pyarpg.assets import IMAGE_DICT

class Projectile(pygame.sprite.Sprite):
    target_range = None

    def __init__(self, image, start_pos, aimed_target_pos, max_distance=500, move_speed=400, muzzle_offset=20, damage=10):
        super().__init__()

        self.image = image

        start_target_offset = aimed_target_pos - start_pos

        if start_target_offset.length() == 0:
            self.direction = pygame.Vector2(1, 1).normalize()
        else:
            self.direction = start_target_offset.normalize()

        # adding muzzle offset
        self.pos = start_pos + muzzle_offset * self.direction
        self.target_pos = self.pos + self.direction * max_distance

        self.rect = self.image.get_rect(center=self.pos)

        self.move_speed = move_speed
        self.damage = damage

        self.expired = False

    def update(self, dt: float, world):
        if self.expired:
            self.kill()

        self.move_to_target(dt)
    
    def _update_pos(self, new_pos):
        self.pos = new_pos
        self.rect.center = self.pos

    def move_to_target(self, dt: float):
        remaining_distance = (self.target_pos - self.pos).length()
        coverable_distance = self.move_speed * dt
        
        if remaining_distance <= coverable_distance:
            self._update_pos(self.target_pos)
            self.expired = True
            return
        
        step = self.direction * coverable_distance
        self._update_pos(self.pos + step)


class FireballProjectile(Projectile):
    target_range = 400
    def __init__(self, start_pos, aimed_target_pos):
        super().__init__(
            image=IMAGE_DICT["fireball"],
            start_pos=start_pos,
            aimed_target_pos=aimed_target_pos,
            move_speed=600,
            damage=15,
            max_distance=500
        )


class ShortFireballProjectile(Projectile):
    target_range = 70

    def __init__(self, start_pos, aimed_target_pos):
        super().__init__(
            image=IMAGE_DICT["fireball"],
            start_pos=start_pos,
            aimed_target_pos=aimed_target_pos,
            move_speed=600,
            damage=15,
            max_distance=80,
            muzzle_offset=10
        )