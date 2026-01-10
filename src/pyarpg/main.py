import pygame
from pygame import Vector2
import math

init_size = (1600, 900)
pygame.init()
pygame.display.set_caption("PyARPG")
real_screen = pygame.display.set_mode(init_size, pygame.RESIZABLE)
screen = pygame.Surface(init_size)

from pyarpg.assets import SPRITE_DICT
from pyarpg.assets import SOUNDS_DICT
from pyarpg.world import World
from pyarpg.level import spawn_random_enemies
from pyarpg.skills import FireballProjectile
from pyarpg.skills import BlueCircleAOESkill
from pyarpg.skills import RingOfFire
from pyarpg.ui import draw_enemy_hp_bars
from pyarpg.player import Player
from pyarpg.pickups import DropGlobe
from pyarpg.ui import BottomUIBar
from pyarpg.stats import PlayerStats
from pyarpg.portals import Portal
import cProfile, pstats

profiler = cProfile.Profile()
profiler.enable()



BG_COLOR = (48, 47, 61)
screen.fill(BG_COLOR)

clock = pygame.time.Clock()
running = True
ui_bar = BottomUIBar(*init_size)

world = World(screen, PlayerStats())


player = Player(pos=(500, 400))
world.add_player(player)

button_to_skill = {
    pygame.K_q: FireballProjectile
}

button_to_ground_skill = {
    pygame.K_w: RingOfFire
}

spawn_random_enemies(world, n_enemies=100)
"""
cell_size = 64
n_grid_cols = math.ceil(init_size[0] / cell_size)
n_grid_rows = math.ceil(init_size[1] / cell_size)
print("Grid Size:", (n_grid_rows, n_grid_cols))
spatial_grid = [
    {
        "enemy": [],
    }
    for _ in range(n_grid_rows * n_grid_cols)
]

def _transform_to_grid_index(col_ix, row_ix, n_rows):
    return col_ix * n_rows + row_ix

def gen_relevant_indices(col_ix, row_ix, max_col, max_row):
    nbors = set()
    for col_offset in (-1, 0, 1):
        for row_offset in (-1, 0, 1):
            col_ = min(max(0, col_ix + col_offset), max_col)
            row_ = min(max(0, row_ix + row_offset), max_row)
            nbors.add(col_)
    
    return (_transform_to_grid_index(c, r) for c_r in nbors)

grid_ix_to_neighboring_indices = [
    f??
]
"""

portal = Portal(pygame.Vector2(70, init_size[1] // 2 + 20))
slow_mo = 5
while running:
    #aimed_target_pos = pygame.Vector2(pygame.mouse.get_pos())
    mx, my = pygame.mouse.get_pos()
    vw, vh = init_size
    ww, wh = real_screen.get_size()
    aimed_target_pos = pygame.Vector2(mx * vw / ww, my * vh / wh)

    dt = clock.tick(300) / 1000.0 / max(slow_mo, 1)
    slow_mo -= (dt * 15)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # 3 = right
            mx, my = event.pos
            vw, vh = init_size
            ww, wh = real_screen.get_size()
            player_target = pygame.Vector2(mx * vw / ww, my * vh / wh)
            player.set_target_pos(player_target)

        elif event.type == pygame.KEYDOWN:
            skill = button_to_skill.get(event.key)
            if skill is not None:
                world.add_active_player_skill(skill(player.pos, aimed_target_pos))

            skill = button_to_ground_skill.get(event.key)
            if skill is not None:
                world.add_active_player_ground_skill(skill(aimed_target_pos))

            if event.key == pygame.K_SPACE:
                player.set_dash_target(aimed_target_pos)

        elif event.type == pygame.VIDEORESIZE:
            # Recreate the window at the new size
            real_screen = pygame.display.set_mode(
                (event.w, event.h),
                pygame.RESIZABLE
            )

    if pygame.mouse.get_pressed()[2]:
        player.set_target_pos(aimed_target_pos)

    portal.update(dt, world)
    world.players.update(dt, world)
    world.active_player_skills.update(dt, world)
    world.active_player_ground_skills.update(dt, world)
    world.enemies.update(dt, world)
    world.active_enemy_skills.update(dt, world)
    world.pickups_waiting.update(dt, world)
    world.pickups_collected.update(dt, world)
    ui_bar.update(dt, world)

    hits = pygame.sprite.groupcollide(world.active_player_skills, world.enemies, dokilla=True, dokillb=False)
    for projectile, hit_enemies in hits.items():
        for enemy in hit_enemies:
            enemies_dies = enemy.take_damage(projectile.damage, world)

    hits = pygame.sprite.groupcollide(world.active_enemy_skills, world.players, dokilla=True, dokillb=False)
    for attack, hit_players in hits.items():
        for player_ in hit_players:
            player_.take_damage(attack.damage)
            print(player.current_hp)
    
    for pickup in world.pickups_waiting:
        if player.pickup_rect.colliderect(pickup.rect):
            pickup.collect(*ui_bar.loot_count_pos.center)
            world.pickups_waiting.remove(pickup)
            world.pickups_collected.add(pickup)


    for ground_skill in world.active_player_ground_skills:
        for enemy in ground_skill.get_collisions(world.enemies):
            enemy.take_damage(ground_skill.damage, world)
            
    screen.fill(BG_COLOR)
    screen.blit(portal.image, portal.rect)
    world.active_player_ground_skills.draw(screen)
    world.pickups_waiting.draw(screen)
    world.enemies.draw(screen)
    world.players.draw(screen)
    world.active_enemy_skills.draw(screen)
    world.active_player_skills.draw(screen)
    draw_enemy_hp_bars(world, screen)
    ui_bar.draw(screen)
    world.pickups_collected.draw(screen)
    
    screen.blit(SPRITE_DICT["tree1"], (1000, 240))
    screen.blit(SPRITE_DICT["tree1"], (300, 190))
    screen.blit(SPRITE_DICT["tree1"], (800, 600))

    # fps
    #screen.blit(text_surface, (0,0))
    if screen.get_size() != real_screen.get_size():
        scaled = pygame.transform.scale(screen, real_screen.get_size())
    else:
        scaled = screen

    real_screen.blit(scaled, (0, 0))
    pygame.display.flip()

profiler.disable()

stats = pstats.Stats(profiler).sort_stats('cumtime')
stats.print_stats(20)  # top 20 slowest calls

pygame.quit()
