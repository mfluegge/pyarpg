import pygame

from pyarpg.assets import SPRITE_DICT


class Portal(pygame.sprite.Sprite):
    def __init__(self, pos):
        self.sprite_sheet = SPRITE_DICT["portal"]

        self.width_per_frame = 44
        self.height = 57
        self.n_frames = 8

        self.frames = []
        for i in range(self.n_frames):
            rect = pygame.Rect(i * self.width_per_frame, 0, self.width_per_frame, self.height)
            
            self.frames.append(pygame.transform.scale(self.sprite_sheet.subsurface(rect).copy(), (66, 86)))

        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=pos)
        self.pos = pygame.Vector2(self.rect.midbottom)
        self.frame_index = 0
        self.animation_speed = 10
    
    def update(self, dt, world):
        self.frame_index += self.animation_speed * dt
        self.frame_index %= len(self.frames)
        self.image = self.frames[int(self.frame_index)]
