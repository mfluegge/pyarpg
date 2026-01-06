from pathlib import Path
import pygame
from pygame import Vector2
import math

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
IMG_DIR = ASSETS_DIR / "images"

pygame.init()
pygame.display.set_caption("PyARPG")
screen = pygame.display.set_mode((1600, 1000))

print("Loading Assets")
ASSET_DICT = {
    "player": pygame.image.load(IMG_DIR / "player3.png").convert_alpha(),
    "fireball": pygame.image.load(IMG_DIR / "fireball.png").convert_alpha(),
    "dummy": pygame.image.load(IMG_DIR / "dummy.png").convert_alpha(),
}

ASSET_DICT["fireball"].set_alpha(180)


BG_COLOR = (48, 47, 61)

screen.fill(BG_COLOR)

clock = pygame.time.Clock()
running = True

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, move_speed=400, dash_speed=1200, dash_distance=150, max_hp=100):
        super().__init__()

        self.image = ASSET_DICT["player"]
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

    def update(self, dt: float):
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
    
class DummyEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, max_hp=100):
        super().__init__()
        self.max_hp = max_hp
        self.current_hp = max_hp

        self.base_image = ASSET_DICT["dummy"]
        self.rect = self.base_image.get_rect(center=pos)

        # --- hit feedback ---
        self.hit_fx_time = 0.0
        self.hit_fx_duration = 0.10  # seconds (short feels better)

        # precompute a flash version (cheap)
        self.flash_image = self.base_image.copy()
        self.flash_image.fill((40, 40, 40), special_flags=pygame.BLEND_RGB_ADD)

        self.time_since_last_attack = 100

    @property
    def hp_percent(self):
        return self.current_hp / self.max_hp
    
    def take_damage(self, n_dmg):
        new_hp = self.current_hp - n_dmg
        if new_hp <= 0:
            self.kill()
            return True
        self.current_hp = max(0, new_hp)

        # trigger feedback
        self.hit_fx_time = self.hit_fx_duration
        return False

    def update(self, dt):
        if self.hit_fx_time > 0:
            self.hit_fx_time = max(0.0, self.hit_fx_time - dt)
            t = 1.0 - (self.hit_fx_time / self.hit_fx_duration)  # 0..1

            # zoom curve: up then back (sine)
            zoom = 1.0 + math.sin(t * math.pi) * 0.12

            # choose flash half the time (or entire time if you want)
            use_flash = t < 0.6
            src = self.flash_image if use_flash else self.base_image

            # scale around center
            center = self.rect.center
            w = max(1, int(src.get_width() * zoom))
            h = max(1, int(src.get_height() * zoom))

            # for pixel art use pygame.transform.scale instead
            self.image = pygame.transform.scale(src, (w, h))
            self.rect = self.image.get_rect(center=center)
        else:
            # restore
            if self.image is not self.base_image:
                center = self.rect.center
                self.image = self.base_image
                self.rect = self.image.get_rect(center=center)

    def launch_attack(self, player_pos, dt):
        dist = (self.rect.center - player_pos).length()

        if dist < 250 and self.time_since_last_attack > 0.6:
            self.time_since_last_attack = 0
            return FireballProjectile(self.rect.center, player_pos)

        else:
            self.time_since_last_attack += dt


class Projectile(pygame.sprite.Sprite):
    def __init__(self, image, start_pos, aimed_target_pos, max_distance=500, move_speed=400, muzzle_offset=20, damage=10):
        super().__init__()

        self.image = image

        start_target_offset = aimed_target_pos - start_pos

        if start_target_offset.length() == 0:
            self.direction = pygame.Vector2(1, 1).normalize()
        else:
            self.direction = start_target_offset.normalize()

        # adding muzzle offset
        self.pos = start_pos + muzzle_offset * self.direction
        self.target_pos = self.pos + self.direction * max_distance

        self.rect = self.image.get_rect(center=self.pos)

        self.move_speed = move_speed
        self.damage = damage

        self.expired = False

    def update(self, dt: float):
        if self.expired:
            self.kill()

        self.move_to_target(dt)
    
    def _update_pos(self, new_pos):
        self.pos = new_pos
        self.rect.center = self.pos

    def move_to_target(self, dt: float):
        remaining_distance = (self.target_pos - self.pos).length()
        coverable_distance = self.move_speed * dt
        
        if remaining_distance <= coverable_distance:
            self._update_pos(self.target_pos)
            self.expired = True
            return
        
        step = self.direction * coverable_distance
        self._update_pos(self.pos + step)


class FireballProjectile(Projectile):
    def __init__(self, start_pos, aimed_target_pos):
        super().__init__(
            image=ASSET_DICT["fireball"],
            start_pos=start_pos,
            aimed_target_pos=aimed_target_pos,
            move_speed=600,
            damage=15
        )

def draw_hp_bar(screen: pygame.Surface, enemy: DummyEnemy,
                width: int = 28, height: int = 6, y_offset: int = 13):
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


def draw_progress_bar(screen, kills):
    pass

players = pygame.sprite.Group()
player = Player(pos=(500, 400))
players.add(player)

enemies = pygame.sprite.Group(
    [DummyEnemy(pos=(100, 200), max_hp=100), DummyEnemy(pos=(300, 600), max_hp=100)]
)

button_to_skill = {
    pygame.K_q: FireballProjectile
}

active_skills = pygame.sprite.Group()
my_font = pygame.font.SysFont('Comic Sans MS', 30)
enemy_attacks = pygame.sprite.Group()
kills = 0
while running:
    aimed_target_pos = pygame.Vector2(pygame.mouse.get_pos())
    dt = clock.tick(300) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # 3 = right
            player.set_target_pos(pygame.Vector2(event.pos))

        elif event.type == pygame.KEYDOWN:
            skill = button_to_skill.get(event.key)
            if skill is not None:
                active_skills.add(skill(player.pos, aimed_target_pos))

            if event.key == pygame.K_SPACE:
                player.set_dash_target(aimed_target_pos)

    if pygame.mouse.get_pressed()[2]:
        player.set_target_pos(pygame.Vector2(pygame.mouse.get_pos()))

    players.update(dt)
    active_skills.update(dt)
    enemies.update(dt)
    enemy_attacks.update(dt)

    hits = pygame.sprite.groupcollide(active_skills, enemies, dokilla=True, dokillb=False)
    for projectile, hit_enemies in hits.items():
        for enemy in hit_enemies:
            enemies_dies = enemy.take_damage(projectile.damage)
            kills += enemies_dies

    # enemy attacks
    for enemy in enemies:
        attack = enemy.launch_attack(player.pos, dt)
        if attack is not None:
            enemy_attacks.add(attack)

    hits = pygame.sprite.groupcollide(enemy_attacks, players, dokilla=True, dokillb=False)
    for attack, hit_players in hits.items():
        for player_ in hit_players:
            player.take_damage(attack.damage)
            print(player.current_hp)
            
    screen.fill(BG_COLOR)
    players.draw(screen)
    enemies.draw(screen)
    for enemy in enemies:
        draw_hp_bar(screen, enemy)

    active_skills.draw(screen)
    enemy_attacks.draw(screen)

    # fps
    text_surface = my_font.render(f"Kills: {kills}", False, (66, 161, 26))    
    screen.blit(text_surface, (0,0))

    pygame.display.flip()

pygame.quit()
