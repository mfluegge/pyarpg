import pygame
from pygame import Vector2
import math

init_size = (1600, 1000)
pygame.init()
pygame.display.set_caption("PyARPG")
real_screen = pygame.display.set_mode(init_size, pygame.RESIZABLE)
screen = pygame.Surface(init_size)

from pyarpg.assets import SPRITE_DICT
from pyarpg.assets import SOUNDS_DICT
from pyarpg.world import World
from pyarpg.level import spawn_random_enemies
from pyarpg.skills import FireballProjectile
from pyarpg.ui import draw_enemy_hp_bars
from pyarpg.player import Player
from pyarpg.pickups import DropGlobe


BG_COLOR = (48, 47, 61)
screen.fill(BG_COLOR)

clock = pygame.time.Clock()
running = True
world = World(screen)


player = Player(pos=(500, 400))
world.add_player(player)

button_to_skill = {
    pygame.K_q: FireballProjectile
}

spawn_random_enemies(world, n_enemies=10)

while running:
    #aimed_target_pos = pygame.Vector2(pygame.mouse.get_pos())
    mx, my = pygame.mouse.get_pos()
    vw, vh = init_size
    ww, wh = real_screen.get_size()
    aimed_target_pos = pygame.Vector2(mx * vw / ww, my * vh / wh)

    dt = clock.tick(300) / 1000.0
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

    world.players.update(dt, world)
    world.active_player_skills.update(dt, world)
    world.enemies.update(dt, world)
    world.active_enemy_skills.update(dt, world)
    world.pickups_waiting.update(dt, world)
    world.pickups_collected.update(dt, world)

    hits = pygame.sprite.groupcollide(world.active_player_skills, world.enemies, dokilla=True, dokillb=False)
    for projectile, hit_enemies in hits.items():
        for enemy in hit_enemies:
            enemies_dies = enemy.take_damage(projectile.damage, world)

    hits = pygame.sprite.groupcollide(world.active_enemy_skills, world.players, dokilla=True, dokillb=False)
    for attack, hit_players in hits.items():
        for player_ in hit_players:
            player_.take_damage(attack.damage)
            print(player.current_hp)
    
            
    screen.fill(BG_COLOR)
    world.pickups_waiting.draw(screen)
    world.pickups_collected.draw(screen)
    world.enemies.draw(screen)
    world.players.draw(screen)
    world.active_enemy_skills.draw(screen)
    world.active_player_skills.draw(screen)
    draw_enemy_hp_bars(world, screen)

    # fps
    #text_surface = my_font.render(f"Kills: {kills}", False, (66, 161, 26))    
    #screen.blit(text_surface, (0,0))

    scaled = pygame.transform.scale(screen, real_screen.get_size())

    real_screen.blit(scaled, (0, 0))
    pygame.display.flip()

pygame.quit()
