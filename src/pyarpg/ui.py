import pygame
from pyarpg.world import World
from pyarpg.assets import SPRITE_DICT
from pyarpg.assets import FONT_DICT


def draw_enemy_hp_bars(world, screen, width: int = 28, height: int = 6, y_offset: int = 13):
    for enemy in world.get_enemies():
        # clamp hp ratio
        hp = max(0.0, min(1.0, enemy.hp_percent))

        # position bar above the enemy
        x = enemy.rect.centerx - width // 2
        y = enemy.rect.top - y_offset

        # background (missing HP)
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (60, 60, 60), bg_rect)

        # fill (current HP)
        fill_rect = pygame.Rect(x, y, int(width * hp), height)
        pygame.draw.rect(screen, (200, 50, 50), fill_rect)

        # border
        pygame.draw.rect(screen, (10, 10, 10), bg_rect, 1)

class BottomUIBar(pygame.sprite.Sprite):
    def __init__(self, screen_w, screen_h, n_skills=3, inside_margin=8, outside_margin=8, loot_slot_width=64, loot_count_init=0):
        super().__init__()

        self.slot_width = SPRITE_DICT["empty_skill_slot"].width
        self.slot_height = SPRITE_DICT["empty_skill_slot"].height
        self.screen_h = screen_h
        self.screen_w = screen_w
        self.inside_margin = inside_margin
        self.outside_margin = outside_margin
        self.loot_slot_width = loot_slot_width

        self.bar_width = (
            self.slot_width * n_skills
            + loot_slot_width
            + inside_margin * n_skills
            + outside_margin * 2

        )

        self.bar_height = self.slot_height + inside_margin * 2

        self.bar_bg = pygame.Surface((self.bar_width, self.bar_height), pygame.SRCALPHA)
        self.bar_bg.fill((80, 80, 80, 50))
        pygame.draw.rect(
            self.bar_bg,
            ((6, 6, 6)),
            self.bar_bg.get_rect(),
            2
        )
        self.rect = self.bar_bg.get_rect(center=(screen_w // 2, screen_h - self.bar_height // 2 - 16))

        self.skill_slots = [
            SkillSlot((self.rect.left + self.outside_margin + (inside_margin * slot_ix) + (self.slot_width // 2) + self.slot_width * slot_ix, self.rect.centery))
            for slot_ix in range(n_skills)
        ]

        self.loot_count = loot_count_init
        self.loot_count_label = FONT_DICT["press_start_18"].render(f"{self.loot_count}", False, (220, 220, 220))   
        self.loot_count_pos = self.loot_count_label.get_rect(center=(self.rect.right - outside_margin - loot_slot_width + inside_margin , self.rect.centery))

    def draw(self, screen):
        screen.blit(self.bar_bg, self.rect)
        for skill_slot in self.skill_slots:
            skill_slot.draw(screen)

        screen.blit(self.loot_count_label, self.loot_count_pos)

    def update(self, dt, world):
        if world.player_stats.loot_count != self.loot_count:
            self.loot_count = world.player_stats.loot_count
            self.loot_count_label = FONT_DICT["press_start_18"].render(f"{self.loot_count}", False, (220, 220, 220)) 


class SkillSlot(pygame.sprite.Sprite):
    def __init__(self, pos, skill_icon=None):
        self.bg_image = SPRITE_DICT["empty_skill_slot"]
        self.rect = self.bg_image.get_rect(center=pos)
    
    def draw(self, screen):
        screen.blit(self.bg_image, self.rect)