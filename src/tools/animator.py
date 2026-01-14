import pygame
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

    def draw_text(self, surface, font, world_scalar_x, world_scalar_y):
        px = int(point.position.x * world_scalar_x)
        py = int(point.position.y * world_scalar_y)

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
        "options": ["lerp", "bezier_cubic", "catmull_rom"],
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
    }
}

points_to_activity = {
    Point(pygame.Vector2(640, 360), "test p1"): False,
    Point(pygame.Vector2(800, 250), "test p2"): False,
}

while running:
    dt = clock.tick(60) / 1000.0
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

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # todo: check if this is actually in the draw surface
            # dimensions for the different windows should be fixed so this can be done
            click_pos = inverse_scale_mouse_pos(draw_surface, screen, *pygame.mouse.get_pos())
            flip_activity = []
            for point in points_to_activity:
                if point.distance_to_reference(click_pos) < 10:
                    flip_activity.append(point)

            for point in flip_activity:
                points_to_activity[point] = not points_to_activity[point]

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            # todo: check if in game window
            next_animation_point = pygame.Vector2(pygame.mouse.get_pos())


    control_name_to_value = {
        control["short_name"]: control["value"]
        for control in controls.values()
    }
    active_points = [p for p, active in points_to_activity.items() if active]

    # --- draw ---
    screen.fill(WINDOW_BG_COLOR)
    draw_surface.fill(DRAW_SURFACE_BG_COLOR)

    if control_name_to_value["render_model_points"]:
        for point, active in points_to_activity.items():
            color = active_point_color if active else passive_point_color
            point.draw(draw_surface, color=color)

    # Scaling draw surface
    #scaled = pygame.transform.scale(draw_surface, screen.get_size())
    #screen.blit(scaled, (0, 0))
    screen.blit(draw_surface, (screen.get_width() - draw_surface.get_width() -400, 0 + 100))

    if control_name_to_value["render_text"]:
        # Adding text afterwards
        world_scalar_x = screen.get_width() / draw_surface.get_width()
        world_scalar_y = screen.get_height() / draw_surface.get_height()
        for point in points_to_activity:
            point.draw_text(screen, small_font, world_scalar_x, world_scalar_y)


    # Adding legend
    legend = pygame.Surface((400, 900), pygame.SRCALPHA)
    pygame.draw.rect(legend, (40, 40, 40, 255), legend.get_rect())
    x_offset = 25
    y_offset = 60
    for key, state in controls.items():
        label = big_font.render(f"{state['key_name']}     {state['desc']}", True, (220, 220, 220))
        legend.blit(label, (x_offset, y_offset))
        y_offset += 75

    screen.blit(legend, (100, 100))

    pygame.display.flip()

pygame.quit()