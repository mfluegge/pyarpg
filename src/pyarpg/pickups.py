import pygame

from pyarpg.assets import SPRITE_DICT


class DropGlobe(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()

        self.width_per_frame = 22
        self.height = 36
        self.n_frames = 6

        self.sprite_sheet = SPRITE_DICT["drop_globe"]

        self.frames = []
        for i in range(self.n_frames):
            rect = pygame.Rect(i * self.width_per_frame, 0, self.width_per_frame, self.height)
            
            self.frames.append(self.sprite_sheet.subsurface(rect).copy())
    
        self.image = self.frames[0]
    
        self.rect = self.image.get_rect()

        self.rect.midbottom = pos

        self.frame_index = 0
        self.animation_speed = 10
    
    def update(self, dt, world):
        self.frame_index += self.animation_speed * dt
        self.frame_index %= len(self.frames)

        self.image = self.frames[int(self.frame_index)]


