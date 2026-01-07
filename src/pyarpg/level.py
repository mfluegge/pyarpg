import random
import pygame

from pyarpg.world import World
from pyarpg.enemies import MeleeEnemy
from pyarpg.enemies import RangedEnemy


def spawn_random_enemies(world: World, n_enemies=10):
    enemy_types = random.choices([MeleeEnemy, RangedEnemy], k=n_enemies)
    min_w = round(world.max_width * 0.05)
    max_w = round(world.max_width * 0.95)
    min_h = round(world.max_height * 0.05)
    max_h = round(world.max_height * 0.95)

    for enemy_class in enemy_types:
        x = random.randint(min_w, max_w)
        y = random.randint(min_h, max_h)
        pos = pygame.Vector2(x, y)
        enemy = enemy_class(start_pos=pos)
        world.add_enemy(enemy)

