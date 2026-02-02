import pygame
import os
from config import *

class Assets:
    _instance = None
    
    def __init__(self):
        self.images = {}
        self.masks = {}
        self.fonts = {}
        
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = Assets()
        return cls._instance
        
    def load_images(self):
        def load(name, filename, size=None, create_mask=False):
            path = os.path.join("assets", filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                if size:
                    img = pygame.transform.scale(img, size)
                self.images[name] = img
                
                if create_mask:
                    self.masks[name] = pygame.mask.from_surface(img)
            else:
                print(f"Warning: Asset {path} not found. Using fallback.")
                s = pygame.Surface(size if size else (TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                s.fill((255, 0, 255, 128))
                self.images[name] = s
                if create_mask:
                    self.masks[name] = pygame.mask.from_surface(s)

        def load_scaled(name, filename, target_height, create_mask=False):
            """Load image and scale to target height while keeping aspect ratio"""
            path = os.path.join("assets", filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                
                # Calculate scale factor to fit target height
                original_width, original_height = img.get_size()
                scale_factor = target_height / original_height
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                
                img = pygame.transform.scale(img, (new_width, new_height))
                self.images[name] = img
                
                if create_mask:
                    self.masks[name] = pygame.mask.from_surface(img)
            else:
                print(f"Warning: Asset {path} not found. Using fallback.")
                s = pygame.Surface((target_height, target_height), pygame.SRCALPHA)
                s.fill((255, 0, 255, 128))
                self.images[name] = s
                if create_mask:
                    self.masks[name] = pygame.mask.from_surface(s)

        # Restaurant interiors
        resto_width = RESTAURANT_WIDTH * TILE_SIZE
        resto_height = RESTAURANT_HEIGHT * TILE_SIZE
        load("interior_tacos", "floor_tacos.png", (resto_width, resto_height))
        load("interior_kebab", "floor_kebab.png", (resto_width, resto_height))
        
        # Street tiles
        load("sidewalk", "sidewalk.png", (TILE_SIZE, TILE_SIZE))
        load("road", "street.png", (TILE_SIZE, TILE_SIZE))
        load("wall", "wall.png", (TILE_SIZE, TILE_SIZE))
        
        # Facades
        facade_w = 6 * TILE_SIZE
        facade_h = 3 * TILE_SIZE
        load("facade_tacos", "facade_tacos.png", (facade_w, facade_h))
        load("facade_kebab", "facade_kebab.png", (facade_w, facade_h))
        
        # Door
        load("door", "door.png", (TILE_SIZE, TILE_SIZE))
        
        # Characters - scale to height while keeping aspect ratio
        char_height = int(TILE_SIZE * 1.8)  # Larger characters for better visibility
        load_scaled("player1", "player1.png", char_height, create_mask=True)
        load_scaled("player2", "player2.png", char_height, create_mask=True)
        load_scaled("client", "client.png", char_height, create_mask=True)
        
    def get_image(self, name):
        return self.images.get(name)
        
    def get_mask(self, name):
        return self.masks.get(name)
