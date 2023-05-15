import pygame as pg
import os, json

def load_spritesheet(path: str, scale=1, colorkey=(0, 0, 0)) -> list[pg.Surface]:
    '''
        path is the path of a .png file of the following format: `{directory}/{spritesheet_name}-{rows}-{cols}.png`
        
        the `spritesheet_name` specifies the name of the spritesheet

        the `row` specifies the number of rows in the spritesheet and `col` specifies the number of columns in the spritesheet

        returns a list of all of the sprites cropped according the `row` and `col`
    '''
    spritesheet = pg.image.load(path).convert()
    width, height = spritesheet.get_size()
    rows, cols = path.split('-')[1], path.split('-')[2]
    sprite_width, sprite_height = width//cols, height//rows

    sprites : list[pg.Surface] = []
    for row in range(rows):
        for col in range(cols):
            sprite = pg.Surface((sprite_width, sprite_height))
            sprite.blit(spritesheet, (-col * sprite_width, -row * sprite_height))
            width, height = sprite.get_size()
            sprite = pg.transform.scale(sprite, (scale * width, scale * height))
            if colorkey:
                sprite.set_colorkey(colorkey)
            sprites.append(sprite) 

    return sprites

def load_animations(path: str, scale=1, colorkey=(0, 0, 0)) -> dict[str, list[pg.Surface]]:
    '''
        path is a directory which contains many spritesheets, each of which is a .png file of the following format: `{directory}/{spritesheet_name}-{rows}-{cols}.png`
        
        the `spritesheet_name` specifies the name of the spritesheet

        the `row` specifies the number of rows in the spritesheet and `col` specifies the number of columns in the spritesheet

        returns a dictionary which can be keyed using `spritesheet_name` which yields a list of sprites
    '''
    animations_dir = os.listdir(path)
    animations : dict[str, list[pg.Surface]] = {}
    for animation in animations_dir:
        animations[animation.split('-')[0]] = load_spritesheet(os.path.join(path, animation), scale, colorkey)
    
    return animations

def load_sprites(path: str, scale=1, colorkey=(0, 0, 0)) -> dict[str, pg.Surface]:
    '''
        path is a directory containing different png files of the format: `{sprite_name}.png`
        
        the `sprite_name` specifies the name of the sprite

        returns a dict of the sprites which can be keyed with their `sprite_name`
    '''

    sprites_dir = os.listdir(path)
    
    sprites : dict[str, pg.Surface] = {}
    for sprite_img in sprites_dir:
        if sprite_img.split('.')[1] == 'png':
            sprite = pg.image.load(os.path.join(path, sprite_img)).convert()
            width, height = sprite.get_size()
            sprite = pg.transform.scale(sprite, (scale * width, scale * height))
            if colorkey:
                sprite.set_colorkey(colorkey)
            sprites[sprite_img.split('.')[0]] = sprite
    
    return sprites

def load_sprite_groups(path: str, scale=1, colorkey=(0, 0, 0)) -> dict[str, dict[str, pg.Surface]]:
    '''
        path is a directory containing directories `{dir_name}` which themselves contain .png files of the format: `{sprite_name}.png`
        
        the `dir_name` specifies the name of the sprite group

        the `sprite_name` specifies the name of the sprite

        returns a dict of sprite groups which can be keyed using `dir_name`. each sprite group is itself a dict which can be keyed with `sprite_name`
    '''

    sprite_group_dir = os.listdir(path)
    sprite_groups : dict[str, dict[str, pg.Surface]] = {}
    for sprite_group in sprite_group_dir:
        sprite_groups[sprite_group] = load_sprites(os.path.join(path, sprite_group), scale, colorkey)
    
    return sprite_group

def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)