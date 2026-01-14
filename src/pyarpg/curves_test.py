import pygame
from pygame.math import Vector2
import math

init_size = (1600, 900)
pygame.init()
pygame.display.set_caption("PyARPG")
screen = pygame.display.set_mode(init_size, pygame.RESIZABLE)

BG_COLOR = (45, 64, 54)


def quartic_bezier(p0, p1, p2, p3, p4, t):
    u = 1 - t
    return (
        u**4 * p0 +
        4 * u**3 * t * p1 +
        6 * u**2 * t**2 * p2 +
        4 * u * t**3 * p3 +
        t**4 * p4
    )


def draw_wings(surface, point_seqs, player_pos, target_pos, steps=30):
    diff = target_pos - player_pos
    #rot_angle = math.degrees(math.atan2(diff.x, diff.y)) * -1
    rot_angle = pygame.Vector2(0, -1).angle_to(diff)
    for p0, p1, p2, p3, p4 in point_seqs:
        pts = [((quartic_bezier(p0 + player_pos, p1+player_pos, p2+player_pos, p3+player_pos, p4+player_pos, i/steps) - player_pos).rotate(rot_angle) + player_pos) for i in range(steps+1)]

        pygame.draw.lines(surface, (30, 30, 30), False, pts,width=6)


class MultiShotWings:
    def __init__(self, player_pos, target_pos):
        self. right_1 = [
            #pygame.Vector2(10, 10),
            pygame.Vector2(0, 0),
            pygame.Vector2(30, 40),
            pygame.Vector2(100, 16),
            pygame.Vector2(10, -30),
            pygame.Vector2(10, -100)
        ]
      
        self.right_2 = [
            v * 1.4 for v in self.right_1
        ]
        self.right_2[-1] = self.right_1[-1] + pygame.Vector2(20, 0)

        self.right_3 = [
            v * 1.4 for v in self.right_2
        ]
        self.right_3[-1] = self.right_2[-1] + pygame.Vector2(20, 0)

        self.left_1 = [
            #pygame.Vector2(-10, 10),
            pygame.Vector2(0, 0),
            pygame.Vector2(-30, 40),
            pygame.Vector2(-100, 16),
            pygame.Vector2(-10, -30),
            pygame.Vector2(-10, -100)
        ]
        self.left_2 = [
            v * 1.4 for v in self.left_1
        ]
        self.left_2[-1] = self.left_1[-1] + pygame.Vector2(-20, 0)


        self.left_3 = [
            v * 1.4 for v in self.left_2
        ]
        self.left_3[-1] = self.left_2[-1] + pygame.Vector2(-20, 0)

        self.init_right1 = [
            pygame.Vector2(0, 0),
            pygame.Vector2(0, 10),
            pygame.Vector2(0, 20),
            pygame.Vector2(0, 30),
            pygame.Vector2(0, 40),
        ]
        self.init_right2 = self.init_right1[:]
        self.init_right3 = self.init_right2[:]
        self.init_left1 = [
            pygame.Vector2(0, 0),
            pygame.Vector2(0, 10),
            pygame.Vector2(0, 20),
            pygame.Vector2(0, 30),
            pygame.Vector2(0, 40),
        ]
        self.init_left2 = self.init_left1[:]
        self.init_left3 = self.init_left2[:]

        self.time_passed = 0

        diff = target_pos - player_pos
        self.player_pos = player_pos
        self.target_pos = target_pos
        self.rot_angle = pygame.Vector2(0, -1).angle_to(diff)

    def update(self, dt):
        self.time_passed += dt
        

    def draw(self, surface, steps=100):
        if self.time_passed < 0.2:
            use_points = 2
        elif self.time_passed < 0.4:
            use_points = 4

        mult = min(1, self.time_passed)
        point_seqs = [
            [
                (1-mult) * init + mult * post
                for init, post in zip(self.init_right1, self.right_1)
            ],
            [
                (1-mult) * init + mult * post
                for init, post in zip(self.init_right2, self.right_2)
            ],
            [
                (1-mult) * init + mult * post
                for init, post in zip(self.init_right3, self.right_3)
            ],
            [
                (1-mult) * init + mult * post
                for init, post in zip(self.init_left1, self.left_1)
            ],
            [
                (1-mult) * init + mult * post
                for init, post in zip(self.init_left2, self.left_2)
            ],
            [
                (1-mult) * init + mult * post
                for init, post in zip(self.init_left3, self.left_3)
            ]
        ]

        
        for p0, p1, p2, p3, p4 in point_seqs:
            pts = [((quartic_bezier(p0 + self.player_pos, p1+self.player_pos, p2+self.player_pos, p3+self.player_pos, p4+self.player_pos, i/steps) - self.player_pos).rotate(self.rot_angle) + self.player_pos) for i in range(steps+1)]

            pygame.draw.lines(surface, (30, 30, 30), False, pts, width=6)

class String2:
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

    def _update_point(self, dt, point, point_prev, pull_direction = None):
        # -------------------------
        # Verlet update for p2
        # -------------------------
        # "velocity" from last frame (purely from position memory)
        vel = (point - point_prev) * self.damping

        if pull_direction is None:
            acc = Vector2(0, 0)
        else:
            acc = pull_direction * 100

        # Verlet integration step (note the dt*dt)
        point_temp = point.copy()
        point = point + vel + acc * (dt * dt)
        point_prev = point_temp

        return point, point_prev

    def update(self, dt, player_pos, pull_direction):
        # --- pin p1 to character ---
        self.p1 = Vector2(player_pos + self.attach_offset)
        self.p1_prev = self.p1.copy()

        self.p2, self.p2_prev = self._update_point(dt, self.p2, self.p2_prev, pull_direction=None)

        self.p3, self.p3_prev = self._update_point(dt, self.p3, self.p3_prev, pull_direction)

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
        c = (20, 20, 20)
        w = self.width
        w2 = self.width
        pygame.draw.line(screen, c, self.p1, self.p2, w)
        pygame.draw.line(screen, c, self.p2, self.p3, w2)


class String:
    def __init__(self, head_rect, attachment_offset=0, segment_length=30, width=12,
                 is_outline=False, upper_body_rigidity=1, damping=0.98, y_offset=0):
        self.head_rect = head_rect
        self.attach_offset = Vector2(attachment_offset, y_offset)
        self.segment_length = segment_length
        self.width = width

        # points
        self.p1 = Vector2(head_rect.midbottom) + self.attach_offset
        self.p2 = self.p1 + Vector2(0, segment_length)
        self.p3 = self.p2 + Vector2(0, segment_length)

        # previous positions (verlet)
        self.p1_prev = self.p1.copy()
        self.p2_prev = self.p2.copy()
        self.p3_prev = self.p3.copy()

        self.damping = damping
        self.constraint_iters = 6  # more iters = stiffer
        self.pull_strength = 2000  # tune this
        self.max_pull_acc = 20000  # clamp so it doesn't explode

    def _verlet(self, dt, p, p_prev, acc):
        vel = (p - p_prev) * self.damping
        p_temp = p.copy()
        p = p + vel + acc * (dt * dt)
        p_prev = p_temp
        return p, p_prev

    def _solve_distance(self, a, b, rest_len, wa, wb):
        """
        Enforce |b-a| == rest_len by moving a and/or b.
        wa/wb are "weights": 0 means pinned, 1 means free (or any ratio you want).
        """
        delta = b - a
        dist = delta.length()
        if dist == 0:
            return a, b

        # how much to correct along the delta direction
        diff = (dist - rest_len) / dist
        total_w = wa + wb
        if total_w == 0:
            return a, b

        correction = delta * diff

        # move proportionally (pinned endpoint gets wa=0 so it won't move)
        a = a + correction * (wa / total_w)
        b = b - correction * (wb / total_w)
        return a, b

    def update(self, dt, player_pos, pull_target=None):
        # pin p1 to character
        self.p1 = Vector2(player_pos) + self.attach_offset
        self.p1_prev = self.p1.copy()

        # free verlet for p2 (no external force)
        self.p2, self.p2_prev = self._verlet(dt, self.p2, self.p2_prev, Vector2(0, 0))

        # pull p3 toward target (like gravity toward a point)
        acc3 = Vector2(0, 0)
        if pull_target is not None:
            to_target = Vector2(pull_target) - self.p3
            # linear attraction (good for "string being dragged")
            acc3 = to_target * self.pull_strength
            # clamp acceleration magnitude
            if acc3.length() > self.max_pull_acc:
                acc3.scale_to_length(self.max_pull_acc)

        self.p3, self.p3_prev = self._verlet(dt, self.p3, self.p3_prev, acc3)

        # solve constraints multiple times so pull transmits up the chain
        for _ in range(self.constraint_iters):
            # segment p1-p2: p1 pinned, p2 free
            self.p1, self.p2 = self._solve_distance(self.p1, self.p2, self.segment_length, wa=0.0, wb=1.0)

            # segment p2-p3: both free (this is the key change!)
            self.p2, self.p3 = self._solve_distance(self.p2, self.p3, self.segment_length, wa=1.0, wb=1.0)

            # re-pin p1 each iteration to avoid drift from float error
            self.p1 = Vector2(player_pos) + self.attach_offset

    def draw(self, screen):
        c = (20, 20, 20)
        pygame.draw.line(screen, c, self.p1, self.p2, self.width)
        pygame.draw.line(screen, c, self.p2, self.p3, self.width)


clock = pygame.time.Clock()
running = True


player = pygame.Surface((20, 20))
player.fill((80, 80, 80))
player_rect = player.get_rect(center=(800, 450))

target = pygame.Vector2(800, 200)
current_deviation = 0
max_deviation = 100
step = 6
player_pos = pygame.Vector2(player_rect.center)
#wings = MultiShotWings(player_pos, target)
s = String(player_rect, segment_length=50)

while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            target = pygame.Vector2(pygame.mouse.get_pos())
            print("setting target", target)
            #wings = MultiShotWings(player_pos, target)

    s.update(dt, player_pos, pull_target=target)

    # --- draw ---
    screen.fill(BG_COLOR)

    """
    diff = target - pygame.Vector2(player_rect.center)
    forward = diff.normalize()
    right = forward.rotate(-90)   # screen coords: this usually behaves like "right"
    up = forward.rotate(90)       # this is "left"
    behind = -forward   
    #diff = (target - player_rect.center)
    parallel = diff.normalize()
    normal = diff.normalize().rotate(90)

    #right_3[3] += normal * current_deviation
    #right_3[1] += behind * current_deviation

    #left_3[3] -= normal * current_deviation
    #left_3[1] += behind * current_deviation

    # local-space pulse directions (template faces up)
    local_behind = pygame.Vector2(0, 1)
    local_out_right = pygame.Vector2(1, 0)
    local_out_left  = pygame.Vector2(-1, 0)
    """
    """
    # spread / flap (choose points you want)
    right_3[2] += local_out_right * (- current_deviation / 2 + max_deviation)
    right_2[2] += local_out_right * (- current_deviation / 2+ max_deviation)
    right_1[2] += local_out_right * (- current_deviation / 2+ max_deviation)
    right_3[3] += local_out_right * (current_deviation - max_deviation)
    right_2[3] += local_out_right * (current_deviation - max_deviation)
    right_1[3] += local_out_right * (current_deviation - max_deviation)
    right_3[1] += local_behind * current_deviation
    right_2[1] += local_behind * current_deviation
    right_1[1] += local_behind * current_deviation

    left_3[3]  += local_out_left  * (- current_deviation + max_deviation)
    left_2[3] += local_out_left * (- current_deviation + max_deviation)
    left_1[3] += local_out_left * (- current_deviation + max_deviation)
    left_3[1] += local_behind * current_deviation
    left_2[1] += local_behind * current_deviation
    left_1[1] += local_behind * current_deviation

    draw_wings(
        screen,
        [right_1, right_2, right_3, left_1, left_2, left_3],
        pygame.Vector2(player_rect.center),
        target,
        steps=200
    )


    pygame.draw.circle(screen, color=(150, 30, 30), center=target, radius=6)


    path = pygame.draw.line(screen, (200, 200, 200), player_rect.center, player_rect.center + diff)
    pygame.draw.line(screen, (200, 200, 200), player_rect.center - normal * 100, player_rect.center + normal * 100)
    """
    #wings.update(dt)
    #wings.draw(screen)
    pygame.draw.circle(screen, color=(150, 30, 30), center=target, radius=6)
    screen.blit(player, player_rect)
    s.draw(screen)

    pygame.display.flip()

    #current_deviation += step
    #if current_deviation >= max_deviation or current_deviation <= 0:
    #    step *= -1

pygame.quit()