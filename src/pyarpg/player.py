import pygame
from pygame import Vector2
from pyarpg.assets import IMAGE_DICT
from pyarpg.world import World

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, move_speed=400, dash_speed=1200, dash_distance=150, max_hp=100):
        super().__init__()

        self.image = IMAGE_DICT["player"]
        self.rect = self.image.get_rect(center=pos)

        self.pos: Vector2 = pygame.Vector2(self.rect.center)

        self.move_speed = move_speed
        self.dash_speed = dash_speed

        self.current_target_pos = None
        
        self.is_dashing = False
        self.dash_distance = dash_distance

        self.max_hp = max_hp
        self.current_hp = max_hp

    def set_target_pos(self, target_pos):
        if self.is_dashing:
            return

        self.current_target_pos = target_pos

    def take_damage(self, n_dmg):
        self.current_hp = self.current_hp - n_dmg

    def set_dash_target(self, aimed_pos):
        offset = aimed_pos - self.pos
        if offset.length_squared() == 0:
            return
        direction = offset.normalize()

        target_pos = self.pos + direction * self.dash_distance
        self.current_target_pos = target_pos
        self.is_dashing = True

    def update(self, dt: float, world: World):
        if self.current_target_pos is not None:
            self.move_to_target(dt)

    def _update_pos(self, new_pos):
        self.pos = new_pos
        self.rect.center = new_pos

    def move_to_target(self, dt: float):
        if self.current_target_pos is None:
            return

        if self.is_dashing:
            coverable_distance = self.dash_speed * dt
        else:
            coverable_distance = self.move_speed * dt

        diff = (self.current_target_pos - self.pos)
        distance = diff.length()
        
        if distance <= coverable_distance:
            self._update_pos(self.current_target_pos)
            self.current_target_pos = None
            self.is_dashing = False
            return
        
        direction = diff / distance
        step = direction * coverable_distance
        self._update_pos(self.pos + step)