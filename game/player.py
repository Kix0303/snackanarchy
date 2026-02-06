import pygame
import time
import math
from config import *
from game.equipment import Fryer, Spit, Menu, Register, Toilets
from game.assets_loader import Assets
from game.inventory import PlayerInventory, FoodStock
from game.animation import WalkAnimation, AttackAnimation, AnimationManager, FloatingText, ServeAnimation
from game.audio import play_sound
from game.missions import MissionManager

class Player(pygame.sprite.Sprite):
    def __init__(self, id, x, y, color, start_zone="street", username=None):
        super().__init__()
        self.id = id
        self.color = color
        self.username = username or f"Joueur {id}"
        
        assets = Assets.get()
        sprite_name = f"player{id}"
        sprite_name_left = f"player{id}_left"
        
        # Charger les sprites droite et gauche
        self.image_right = assets.get_image(sprite_name)
        self.image_left = assets.get_image(sprite_name_left)
        self.mask = assets.get_mask(sprite_name)
        
        # Fallback pour le sprite gauche si non trouvé
        if not self.image_left and self.image_right:
            self.image_left = pygame.transform.flip(self.image_right, True, False)
        
        # Fallback complet si aucun sprite
        if not self.image_right:
            self.image_right = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            self.image_right.fill(color)
            self.image_left = pygame.transform.flip(self.image_right, True, False)
            self.mask = pygame.mask.from_surface(self.image_right)
            
        # Image actuelle (par défaut: droite)
        self.image = self.image_right
        self.base_image = self.image_right
            
        # Use actual image size for rect
        self.rect = self.image.get_rect()
        self.rect.topleft = (x * TILE_SIZE, y * TILE_SIZE)
        self.speed = PLAYER_SPEED
        self.vx = 0
        self.vy = 0
        
        self.current_zone = start_zone
        self.home_zone = start_zone  # Zone de départ (son restaurant)
        
        self.money = 0
        self.reputation = 50
        
        self.equipment = {
            "fryer": Fryer(),
            "spit": Spit(),
            "menu": Menu(),
            "register": Register(),
            "toilets": Toilets()
        }
        
        self.current_client = None
        self.active_minigame = None
        self.serve_animation = None  # Animation aller cuisine -> retour client
        self.active_sabotages = []
        
        # Nouveau: Inventaire et stock
        self.inventory = PlayerInventory(id)
        restaurant_type = 'tacos' if start_zone == 'tacos' else 'kebab'
        self.food_stock = FoodStock(restaurant_type)
        
        # Nouveau: Animations
        self.walk_animation = WalkAnimation(self.base_image)
        self.attack_animation = None
        self.animation_manager = AnimationManager()
        self.bob_offset = 0
        
        # Direction du joueur
        self.facing = 'right'
        self.is_moving = False
        
        # Attaque
        self.attack_cooldown = 0
        self.attack_cooldown_duration = 0.5
        
        # Sons de pas
        self.last_footstep = 0
        self.footstep_interval = 0.3
        
        # Statistiques de la partie (pour l'historique)
        self.clients_served = 0
        self.tacos_served = 0
        self.kebabs_served = 0
        self.attacks_made = 0
        self.sabotages_done = 0
        self.missions_completed = 0
        self.cleaning_done = 0
        
        # Système de nettoyage (balai)
        self.sweep_cooldown = 0
        self.sweep_cooldown_duration = 15.0  # 15 secondes de cooldown
        self.is_sweeping = False
        self.sweep_animation_timer = 0
        self.sweep_animation_duration = 1.0  # 1 seconde d'animation
        
        # Système de missions
        self.mission_manager = MissionManager(self)
        
    def move(self, dx, dy):
        if self.active_minigame: return
        if self.serve_animation and not self.serve_animation.completed: return
        if self.attack_animation and not self.attack_animation.completed: return
        
        self.vx = dx * self.speed
        self.vy = dy * self.speed
        
        # Mettre à jour la direction
        if dx > 0:
            self.facing = 'right'
        elif dx < 0:
            self.facing = 'left'
            
        self.is_moving = (dx != 0 or dy != 0)
        
    def update(self, world_map, events=None):
        # Mettre à jour les animations
        self.animation_manager.update()
        
        # Animation de marche
        _, self.bob_offset = self.walk_animation.update(self.is_moving)
        
        # Son de pas
        if self.is_moving and time.time() - self.last_footstep > self.footstep_interval:
            play_sound('footstep', f'player{self.id}')
            self.last_footstep = time.time()
        
        # Mettre à jour l'animation d'attaque
        if self.attack_animation:
            result = self.attack_animation.update()
            if self.attack_animation.completed:
                self.attack_animation = None

        # Mettre à jour l'animation de service (aller cuisine -> retour client)
        if self.serve_animation:
            self.serve_animation.update()
            pos = self.serve_animation.current_pos
            self.rect.x = int(pos[0])
            self.rect.y = int(pos[1])
            # Orientation : regarder vers la cuisine ou le client selon la phase
            if not self.serve_animation.completed:
                progress = (time.time() - self.serve_animation.start_time) / self.serve_animation.duration
                if progress < 0.5:
                    self.facing = 'right' if self.serve_animation.kitchen_pos[0] >= self.rect.centerx else 'left'
                else:
                    self.facing = 'right' if self.serve_animation.client_pos[0] >= self.rect.centerx else 'left'
            return
                
        # Cooldown d'attaque
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1/60  # Approximation pour 60 FPS
            
        # Cooldown de balayage
        if self.sweep_cooldown > 0:
            self.sweep_cooldown -= 1/60
            
        # Animation de balayage
        if self.is_sweeping:
            self.sweep_animation_timer -= 1/60
            if self.sweep_animation_timer <= 0:
                self.is_sweeping = False
        
        if self.active_minigame:
            if events:
                self.active_minigame.update(events)
            if self.active_minigame.completed:
                pass
        else:
            new_x = self.rect.x + self.vx
            new_y = self.rect.y + self.vy
            
            zone = world_map.get_zone(self.current_zone)
            if not zone:
                return
            
            can_move_x = True
            can_move_y = True
            
            # Utiliser les collisions en pixels si disponibles
            if zone.use_pixel_collisions:
                # Collision hitbox plus petite que le sprite pour plus de fluidité
                collision_width = self.rect.width // 2
                collision_height = self.rect.height // 3
                collision_offset_x = (self.rect.width - collision_width) // 2
                collision_offset_y = self.rect.height - collision_height
                
                # Test mouvement X
                if self.vx != 0:
                    test_x = new_x + collision_offset_x
                    test_y = self.rect.y + collision_offset_y
                    if not zone.is_walkable_pixel(test_x, test_y, collision_width, collision_height):
                        can_move_x = False
                
                # Test mouvement Y
                if self.vy != 0:
                    test_x = self.rect.x + collision_offset_x
                    test_y = new_y + collision_offset_y
                    if not zone.is_walkable_pixel(test_x, test_y, collision_width, collision_height):
                        can_move_y = False
            else:
                # Fallback: collision par tiles
                center_x = new_x + self.rect.width // 2
                center_y = new_y + self.rect.height // 2
                
                tile_x = int(center_x // TILE_SIZE)
                tile_y = int(center_y // TILE_SIZE)
                
                if self.vx != 0:
                    check_x = int((new_x + self.rect.width // 2 + (self.rect.width // 3 if self.vx > 0 else -self.rect.width // 3)) // TILE_SIZE)
                    if not zone.is_walkable(check_x, int((self.rect.y + self.rect.height // 2) // TILE_SIZE)):
                        can_move_x = False
                        
                if self.vy != 0:
                    check_y = int((new_y + self.rect.height // 2 + (self.rect.height // 3 if self.vy > 0 else -self.rect.height // 3)) // TILE_SIZE)
                    if not zone.is_walkable(int((self.rect.x + self.rect.width // 2) // TILE_SIZE), check_y):
                        can_move_y = False
            
            if can_move_x:
                self.rect.x = new_x
            if can_move_y:
                self.rect.y = new_y
                
            # Door transitions - use center
            center_tile_x = int(self.rect.centerx // TILE_SIZE)
            center_tile_y = int(self.rect.centery // TILE_SIZE)
            door = zone.get_door_at(center_tile_x, center_tile_y)
            if door:
                _, _, target_zone, target_x, target_y = door
                old_zone = self.current_zone
                self.current_zone = target_zone
                self.rect.centerx = target_x * TILE_SIZE + TILE_SIZE // 2
                self.rect.centery = target_y * TILE_SIZE + TILE_SIZE // 2
                play_sound('door', f'player{self.id}')
        
    def draw(self, surface, camera, viewport_owner_id=None):
        """Dessine le joueur. viewport_owner_id: id du joueur dont c'est la vue (1 ou 2).
        La box de service (minigame) n'est affichée que sur la vue de ce joueur."""
        draw_x = self.rect.x - camera.x
        draw_y = self.rect.y - camera.y + self.bob_offset
        
        # Utiliser le bon sprite selon la direction
        if self.facing == 'left':
            surface.blit(self.image_left, (draw_x, draw_y))
        else:
            surface.blit(self.image_right, (draw_x, draw_y))
        
        # Dessiner l'animation d'attaque
        if self.attack_animation and not self.attack_animation.completed:
            self.attack_animation.draw_weapon(surface, camera)
        
        # Dessiner l'animation de balayage
        if self.is_sweeping:
            self._draw_sweep_animation(surface, draw_x, draw_y)
        
        # Indicateur d'arme équipée
        weapon_info = self.get_weapon_info()
        if weapon_info:
            # Petit icône au-dessus du joueur
            icon_x = draw_x + self.rect.width // 2 - 8
            icon_y = draw_y - 20
            pygame.draw.rect(surface, (50, 50, 50), (icon_x - 2, icon_y - 2, 20, 20), border_radius=3)
            if weapon_info['type'] == 'knife':
                pygame.draw.polygon(surface, (180, 180, 180), [
                    (icon_x + 2, icon_y + 8),
                    (icon_x + 14, icon_y + 4),
                    (icon_x + 14, icon_y + 12)
                ])
            else:  # fork
                for i in range(3):
                    pygame.draw.line(surface, (150, 150, 150), 
                                   (icon_x + 4 + i * 4, icon_y + 2),
                                   (icon_x + 4 + i * 4, icon_y + 12), 2)
        
        # N'afficher la box de service (minigame) que sur la vue du joueur qui sert.
        # En split screen (viewport_owner_id défini) elle est dessinée au-dessus du HUD par le renderer.
        if self.active_minigame and viewport_owner_id is None:
            self.active_minigame.draw(surface, draw_x - 50, draw_y - 140)
            
    def _draw_sweep_animation(self, surface, draw_x, draw_y):
        """Dessine l'animation de balayage"""
        import math
        
        # Calculer la progression de l'animation (0 à 1)
        progress = 1 - (self.sweep_animation_timer / self.sweep_animation_duration)
        
        # Position du balai
        center_x = draw_x + self.rect.width // 2
        center_y = draw_y + self.rect.height
        
        # Angle du balai qui oscille (gauche-droite-gauche)
        sweep_angle = math.sin(progress * math.pi * 3) * 45  # 3 oscillations
        
        # Longueur du balai
        broom_length = 40
        
        # Calculer les points du balai
        angle_rad = math.radians(-90 + sweep_angle)
        end_x = center_x + int(broom_length * math.cos(angle_rad))
        end_y = center_y + int(broom_length * math.sin(angle_rad))
        
        # Manche du balai
        pygame.draw.line(surface, (139, 90, 43), (center_x, center_y - 10), (end_x, end_y), 3)
        
        # Tête du balai (plus large à l'extrémité)
        broom_width = 20
        perp_angle = angle_rad + math.pi / 2
        broom_points = [
            (end_x - int(broom_width // 2 * math.cos(perp_angle)),
             end_y - int(broom_width // 2 * math.sin(perp_angle))),
            (end_x + int(broom_width // 2 * math.cos(perp_angle)),
             end_y + int(broom_width // 2 * math.sin(perp_angle))),
            (end_x + int((broom_width // 2 + 5) * math.cos(perp_angle)) + int(10 * math.cos(angle_rad)),
             end_y + int((broom_width // 2 + 5) * math.sin(perp_angle)) + int(10 * math.sin(angle_rad))),
            (end_x - int((broom_width // 2 + 5) * math.cos(perp_angle)) + int(10 * math.cos(angle_rad)),
             end_y - int((broom_width // 2 + 5) * math.sin(perp_angle)) + int(10 * math.sin(angle_rad))),
        ]
        pygame.draw.polygon(surface, (180, 140, 70), broom_points)
        
        # Effet de particules de poussière
        if progress > 0.2:
            for i in range(3):
                dust_x = end_x + int((progress * 30 + i * 10) * (1 if self.facing == 'right' else -1))
                dust_y = end_y + 5 - int(progress * 10)
                alpha = int(150 * (1 - progress))
                dust_size = int(3 + progress * 5)
                dust_surface = pygame.Surface((dust_size * 2, dust_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(dust_surface, (200, 180, 150, alpha), (dust_size, dust_size), dust_size)
                surface.blit(dust_surface, (dust_x - dust_size, dust_y - dust_size))
            
    def check_collision_with(self, other):
        """Pixel-perfect collision check"""
        if not self.mask or not other.mask:
            return self.rect.colliderect(other.rect)
            
        offset_x = other.rect.x - self.rect.x
        offset_y = other.rect.y - self.rect.y
        
        overlap = self.mask.overlap(other.mask, (offset_x, offset_y))
        return overlap is not None
        
    def get_distance_to(self, other):
        return ((self.rect.centerx - other.rect.centerx)**2 + 
                (self.rect.centery - other.rect.centery)**2)**0.5
        
    def add_money(self, amount):
        self.money += amount
        
    def modify_reputation(self, amount):
        self.reputation = max(0, min(100, self.reputation + amount))
        
    def get_tile_pos(self):
        return (int(self.rect.centerx // TILE_SIZE), int(self.rect.centery // TILE_SIZE))
        
    # === MÉTHODES D'ARMES ET D'ATTAQUE ===
    
    def pickup_weapon(self, weapon):
        """Ramasse une arme"""
        if self.inventory.pickup_weapon(weapon):
            play_sound('pickup', f'player{self.id}')
            self.animation_manager.add_floating_text(
                f"+{weapon.name}",
                (self.rect.centerx, self.rect.top - 20),
                GREEN
            )
            return True
        return False
        
    def attack(self, target_pos):
        """Lance une attaque avec l'arme équipée"""
        if not self.inventory.has_weapon():
            return None
            
        if self.attack_cooldown > 0:
            return None
            
        weapon = self.inventory.use_weapon()
        if weapon is None:
            return None
            
        # Créer l'animation d'attaque
        self.attack_animation = AttackAnimation(
            (self.rect.centerx, self.rect.centery),
            target_pos,
            weapon.weapon_type
        )
        
        self.attack_cooldown = self.attack_cooldown_duration
        play_sound('stab', 'combat')
        
        return weapon
        
    def can_attack_client(self, client):
        """Vérifie si le joueur peut attaquer un client"""
        if not self.inventory.has_weapon():
            return False
            
        if client.zone != self.current_zone:
            return False
            
        distance = self.get_distance_to(client)
        weapon_info = self.inventory.get_weapon_info()
        
        if weapon_info:
            weapon_range = TILE_SIZE * 2 if weapon_info['type'] == 'fork' else TILE_SIZE * 1.5
            return distance <= weapon_range
            
        return False
        
    def get_weapon_info(self):
        """Retourne les infos sur l'arme équipée"""
        return self.inventory.get_weapon_info()
        
    # === MÉTHODES DE STOCK ===
    
    def can_serve_dish(self, dish_name):
        """Vérifie si le joueur peut servir un plat (stock suffisant)"""
        from game.inventory import RECIPES
        
        if dish_name not in RECIPES:
            return True, None  # Pas de recette = pas de vérification
            
        recipe = RECIPES[dish_name]
        # Recette en dict { ingrédient: quantité } ou liste (1 par élément)
        if isinstance(recipe, dict):
            for ingredient, amount in recipe.items():
                if ingredient in self.food_stock.ingredients:
                    if self.food_stock.ingredients[ingredient]['quantity'] < amount:
                        return False, ingredient
        else:
            for ingredient in recipe:
                if ingredient in self.food_stock.ingredients:
                    if self.food_stock.ingredients[ingredient]['quantity'] < 1:
                        return False, ingredient
        return True, None
        
    def use_ingredients_for_dish(self, dish_name):
        """Utilise les ingrédients pour un plat"""
        from game.inventory import RECIPES
        
        if dish_name not in RECIPES:
            return True
            
        recipe = RECIPES[dish_name]
        success, missing = self.food_stock.use_recipe(recipe)
        
        if not success:
            play_sound('stock_empty', f'player{self.id}')
            self.animation_manager.add_floating_text(
                f"Plus de {missing}!",
                (self.rect.centerx, self.rect.top - 20),
                RED
            )
            
        return success
        
    def restock(self, ingredient_name=None):
        """Réapprovisionne le stock (déduit l'argent seulement si le joueur peut payer)"""
        if ingredient_name:
            amount, cost = self.food_stock.restock(ingredient_name, dry_run=True)
            if cost > 0 and self.money >= cost:
                self.money -= cost
                self.food_stock.restock(ingredient_name, amount=amount)
                play_sound('restock', f'player{self.id}')
                return amount, cost
        else:
            cost = self.food_stock.restock_all(dry_run=True)
            if cost > 0 and self.money >= cost:
                self.money -= cost
                self.food_stock.restock_all()
                play_sound('restock', f'player{self.id}')
                return True, cost
        return 0, 0
        
    def get_low_stock_warning(self):
        """Retourne les avertissements de stock bas"""
        return self.food_stock.get_low_stock(threshold=5)
        
    # === MÉTHODES DE SABOTAGE ===
    
    def is_in_enemy_zone(self):
        """Vérifie si le joueur est dans la zone ennemie"""
        if self.id == 1:
            return self.current_zone == 'kebab'
        else:
            return self.current_zone == 'tacos'
            
    # === MÉTHODES DE NETTOYAGE ===
    
    def can_sweep(self):
        """Vérifie si le joueur peut balayer"""
        return self.sweep_cooldown <= 0 and not self.is_sweeping
        
    def start_sweep(self):
        """Commence l'animation de balayage"""
        if not self.can_sweep():
            return False
            
        self.is_sweeping = True
        self.sweep_animation_timer = self.sweep_animation_duration
        self.sweep_cooldown = self.sweep_cooldown_duration
        play_sound('sweep', f'player{self.id}')
        return True
        
    def get_sweep_cooldown(self):
        """Retourne le temps restant avant de pouvoir balayer"""
        return max(0, self.sweep_cooldown)
            
    def can_steal_spit(self, other_player):
        """Vérifie si le joueur peut voler la broche de l'autre"""
        if not self.is_in_enemy_zone():
            return False
        if self.current_zone != other_player.home_zone:
            return False
        # Vérifier si la broche est disponible
        return other_player.food_stock.is_spit_available()