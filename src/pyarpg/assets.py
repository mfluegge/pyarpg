import pygame
from pyarpg.config import IMG_DIR
from pyarpg.config import SOUNDS_DIR
from pyarpg.config import FONT_DIR


def mute(surface, mult=180, alpha=240):
    out = surface.copy()
    out.fill((mult, mult, mult), special_flags=pygame.BLEND_RGB_MULT)
    out.set_alpha(alpha)
    return out

def fake_desaturate(surface, strength=0.5):
    out = surface.copy()
    gray = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    gray.fill((128, 128, 128, int(255 * strength)))
    out.blit(gray, (0, 0))
    return out

def _add_flash_images(img_dict, suffix="_flash"):
    new_imgs = {}
    for img_name, img in img_dict.items():
        flash_image = img.copy()
        flash_image.fill((40, 40, 40), special_flags=pygame.BLEND_RGB_ADD)

        new_imgs[img_name + suffix] = flash_image
    
    img_dict.update(new_imgs)

def load_images(img_dir):
    img_dict = {
        "player": pygame.image.load(img_dir / "player3.png").convert_alpha(),
        "fireball": pygame.image.load(img_dir / "fireball.png").convert_alpha(),
        "dummy": pygame.image.load(img_dir / "dummy.png").convert_alpha(),
        "melee": pygame.image.load(img_dir / "melee.png").convert_alpha(),
        "drop_globe": pygame.image.load(img_dir / "monster_globe_drop_test.png").convert_alpha(),
        "empty_skill_slot": pygame.transform.scale(pygame.image.load(img_dir / "empty_skill_slot.png").convert_alpha(), (48, 48)),
        "blue_bean_ellipsis": pygame.image.load(img_dir / "blue_bean_ellipsis.png").convert_alpha(),
        "ring_of_fire": mute(pygame.transform.scale(pygame.image.load(img_dir / "ring_of_fire_no_outline.png").convert_alpha(), (64 * 12 * 4, 256))),
        "tree1": pygame.image.load(img_dir / "tree_1.png").convert_alpha(),
        "portal": pygame.image.load(img_dir / "portal1.png").convert_alpha(),
    }

    img_dict["fireball"].set_alpha(180)
    img_dict["drop_globe"].set_alpha(160)
    #img_dict["empty_skill_slot"].set_alpha(120)

    _add_flash_images(img_dict)

    return img_dict

def load_sounds(sounds_dir):
    sound_dict = {
        "enemy_hit_sound": pygame.Sound(sounds_dir / "hit_sound_1.wav")
    }

    sound_dict["enemy_hit_sound"].set_volume(0.07)

    return sound_dict

def load_fonts(font_dir):
    font_dict = {
        "press_start_12": pygame.font.Font(font_dir / "PrStart.ttf", 12),
        "press_start_16": pygame.font.Font(font_dir / "PrStart.ttf", 16),
        "press_start_18": pygame.font.Font(font_dir / "PrStart.ttf", 18),
        "press_start_24": pygame.font.Font(font_dir / "PrStart.ttf", 24),
        "press_start_30": pygame.font.Font(font_dir / "PrStart.ttf", 30),
    }

    return font_dict


print("Loading Sprites")
SPRITE_DICT = load_images(IMG_DIR)

print("Loading Sounds")
SOUNDS_DICT = load_sounds(SOUNDS_DIR)

print("Loading Fonts")
FONT_DICT = load_fonts(FONT_DIR)


