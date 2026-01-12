import pygame
from pygame import Vector2
from pyarpg.assets import SPRITE_DICT
from pyarpg.world import World

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, move_speed=400, dash_speed=1200, dash_distance=150, max_hp=100, pickup_radius=40):
        super().__init__()

        self.pickup_radius = pickup_radius
        self.image = SPRITE_DICT["player_test"]
        self.rect = self.image.get_rect(center=pos)
        self.pickup_rect = self.rect.inflate(self.pickup_radius * 2, self.pickup_radius * 2)

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
            self.move_to_target(dt, world)

    def _update_pos(self, new_pos, world):
        max_w = world.max_width - self.rect.width // 2
        max_h = world.max_height - self.rect.height // 2

        if new_pos[0] > max_w:
            new_pos[0] = max_w
            self.current_target_pos = None
            self.is_dashing = False

        elif new_pos[0] < self.rect.width // 2:
            new_pos[0] = self.rect.width // 2
            self.current_target_pos = None
            self.is_dashing = False


        if new_pos[1] > max_h:
            new_pos[1] = max_h
            self.current_target_pos = None
            self.is_dashing = False

        elif new_pos[1] < self.rect.height // 2:
            new_pos[1] = self.rect.height // 2
            self.current_target_pos = None
            self.is_dashing = False


        self.pos = new_pos
        self.rect.center = new_pos
        
        self.pickup_rect = self.rect.inflate(self.pickup_radius * 2, self.pickup_radius * 2)


    def move_to_target(self, dt: float, world):
        if self.current_target_pos is None:
            return

        if self.is_dashing:
            coverable_distance = self.dash_speed * dt
        else:
            coverable_distance = self.move_speed * dt

        diff = (self.current_target_pos - self.pos)
        distance = diff.length()
        
        if distance <= coverable_distance:
            self._update_pos(self.current_target_pos, world)
            self.current_target_pos = None
            self.is_dashing = False
            return
        
        direction = diff / distance
        step = direction * coverable_distance
        self._update_pos(self.pos + step, world)