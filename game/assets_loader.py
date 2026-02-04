import pygame
import os
import sys
import xml.etree.ElementTree as ET
from config import *


def get_base_path():
    """Retourne le chemin de base pour les ressources."""
    if getattr(sys, 'frozen', False):
        # Exécutable PyInstaller
        exe_dir = os.path.dirname(sys.executable)
        
        if sys.platform == 'darwin':
            # macOS app bundle - essayer plusieurs emplacements
            # Structure: SnackAnarchy.app/Contents/MacOS/SnackAnarchy
            # Les assets peuvent être dans:
            # 1. Contents/Resources/
            # 2. Contents/MacOS/ (à côté de l'exe)
            # 3. Contents/Frameworks/
            
            resources_path = os.path.realpath(os.path.join(exe_dir, '..', 'Resources'))
            if os.path.exists(os.path.join(resources_path, 'assets')):
                return resources_path
            
            # Fallback: à côté de l'exécutable
            if os.path.exists(os.path.join(exe_dir, 'assets')):
                return exe_dir
            
            # Dernier recours: Resources quand même
            return resources_path
        else:
            # Windows/Linux : à côté de l'exécutable
            return os.path.realpath(exe_dir)
    else:
        # Mode développement : racine du projet
        return os.path.realpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_resource_path(relative_path):
    """Retourne le chemin absolu vers une ressource, compatible PyInstaller."""
    base = get_base_path()
    full_path = os.path.join(base, relative_path)
    
    # Si le fichier n'existe pas, essayer d'autres emplacements en mode frozen
    if not os.path.exists(full_path) and getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        
        # Essayer à côté de l'exécutable
        alt_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(alt_path):
            return os.path.realpath(alt_path)
        
        # macOS: essayer dans Resources
        if sys.platform == 'darwin':
            resources_path = os.path.realpath(os.path.join(exe_dir, '..', 'Resources', relative_path))
            if os.path.exists(resources_path):
                return resources_path
    
    return os.path.realpath(full_path)

class TMXCollisionLoader:
    """Parse les fichiers TMX Tiled pour extraire les zones de collision"""
    
    @staticmethod
    def load_collisions(tmx_path, target_width, target_height):
        """
        Charge les rectangles de collision depuis un fichier TMX.
        Les coordonnées sont mises à l'échelle vers target_width x target_height.
        
        Returns: Liste de pygame.Rect pour les zones NON walkables
        """
        collisions = []
        
        if not os.path.exists(tmx_path):
            print(f"Warning: TMX file {tmx_path} not found")
            return collisions
            
        try:
            tree = ET.parse(tmx_path)
            root = tree.getroot()
            
            # Récupérer les dimensions originales de la carte
            map_width = int(root.get('width', 88))
            map_height = int(root.get('height', 48))
            tile_width = int(root.get('tilewidth', 32))
            tile_height = int(root.get('tileheight', 32))
            
            original_width = map_width * tile_width
            original_height = map_height * tile_height
            
            # Facteurs d'échelle
            scale_x = target_width / original_width
            scale_y = target_height / original_height
            
            # Chercher le groupe d'objets "collision"
            for objectgroup in root.findall('.//objectgroup'):
                if objectgroup.get('name', '').lower() == 'collision':
                    for obj in objectgroup.findall('object'):
                        x = float(obj.get('x', 0))
                        y = float(obj.get('y', 0))
                        width = float(obj.get('width', 0))
                        height = float(obj.get('height', 0))
                        
                        # Ignorer les objets sans dimensions (points)
                        if width <= 0 or height <= 0:
                            continue
                        
                        # Mettre à l'échelle
                        scaled_rect = pygame.Rect(
                            int(x * scale_x),
                            int(y * scale_y),
                            int(width * scale_x),
                            int(height * scale_y)
                        )
                        collisions.append(scaled_rect)
                        
            print(f"Loaded {len(collisions)} collision zones from {tmx_path}")
            
        except ET.ParseError as e:
            print(f"Error parsing TMX file: {e}")
        except Exception as e:
            print(f"Error loading TMX collisions: {e}")
            
        return collisions


class Assets:
    _instance = None
    
    def __init__(self):
        self.images = {}
        self.masks = {}
        self.fonts = {}
        self.collision_maps = {}  # Stocke les collisions TMX
        
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = Assets()
        return cls._instance
        
    def load_images(self):
        # Debug: afficher le chemin de base
        base = get_base_path()
        assets_dir = get_resource_path("assets")
        print(f"[DEBUG] Base path: {base}")
        print(f"[DEBUG] Assets dir: {assets_dir}")
        print(f"[DEBUG] Assets dir existe: {os.path.exists(assets_dir)}")
        if os.path.exists(assets_dir):
            print(f"[DEBUG] Contenu assets: {os.listdir(assets_dir)[:5]}...")
        
        def load(name, filename, size=None, create_mask=False):
            path = get_resource_path(os.path.join("assets", filename))
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
            path = get_resource_path(os.path.join("assets", filename))
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
        
        # Charger les collisions TMX pour tacos et kebab
        self.collision_maps["tacos"] = TMXCollisionLoader.load_collisions(
            get_resource_path(os.path.join("assets", "floor_tacos.tmx")), resto_width, resto_height
        )
        self.collision_maps["kebab"] = TMXCollisionLoader.load_collisions(
            get_resource_path(os.path.join("assets", "floor_kebab.tmx")), resto_width, resto_height
        )
        
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
        
        # Players - versions droite et gauche
        load_scaled("player1", "player1.png", char_height, create_mask=True)
        load_scaled("player1_left", "player1-left.png", char_height, create_mask=True)
        load_scaled("player2", "player2.png", char_height, create_mask=True)
        load_scaled("player2_left", "player2-left.png", char_height, create_mask=True)
        
        # Clients - 3 types différents
        load_scaled("client", "client.png", char_height, create_mask=True)
        load_scaled("client1", "client1.png", char_height, create_mask=True)
        load_scaled("client2", "client2.png", char_height, create_mask=True)
        
    def get_image(self, name):
        return self.images.get(name)
        
    def get_mask(self, name):
        return self.masks.get(name)
    
    def get_collisions(self, zone_name):
        """Retourne les rectangles de collision pour une zone donnée"""
        return self.collision_maps.get(zone_name, [])