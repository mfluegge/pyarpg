import pygame
from pyarpg.config import IMG_DIR

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
    }

    img_dict["fireball"].set_alpha(180)

    _add_flash_images(img_dict)

    return img_dict

print("Loading Assets")
IMAGE_DICT = load_images(IMG_DIR)
