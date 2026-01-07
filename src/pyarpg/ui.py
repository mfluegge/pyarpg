import pygame
from pyarpg.world import World


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
