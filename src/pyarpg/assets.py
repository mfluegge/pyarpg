import pygame
from pyarpg.config import IMG_DIR
from pyarpg.config import SOUNDS_DIR

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
    }

    img_dict["fireball"].set_alpha(180)
    img_dict["drop_globe"].set_alpha(160)

    _add_flash_images(img_dict)

    return img_dict

def load_sounds(sounds_dir):
    sound_dict = {
        "enemy_hit_sound": pygame.Sound(sounds_dir / "hit_sound_1.wav")
    }

    sound_dict["enemy_hit_sound"].set_volume(0.07)

    return sound_dict

print("Loading Sprites")
SPRITE_DICT = load_images(IMG_DIR)

print("Loading Sounds")
SOUNDS_DICT = load_sounds(SOUNDS_DIR)