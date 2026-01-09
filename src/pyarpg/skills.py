import pygame
from pyarpg.assets import SPRITE_DICT

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
            image=SPRITE_DICT["fireball"],
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
            image=SPRITE_DICT["fireball"],
            start_pos=start_pos,
            aimed_target_pos=aimed_target_pos,
            move_speed=600,
            damage=15,
            max_distance=80,
            muzzle_offset=10
        )

class GroundCircleAOESkill(pygame.sprite.Sprite):
    def __init__(self, image, aimed_target_pos, max_distance=500, radius=30, damage=10, duration=0.2):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect(center=aimed_target_pos)
        self.pos = aimed_target_pos
        self.radius = radius
        self.damage = damage

        self.expired = False

        self.duration = duration
        self.remaining_duration = duration
        
        self.frames_active = 0

    def update(self, dt, world):
        self.frames_active += 1
        self.remaining_duration -= dt

        if self.remaining_duration <= 0:
            self.kill()

    def get_collisions(self, entities):
        if self.frames_active >= 2:
            return []
    
        return [
            e 
            for e in entities
            if (self.pos[0] - e.rect.center[0]) ** 2 + (self.pos[1] - e.rect.center[1]) ** 2 <= self.radius * self.radius
        ]


class BlueCircleAOESkill(GroundCircleAOESkill):
    def __init__(self, aimed_target_pos, radius=120):
        image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(image, (40, 92, 196, 100), (radius, radius), radius)

        super().__init__(
            image=image,
            aimed_target_pos=aimed_target_pos,
            radius=radius,
            damage=20
        )


class RingOfFire(pygame.sprite.Sprite):
    def __init__(self, aimed_target_pos, duration=0.3):
        super().__init__()
    
        self.sprite_sheet = SPRITE_DICT["ring_of_fire"]
        self.width_per_frame = 256
        self.height = 256
        self.n_frames = 12

        self.frames = []
        for i in range(self.n_frames):
            rect = pygame.Rect(i * self.width_per_frame, 0, self.width_per_frame, self.height)
            
            self.frames.append(self.sprite_sheet.subsurface(rect).copy())
    
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=aimed_target_pos)
        self.pos = aimed_target_pos

        self.frame_index = 0
        self.animation_speed = 30

        self.radius = 128
        self.damage = 20

        self.expired = False

        self.duration = duration
        self.remaining_duration = duration
        
        self.frames_active = 0

    def update(self, dt, world):
        self.frames_active += 1
        self.remaining_duration -= dt

        if self.remaining_duration <= 0:
            self.kill()
            return 

        self.frame_index += self.animation_speed * dt
        self.frame_index %= len(self.frames)
        self.image = self.frames[int(self.frame_index)]

    def get_collisions(self, entities):
        if self.frames_active >= 2:
            return []
    
        return [
            e 
            for e in entities
            if (self.pos[0] - e.rect.center[0]) ** 2 + (self.pos[1] - e.rect.center[1]) ** 2 <= self.radius * self.radius
        ]


