import pygame
from PySide6.QtWidgets import QApplication, QFileDialog
import sys

_qt_app = None

def open_file_dialog():
    global _qt_app
    if _qt_app is None:
        _qt_app = QApplication(sys.argv)

    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select a file",
        "",
        "All Files (*.*)"
    )
    return file_path


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
        pygame.draw.rect(surface, color, rect, border_radius=1)

    def distance_to_reference(self, reference: pygame.Vector2):
        diff = self.position - reference
        if diff.length_squared() == 0:
            return 0
        return diff.length()

    def draw_text(self, screen_surface, font, screen_pos: pygame.Vector2):
        label = font.render(str(self), True, (220, 220, 220))
        screen_surface.blit(label, (int(screen_pos.x) + 10, int(screen_pos.y) - label.get_height() // 2))


WINDOW_BG_COLOR = (32, 32, 38)
DRAW_SURFACE_BG_COLOR = (45, 64, 54)

pygame.init()
pygame.display.set_caption("Animation Tool")
init_size = (2560, 1380)
screen = pygame.display.set_mode(init_size, pygame.RESIZABLE)

small_font = pygame.font.Font(None, 18)
big_font = pygame.font.Font(None, 24)

WORLD_SIZE = pygame.Vector2(1600, 900)     # max allowed dimensions / world size
PANEL_SIZE = pygame.Vector2(1600, 900)     # fixed size of the draw panel on screen

draw_surface = pygame.Surface((int(WORLD_SIZE.x), int(WORLD_SIZE.y)), pygame.SRCALPHA)

clock = pygame.time.Clock()
running = True

passive_point_color = (110, 110, 110)
active_point_color = (180, 100, 100)

TOP_MARGIN = 60
DRAW_SURFACE_MARGIN_X = -400

# --- Camera / Zoom / Pan state ---
# viewport_rect is in WORLD coordinates (what part of draw_surface you see)
viewport_rect = pygame.Rect(0, 0, int(WORLD_SIZE.x), int(WORLD_SIZE.y))  # start fully zoomed out
zoom = 1.0                      # 1.0 = whole world fits exactly (viewport = world)
MAX_ZOOM = 6.0                  # zoom in limit
ZOOM_STEP = 1.1                 # wheel tick multiplier

rmb_down = False
rmb_dragging = False
rmb_down_screen_pos = pygame.Vector2(0, 0)
DRAG_THRESHOLD_PX = 10
last_mouse_screen = pygame.Vector2(0, 0)

def clamp_viewport_to_world():
    """Keep viewport inside [0..WORLD_SIZE]."""
    # size must never exceed world size
    if viewport_rect.w > WORLD_SIZE.x:
        viewport_rect.w = int(WORLD_SIZE.x)
    if viewport_rect.h > WORLD_SIZE.y:
        viewport_rect.h = int(WORLD_SIZE.y)

    # clamp position
    viewport_rect.x = max(0, min(viewport_rect.x, int(WORLD_SIZE.x - viewport_rect.w)))
    viewport_rect.y = max(0, min(viewport_rect.y, int(WORLD_SIZE.y - viewport_rect.h)))

def current_scale() -> float:
    """How many screen panel pixels per world pixel."""
    # panel is always PANEL_SIZE, viewport is what we show from the world
    return PANEL_SIZE.x / viewport_rect.w  # same as PANEL_SIZE.y / viewport_rect.h if aspect matches

def panel_top_left_on_screen() -> pygame.Vector2:
    draw_x_offset = screen.get_width() - PANEL_SIZE.x + DRAW_SURFACE_MARGIN_X
    draw_y_offset = TOP_MARGIN
    return pygame.Vector2(draw_x_offset, draw_y_offset)

def screen_to_panel_local(mx, my) -> tuple[pygame.Vector2, bool]:
    """Convert screen mouse -> local coords inside the draw panel."""
    tl = panel_top_left_on_screen()
    local = pygame.Vector2(mx, my) - tl
    inside = (0 <= local.x < PANEL_SIZE.x) and (0 <= local.y < PANEL_SIZE.y)
    return local, inside

def panel_local_to_world(panel_local: pygame.Vector2) -> pygame.Vector2:
    """Panel-local -> world coords, using viewport + scale."""
    s = current_scale()
    world_x = viewport_rect.x + panel_local.x / s
    world_y = viewport_rect.y + panel_local.y / s
    return pygame.Vector2(world_x, world_y)

def screen_to_world(mx, my) -> tuple[pygame.Vector2 | None, bool]:
    """Screen mouse -> world coords. Returns (world_pos, inside_panel)."""
    panel_local, inside = screen_to_panel_local(mx, my)
    if not inside:
        return None, False
    return panel_local_to_world(panel_local), True

def world_to_screen(point_world: pygame.Vector2) -> pygame.Vector2:
    """World coords -> screen coords (pixel on the main window)."""
    tl = panel_top_left_on_screen()
    s = current_scale()
    panel_local = (point_world - pygame.Vector2(viewport_rect.topleft)) * s
    return tl + panel_local

def set_zoom_keeping_world_point_fixed(new_zoom: float, fixed_world_point: pygame.Vector2):
    """Change zoom, adjusting viewport so fixed_world_point stays at the same spot on the panel."""
    global zoom, viewport_rect
    new_zoom = max(1.0, min(MAX_ZOOM, new_zoom))
    if abs(new_zoom - zoom) < 1e-9:
        return

    # Compute new viewport size (world visible area shrinks when zoom increases)
    # At zoom=1 -> viewport == world size; at zoom>1 -> viewport smaller.
    new_w = int(round(WORLD_SIZE.x / new_zoom))
    new_h = int(round(WORLD_SIZE.y / new_zoom))

    # Keep aspect locked to world/panel aspect:
    new_w = max(1, min(new_w, int(WORLD_SIZE.x)))
    new_h = max(1, min(new_h, int(WORLD_SIZE.y)))

    # Where is fixed_world_point inside current viewport (as ratio)?
    old = viewport_rect.copy()
    if old.w <= 0 or old.h <= 0:
        return

    rx = (fixed_world_point.x - old.x) / old.w
    ry = (fixed_world_point.y - old.y) / old.h

    # Build new viewport so that same relative point remains under cursor
    viewport_rect.w = new_w
    viewport_rect.h = new_h
    viewport_rect.x = int(round(fixed_world_point.x - rx * viewport_rect.w))
    viewport_rect.y = int(round(fixed_world_point.y - ry * viewport_rect.h))

    zoom = new_zoom
    clamp_viewport_to_world()

def pan_by_screen_delta(delta_screen: pygame.Vector2):
    """Pan viewport by a screen-space mouse delta (drag)."""
    # dragging right should move camera left (world appears to follow cursor)
    s = current_scale()
    dx_world = -delta_screen.x / s
    dy_world = -delta_screen.y / s
    viewport_rect.x += int(round(dx_world))
    viewport_rect.y += int(round(dy_world))
    clamp_viewport_to_world()


controls = {
    pygame.K_t: {"value": True, "type": "bool", "desc": "Toggle Text (e.g. Coordinates)", "short_name": "render_text", "key_name": "T"},
    pygame.K_p: {"value": True, "type": "bool", "desc": "Toggle Model Points", "short_name": "render_model_points", "key_name": "P"},
    pygame.K_r: {"value": False, "type": "bool", "desc": "Start/Stop Recording", "short_name": "recording", "key_name": "R"},
    pygame.K_d: {"value": False, "type": "bool", "desc": "Discard Current Recording", "short_name": "discard_recording", "key_name": "D"},
    pygame.K_TAB: {"value": 0, "type": "cycle_options", "options": ["lerp", "bezier_cubic", "catmull_rom"], "desc": "Change interpolation type", "short_name": "interpolation_type", "key_name": "TAB"},
    pygame.K_o: {"value": None, "type": "call_function", "function": open_file_dialog, "desc": "Load Model", "short_name": "load_model", "key_name": "O"},
}

points_to_activity = {
    Point(pygame.Vector2(640, 360), "test p1"): False,
    Point(pygame.Vector2(800, 250), "test p2"): False,
}

while running:
    dt = clock.tick(60) / 1000.0

    mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
    world_mouse, mouse_in_panel = screen_to_world(mouse_pos.x, mouse_pos.y)

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

        # --- Zoom (wheel) ---
        # pygame 2: MOUSEWHEEL is best
        elif event.type == pygame.MOUSEWHEEL:
            if mouse_in_panel and world_mouse is not None:
                if event.y > 0:
                    set_zoom_keeping_world_point_fixed(zoom * ZOOM_STEP, world_mouse)
                elif event.y < 0:
                    set_zoom_keeping_world_point_fixed(zoom / ZOOM_STEP, world_mouse)

        # --- LMB select point (uses WORLD coords now) ---
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if mouse_in_panel and world_mouse is not None:
                flip_activity = []
                for point in points_to_activity:
                    if point.distance_to_reference(world_mouse) < 10:
                        flip_activity.append(point)
                for point in flip_activity:
                    points_to_activity[point] = not points_to_activity[point]

        # --- RMB drag-to-pan (drag only; click remains reserved) ---
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if mouse_in_panel:
                rmb_down = True
                rmb_dragging = False
                rmb_down_screen_pos = pygame.Vector2(pygame.mouse.get_pos())
                last_mouse_screen = pygame.Vector2(pygame.mouse.get_pos())

        elif event.type == pygame.MOUSEMOTION:
            if rmb_down and mouse_in_panel:
                cur = pygame.Vector2(event.pos)
                if not rmb_dragging:
                    if (cur - rmb_down_screen_pos).length_squared() >= DRAG_THRESHOLD_PX * DRAG_THRESHOLD_PX:
                        rmb_dragging = True

                if rmb_dragging:
                    delta = cur - last_mouse_screen
                    pan_by_screen_delta(delta)
                last_mouse_screen = cur

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            # If rmb_dragging is False here, it was a normal RMB click -> reserved for later use.
            rmb_down = False
            rmb_dragging = False

    control_name_to_value = {c["short_name"]: c["value"] for c in controls.values()}

    # --- draw world ---
    screen.fill(WINDOW_BG_COLOR)
    draw_surface.fill(DRAW_SURFACE_BG_COLOR)

    if control_name_to_value["render_model_points"]:
        for point, active in points_to_activity.items():
            color = active_point_color if active else passive_point_color
            point.draw(draw_surface, color=color)

    # --- render camera view into fixed-size panel ---
    # subsurface must be fully inside draw_surface; clamp ensures that
    view = draw_surface.subsurface(viewport_rect).copy()
    if viewport_rect.size != (int(PANEL_SIZE.x), int(PANEL_SIZE.y)):
        view = pygame.transform.smoothscale(view, (int(PANEL_SIZE.x), int(PANEL_SIZE.y)))

    panel_tl = panel_top_left_on_screen()
    screen.blit(view, (int(panel_tl.x), int(panel_tl.y)))

    # --- screen-space text labels (must use world->screen transform) ---
    if control_name_to_value["render_text"]:
        scale = current_scale()
        panel_tl = panel_top_left_on_screen()

        for point in points_to_activity:
            # 1. World-space culling (cheap + important)
            if not viewport_rect.collidepoint(point.position):
                continue

            # 2. World -> screen
            p_screen = world_to_screen(point.position)

            label = small_font.render(str(point), True, (220, 220, 220))
            label_rect = label.get_rect()
            label_rect.topleft = (p_screen.x + 10, p_screen.y - label_rect.height // 2)

            # 3. Panel clipping
            panel_rect = pygame.Rect(
                panel_tl.x,
                panel_tl.y,
                PANEL_SIZE.x,
                PANEL_SIZE.y,
            )

            if panel_rect.contains(label_rect):
                screen.blit(label, label_rect)

        # optional: show mouse world coords
        if mouse_in_panel and world_mouse is not None:
            label = small_font.render(
                f"world: ({world_mouse.x:.1f}, {world_mouse.y:.1f})  zoom: {zoom:.2f}",
                True,
                (220, 220, 220),
            )
            screen.blit(label, (int(panel_tl.x) + 10, int(panel_tl.y) + 10))

    # --- legend ---
    legend = pygame.Surface((400, 900), pygame.SRCALPHA)
    pygame.draw.rect(legend, (40, 40, 40, 255), legend.get_rect())
    legend_y_offset = 60
    for key, state in controls.items():
        label = big_font.render(f"{state['key_name']}     {state['desc']}", True, (220, 220, 220))
        legend.blit(label, (25, legend_y_offset))
        legend_y_offset += 75
    screen.blit(legend, (100, TOP_MARGIN))

    # --- timeline ---
    timeline = pygame.Surface((2060, 340))
    timeline.fill((40, 40, 40))
    screen.blit(timeline, (100, 1000))

    pygame.display.flip()

pygame.quit()