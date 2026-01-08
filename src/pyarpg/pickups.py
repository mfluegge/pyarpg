import pygame

from pyarpg.assets import SPRITE_DICT


class DropGlobe(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()

        self.loot_value = 1
        self.width_per_frame = 22
        self.height = 36
        self.n_frames = 6
        self.storage_move_speed = 1200

        self.sprite_sheet = SPRITE_DICT["drop_globe"]

        self.frames = []
        for i in range(self.n_frames):
            rect = pygame.Rect(i * self.width_per_frame, 0, self.width_per_frame, self.height)
            
            self.frames.append(self.sprite_sheet.subsurface(rect).copy())
    
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=pos)
        self.pos = pygame.Vector2(self.rect.midbottom)

        self.frame_index = 0
        self.animation_speed = 10
        self.has_been_collected = False
        self.storage_pos = None
    
    def update(self, dt, world):
        if not self.has_been_collected:
            self.frame_index += self.animation_speed * dt
            self.frame_index %= len(self.frames)
            self.image = self.frames[int(self.frame_index)]
            return

        self._move_to_storage(dt, world)


    def collect(self, x_storage, y_storage):
        self.has_been_collected = True
        self.image = self.frames[int(self.frame_index)]
        self.storage_pos = pygame.Vector2((x_storage, y_storage))

    def _update_pos(self, new_pos):
        self.pos = new_pos
        self.rect.midbottom = new_pos
    
    def _move_to_storage(self, dt, world):
        coverable_distance = self.storage_move_speed * dt

        diff = (self.storage_pos - self.pos)
        distance = diff.length()
        
        if distance <= coverable_distance:
            self._update_pos(self.storage_pos)
            world.player_stats.loot_points += self.loot_value
            self.kill()
            return
        
        direction = diff / distance
        step = direction * coverable_distance
        self._update_pos(self.pos + step)