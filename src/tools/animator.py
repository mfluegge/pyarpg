import pygame
from pygame import Vector2
from PySide6.QtWidgets import QApplication, QFileDialog
import sys

_qt_app = None

def open_file_dialog():
    global _qt_app

    # Create QApplication once
    if _qt_app is None:
        _qt_app = QApplication(sys.argv)

    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select a file",
        "",
        "All Files (*.*)"
    )   

    return file_path


def inverse_scale_mouse_pos(draw_surface, screen, mx, my):
    vw, vh = draw_surface.get_size()
    ww, wh = screen.get_size()
    return pygame.Vector2(mx * vw / ww, my * vh / wh)


def map_mouse_pos(draw_surface, screen, mx, my):
    x = mx - (screen.get_width() - draw_surface.get_width() + DRAW_SURFACE_MARGIN_X)
    y = my - TOP_MARGIN
    return pygame.Vector2(x, y)



def _cr_point(p0: Vector2, p1: Vector2, p2: Vector2, p3: Vector2, t: float) -> Vector2:
    """
    Uniform Catmull–Rom spline point for parameter t in [0, 1].
    Segment runs from p1 to p2.
    """
    t2 = t * t
    t3 = t2 * t

    # Standard Catmull–Rom basis (tau = 0.5)
    return 0.5 * (
        (2.0 * p1) +
        (-p0 + p2) * t +
        (2.0*p0 - 5.0*p1 + 4.0*p2 - p3) * t2 +
        (-p0 + 3.0*p1 - 3.0*p2 + p3) * t3
    )

def catmull_rom_points(anchor_points, steps_per_segment=10, closed=False):
    """
    Returns a list of (x, y) tuples sampled along a Catmull–Rom spline
    that passes through all anchor_points.

    - steps_per_segment: number of samples between each pair of anchors.
      (Higher = smoother)
    - closed: if True, wraps around to form a loop.
    """
    pts = [Vector2(p) for p in anchor_points]
    n = len(pts)
    if n == 0:
        return []
    if n == 1:
        return [(pts[0].x, pts[0].y)]
    if steps_per_segment < 1:
        steps_per_segment = 1

    def get(i):
        if closed:
            return pts[i % n]
        # endpoint clamping for open curves
        return pts[max(0, min(n - 1, i))]

    out = []

    # We generate segments from p1->p2 for i in [0..n-2] (open) or [0..n-1] (closed)
    seg_count = n if closed else n - 1

    for i in range(seg_count):
        p0 = get(i - 1)
        p1 = get(i)
        p2 = get(i + 1)
        p3 = get(i + 2)

        # Sample this segment. Avoid duplicating the first point of subsequent segments.
        start_step = 0 if i == 0 else 1
        for s in range(start_step, steps_per_segment + 1):
            t = s / steps_per_segment
            q = _cr_point(p0, p1, p2, p3, t)
            out.append((q.x, q.y))

    return out

def lerp(a: Vector2, b: Vector2, t: float) -> Vector2:
    return a + (b - a) * t

def lerp_points(anchor_points, steps_per_segment=20, closed=False):
    """
    Returns a list of (x, y) tuples sampled linearly between anchor points.
    """
    pts = [Vector2(p) for p in anchor_points]
    n = len(pts)
    if n == 0:
        return []
    if n == 1:
        return [(pts[0].x, pts[0].y)]
    if steps_per_segment < 1:
        steps_per_segment = 1

    out = []

    seg_count = n if closed else n - 1

    for i in range(seg_count):
        a = pts[i]
        b = pts[(i + 1) % n] if closed else pts[i + 1]

        start_step = 0 if i == 0 else 1
        for s in range(start_step, steps_per_segment + 1):
            t = s / steps_per_segment
            q = lerp(a, b, t)
            out.append((q.x, q.y))

    return out

class Point:
    """A point defining a model that should be moved or not."""

    def __init__(self, position, name):
        self.position = position
        self.name = name

    def __repr__(self):
        x = int(self.position[0])
        y = int(self.position[1])
        return f"{self.name} [{x}, {y}]"
    
    def update(self, new_position):
        self.position = new_position

    def draw(self, surface: pygame.Surface, color=(110, 110, 110), size=6):
        x = int(self.position.x)
        y = int(self.position.y)
        half = size // 2
        rect = pygame.Rect(x - half, y - half, size, size)
        pygame.draw.rect(
            surface, 
            color, 
            rect,
            border_radius=1
        )

    def distance_to_reference(self, reference):
        diff = self.position - reference
        if diff.length_squared() == 0:
            return 0

        return diff.length() 

    def draw_text(self, surface, font, x_offset=0, y_offset=0):
        px = int(point.position.x + x_offset)
        py = int(point.position.y + y_offset)

        label = font.render(str(point), True, (220, 220, 220))
        surface.blit(label, (px + 10, py - label.get_height() // 2))


WINDOW_BG_COLOR = (32, 32, 38)
pygame.init()
pygame.display.set_caption("Animation Tool")
init_size = pygame.display.get_desktop_sizes()[0]
init_size = (2560, 1380)
print(init_size)
screen = pygame.display.set_mode(init_size, pygame.RESIZABLE)
small_font = pygame.font.Font(None, 18)
big_font = pygame.font.Font(None, 24)


DRAW_SURFACE_BG_COLOR = (45, 64, 54)

draw_surface_size = (1600, 900)
draw_surface = pygame.Surface(draw_surface_size, pygame.SRCALPHA)

clock = pygame.time.Clock()
running = True

passive_point_color = (110, 110, 110)
active_point_color = (180, 100, 100)
animation_point_color = (100, 200, 100)

TOP_MARGIN = 60
DRAW_SURFACE_MARGIN_X = - 400

controls = {
    pygame.K_t: {
        "value": True,
        "type": "bool",
        "desc": "Toggle Text (e.g. Coordinates)",
        "short_name": "render_text",
        "key_name": "T"
    },
    pygame.K_p: {
        "value": True,
        "type": "bool",
        "desc": "Toggle Model Points",
        "short_name": "render_model_points",
        "key_name": "P"
    },
    pygame.K_r: {
        "value": False,
        "type": "bool",
        "desc": "Start/Stop Recording",
        "short_name": "recording",
        "key_name": "R"
    },
    pygame.K_d: {
        "value": False,
        "type": "bool",
        "desc": "Discard Current Recording",
        "short_name": "discard_recording",
        "key_name": "D"
    },
    pygame.K_TAB: {
        "value": 0,
        "type": "cycle_options",
        "options": ["lerp", "catmull_rom"],
        "desc": "Change interpolation type",
        "short_name": "interpolation_type",
        "key_name": "TAB"
    },
    pygame.K_o: {
        "value": None,
        "type": "call_function",
        "function": open_file_dialog,
        "desc": "Load Model",
        "short_name": "load_model",
        "key_name": "O"
    },
    pygame.K_SPACE: {
        "value": False,
        "type": "bool",
        "desc": "Play Animation",
        "short_name": "play_animation",
        "key_name": "Space"
    }
}

class Animation:
    def __init__(self, anchor_points, duration, target_points):
        self.anchor_points = anchor_points
        self.duration = duration
        self.target_points = target_points

        self.is_playing = False
        self.time_passed = 0
        self.interpolation_method = "lerp"

        self.animation_points = []
        self.current_playthrough_points = []
        self._rebuild_animation_points()
        self.init_target_positions = []

    def _rebuild_animation_points(self):
        if len(self.anchor_points) < 2:
            return

        if self.interpolation_method == "lerp":
            anim_points = lerp_points(self.anchor_points, steps_per_segment=10)
        
        elif self.interpolation_method == "catmull_rom":
            anim_points = catmull_rom_points(self.anchor_points, steps_per_segment=10)
        
        else:
            print("unknown interpolation method", self.interpolation_method)
            return

        n_points = len(anim_points)
        time_per_point = self.duration / n_points

        self.animation_points = [(ix * time_per_point, point) for ix, point in enumerate(anim_points)]

    def add_anchor_point(self, anchor_point):
        self.anchor_points.append(anchor_point)
        self._rebuild_animation_points()

    def set_interpolation_method(self, method):
        if method != self.interpolation_method:
            self.interpolation_method = method
            self._rebuild_animation_points()

    def play(self):
        self.init_target_positions = [t.position for t in self.target_points]
        self.is_playing = True
        self.time_passed = 0
        self.current_playthrough_points = self.animation_points[:]

    def update_target_points_if_playing(self, dt):
        if not self.is_playing:
            return
        
        self.time_passed += dt

        for ix, (t, p) in enumerate(self.current_playthrough_points):
            if t >= self.time_passed:
                break


        for point in self.target_points:
            point.update(pygame.Vector2(p))

        if ix + 1 >= len(self.current_playthrough_points):
            self.is_playing = False
            
        else:
            self.current_playthrough_points = self.current_playthrough_points[ix + 1:]


    def draw_trajectory(self, surface):
        if self.is_playing:
            return 
        if self.animation_points:
            pygame.draw.lines(surface, (100, 100, 100), False, [p[1] for p in self.animation_points], width=2)



def screen_to_draw(x, y):
    draw_x_offset = screen.get_width() - draw_surface.get_width() + DRAW_SURFACE_MARGIN_X
    draw_y_offset = TOP_MARGIN

    return pygame.Vector2(x, y) - pygame.Vector2(draw_x_offset, draw_y_offset)

def draw_to_screen(x, y):
    draw_x_offset = screen.get_width() - draw_surface.get_width() + DRAW_SURFACE_MARGIN_X
    draw_y_offset = TOP_MARGIN

    return pygame.Vector2(x, y) + pygame.Vector2(draw_x_offset, draw_y_offset)

points_to_activity = {
    Point(pygame.Vector2(640, 360), "test p1"): False,
    Point(pygame.Vector2(800, 250), "test p2"): False,
}
active_points = []

current_animation = Animation(anchor_points=[], duration=1.0, target_points=[])
all_animations = [current_animation]

while running:
    dt = clock.tick(60) / 1000.0
 
    mouse_pos = pygame.mouse.get_pos()
    draw_surface_relative_mouse_pos = screen_to_draw(*mouse_pos)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            control = controls.get(event.key)
            if control is None:
                pass

            elif control["type"] == "bool":
                control["value"] = not control["value"]
            
            elif control["type"] == "call_function":
                result = control["function"]()
                control["value"] = result
                print("Function Result:", result)
            
            elif control["type"] == "cycle_options":
                control["value"] = (control["value"] + 1) % len(control["options"])
                print(control["options"][control["value"]])

            if event.key == pygame.K_SPACE:
                for animation in all_animations:
                    animation.play()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # todo: check if this is actually in the draw surface
            # dimensions for the different windows should be fixed so this can be done
            flip_activity = []
            for point in points_to_activity:
                if point.distance_to_reference(draw_surface_relative_mouse_pos) < 10:
                    flip_activity.append(point)

            for point in flip_activity:
                points_to_activity[point] = not points_to_activity[point]

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            # todo: check if in draw surface
            if len(active_points) > 0:
                next_animation_point = draw_surface_relative_mouse_pos
                current_animation.add_anchor_point(next_animation_point)

    control_name_to_value = {
        control["short_name"]: control["value"] if not control["type"] == "cycle_options" else control["options"][control["value"]]
        for control in controls.values()
    }
    active_points = [p for p, active in points_to_activity.items() if active]

    current_animation.target_points = active_points
    current_animation.set_interpolation_method(control_name_to_value["interpolation_type"])

    # --- draw ---
    screen.fill(WINDOW_BG_COLOR)
    draw_surface.fill(DRAW_SURFACE_BG_COLOR)

    if control_name_to_value["render_model_points"]:
        for point, active in points_to_activity.items():
            color = active_point_color if active else passive_point_color
            point.draw(draw_surface, color=color)

    for animation in all_animations:
        animation.update_target_points_if_playing(dt)

    current_animation.draw_trajectory(draw_surface)
    #for point in current_animation.points:
    #    point.draw(draw_surface, color=animation_point_color)

    screen.blit(draw_surface, (screen.get_width() - draw_surface.get_width() + DRAW_SURFACE_MARGIN_X, TOP_MARGIN))

    if control_name_to_value["render_text"]:
        # Adding text afterwards
        for point in points_to_activity:
            px, py = draw_to_screen(*point.position)
            label = small_font.render(str(point), True, (220, 220, 220))
            screen.blit(label, (px + 10, py - label.get_height() // 2))

    # Adding legend
    legend = pygame.Surface((400, 900), pygame.SRCALPHA)
    pygame.draw.rect(legend, (40, 40, 40, 255), legend.get_rect())
    legend_y_offset = 60
    for key, state in controls.items():
        label = big_font.render(f"{state['key_name']}     {state['desc']}", True, (220, 220, 220))
        legend.blit(label, (25, legend_y_offset))
        legend_y_offset += 75

    screen.blit(legend, (100, TOP_MARGIN))

    # Adding timeline
    timeline = pygame.Surface((2060, 340))
    timeline.fill((40, 40, 40))
    screen.blit(timeline, (100, 1000))

    pygame.display.flip()

pygame.quit()