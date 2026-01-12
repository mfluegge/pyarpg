import pygame
from pygame import Vector2
import math

init_size = (1600, 900)
pygame.init()
pygame.display.set_caption("PyARPG")
screen = pygame.display.set_mode(init_size, pygame.RESIZABLE)

BG_COLOR = (45, 64, 54)



class String:
    def __init__(self, head_rect, attachment_offset=0, segment_length=30, width=12, is_outline=False, upper_body_rigidity=1, damping=0.4, y_offset=0):
        self.head_rect = head_rect
        self.attach_offset = pygame.Vector2(attachment_offset, y_offset)
        self.segment_length = segment_length
        self.width = width


        # --- cloak points ---
        self.p1 = Vector2(head_rect.midbottom + self.attach_offset)
        self.p2 = self.p1 + Vector2(0, segment_length)
        self.p3 = self.p2 + Vector2(0, segment_length)

        # Verlet needs previous position too:
        self.p1_prev = self.p1.copy()
        self.p2_prev = self.p2.copy()
        self.p3_prev = self.p3.copy()

        self.damping = damping  # closer to 1.0 = more swishy, lower = more stable
        self.gravity = 5000 # pixels/sec^2 (downwards)
        self.constraint_iters = 1    # more = stiffer and less stretchy

        self.is_outline = is_outline
        self.upper_body_rigidity = upper_body_rigidity

        self.target = None


    def _update_point(self, dt, point, point_prev, rigidity=1, use_target=False):
        # -------------------------
        # Verlet update for p2
        # -------------------------
        # "velocity" from last frame (purely from position memory)
        vel = (point - point_prev) * self.damping

        if use_target and self.target is not None:
            to_target = (Vector2(self.target) - point)
            if to_target.length_squared() > 1e-8:
                acc = to_target.normalize() * 100000
            else:
                acc = Vector2(0, 0)
        else:
            acc = Vector2(0, self.gravity * rigidity)
        # Verlet integration step (note the dt*dt)
        point_temp = point.copy()
        point = point + vel + acc * (dt * dt)
        point_prev = point_temp

        return point, point_prev

    def update(self, dt, player):
        # --- pin p1 to character ---
        self.p1 = Vector2(player.head_rect.midbottom + self.attach_offset)
        self.p1_prev = self.p1.copy()

        self.p2, self.p2_prev = self._update_point(dt, self.p2, self.p2_prev, self.upper_body_rigidity, use_target=True)
        self.p3, self.p3_prev = self._update_point(dt, self.p3, self.p3_prev, use_target=True)
  
        # -------------------------
        # Distance constraint solve:
        # keep |p2 - p1| == rest_len
        # -------------------------
        for _ in range(self.constraint_iters):
            delta = self.p2 - self.p1
            dist = delta.length()
            if dist != 0:
                # Move ONLY p2, because p1 is pinned
                self.p2 = self.p1 + delta * (self.segment_length / dist)


        for _ in range(self.constraint_iters):
            delta = self.p3 - self.p2
            dist = delta.length()
            if dist != 0:
                # Move ONLY p2, because p1 is pinned
                self.p3 = self.p2 + delta * (self.segment_length / dist)

    def draw(self, screen):
        # Draw the segment for clarity
        if self.is_outline and False:
            c1 = (30, 30, 30)
            c2 = (40, 40, 40)
            w = self.width
            w2 = self.width
            off = pygame.Vector2((5, 0))
            yoff1 = pygame.Vector2((-5, 0))
            yoff2 = pygame.Vector2((-10, 0))
            pygame.draw.line(screen, c1, self.p1, self.p2, w)
            pygame.draw.line(screen, c1, self.p2, self.p3 + yoff2, w)
            pygame.draw.line(screen, c2, self.p1 + off, self.p2 + off, w)
            pygame.draw.line(screen, c2, self.p2 + off, (self.p3 + off) + yoff2, w)

        else:
            c = (20, 20, 20)
            w = self.width
            w2 = self.width
            pygame.draw.line(screen, c, self.p1, self.p2, w)
            pygame.draw.line(screen, c, self.p2, self.p3, w2)



class Player:
    def __init__(self, start_pos, string_offsets=(-8, 0, 8)):
        head_size = (20, 20)
        eye = pygame.surface.Surface((2, 2))
        eye.fill((44, 120, 106))
        head = pygame.surface.Surface(head_size)
        head.fill((30, 30, 30))

        self.head_front = head.copy()
        self.head_front.blit(eye, (7, 6))
        self.head_front.blit(eye, (12, 6))

        self.head_back = head.copy()
        self.head_left = head.copy()
        self.head_left.blit(eye, (3, 6))
        self.head_right = head.copy()
        self.head_right.blit(eye, (15, 6))
        self.head = self.head_front

        self.head_rect = self.head.get_rect(midbottom=start_pos)

        self.n_strings = len(string_offsets)

        self.strings = [
            String(
                self.head_rect, 
                attachment_offset=offset, 
                is_outline=ix==len(string_offsets) - 1,
                upper_body_rigidity=10 - ix
            )
            for ix, offset in enumerate(string_offsets)
        ]

        self.strings2 = [
            String(
                self.head_rect, 
                attachment_offset=offset, 
                is_outline=ix==len(string_offsets) - 1,
                upper_body_rigidity=0.5,
                width=2,
                segment_length=15,
                damping=0.7,
                y_offset=15 + (4 * ix)
            )
            for ix, offset in enumerate([-10, 0, 10])
        ]

        self.movespeed = 500

        self.target = None
        self.direction = "down"

    def set_discrete_direction(self, diff):
        if diff.length() < 0.00001:
            return

        direction = diff.normalize()
        angle = math.degrees(math.atan2(direction.x, direction.y))
        if angle > 135 or angle < -135:
            self.head = self.head_back
            self.direction = "up"

        elif 45 <= angle < 135:
            self.head = self.head_right
            self.direction = "right"
        
        elif -45 <= angle < 45:
            self.head = self.head_front
            self.direction = "up"

        else:
            self.head = self.head_left
            self.direction = "left" 
        

    def set_target(self, target):
        self.target = pygame.Vector2(target)

    def update(self, dt):
        if self.target is not None:
            max_dist = self.movespeed * dt
            diff = Vector2(self.target) - Vector2(self.head_rect.midbottom)
            self.set_discrete_direction(diff)
            if diff.length() <= max_dist:
                self.head_rect.midbottom = self.target
                self.target = None
            else:
                direction = diff.normalize()
                self.head_rect.midbottom += direction * max_dist

        rigidities = [10, 9, 8, 7, 6, 5]
        if self.direction == "right":
            rigidities = rigidities[::-1]
        elif self.direction == "up":
            rigidities = [10] * 6
        elif self.direction == "down":
            rigidities = [1] * 6

        for string, rig in zip(self.strings, rigidities, strict=True):
            string.upper_body_rigidity = rig
            string.update(dt, self)

        for string in self.strings2:
            string.update(dt, self)
        
    def draw(self, screen):
        screen.blit(self.head, self.head_rect)

        for string in self.strings2:
            string.draw(screen)
        for string in self.strings:
            string.draw(screen)





player = Player(start_pos=(300, 300), string_offsets=(-10, -6, -2, 2, 6, 10))

clock = pygame.time.Clock()
running = True

# --- tuning knobs ---
gravity = 5200.0          

while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            player.set_target(pygame.mouse.get_pos())

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            mouse = Vector2(pygame.mouse.get_pos())
            base = (mouse - player.head_rect.midbottom)
            base_dir = base.normalize()
            side = base_dir.rotate(90)

            spread = 180  # pixels across
            n_strings = len(player.strings)
            for ix, s in enumerate(player.strings):
                t = ix / (n_strings - 1)
                offset = (t - 0.5) * spread

                s.target = (mouse + side * offset)

    player.update(dt)

    # --- draw ---
    screen.fill(BG_COLOR)
    player.draw(screen)


    pygame.display.flip()

pygame.quit()