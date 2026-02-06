import pygame
import random
import time
import math
from config import *
from game.dishes import create_dish_for_restaurant
from game.assets_loader import Assets
from game.animation import DeathAnimation, FleeAnimation
from game.audio import play_sound

class Client(pygame.sprite.Sprite):
    # Types de clients disponibles
    CLIENT_TYPES = ['client', 'client1', 'client2']
    
    def __init__(self, x, y, zone="street", client_type=None, target_zone=None):
        super().__init__()
        
        assets = Assets.get()
        
        # Choisir un type de client aléatoire si non spécifié
        if client_type is None:
            client_type = random.choice(self.CLIENT_TYPES)
        self.client_type = client_type
        
        # Charger le sprite correspondant
        self.image = assets.get_image(client_type)
        self.base_image = self.image  # Pour les animations
        self.mask = assets.get_mask(client_type)
        
        # Fallback si l'image n'existe pas
        if not self.image:
            # Essayer le sprite client par défaut
            self.image = assets.get_image("client")
            self.mask = assets.get_mask("client")
            
        if not self.image:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            self.color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            pygame.draw.circle(self.image, self.color, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//2)
            self.mask = pygame.mask.from_surface(self.image)
            
        self.base_image = self.image
            
        # Use actual image size for rect
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        
        # Zone actuelle (où se trouve le sprite) et zone cible (restaurant)
        self.zone = zone  # zone actuelle pour le rendu / collisions
        self.target_zone = target_zone or zone  # zone où il ira commander
        self.is_wanderer = (zone == "street" and target_zone is None)
        
        # Vitesse de déplacement (plus lent qu'un joueur)
        self.speed = 2
        
        # Plat demandé : une instance fraîche par client, variée selon le restaurant
        self.dish = create_dish_for_restaurant(self.target_zone or "street")
            
        self.absurd_request = self._generate_absurd_request()
        
        # États possibles :
        # - "wandering"             : se balade dans la rue
        # - "walking_to_restaurant" : dans la rue, se dirige vers la porte
        # - "waiting_outside"       : fait la queue dehors
        # - "walking_to_queue"      : à l'intérieur, se place dans la file
        # - "waiting"               : en file derrière le comptoir
        # - "angry"                 : a trop attendu
        # - "fleeing"               : s'enfuit
        # - "dying"                 : en train de mourir
        # - "dead"                  : mort
        # - "gone"                  : parti
        if self.is_wanderer:
            self.state = "wandering"
        elif zone == "street" and self.target_zone in ("tacos", "kebab"):
            self.state = "walking_to_restaurant"
        else:
            self.state = "waiting"
        
        # Position de file cible dans le restaurant (en tuiles)
        self.queue_tile_x = None
        self.queue_tile_y = None
        
        # Position de file à l'extérieur (en tuiles)
        self.outside_tile_x = None
        self.outside_tile_y = None
        self.is_first_in_queue = False  # True uniquement pour le premier de la file (bulle plat)
        
        # On commence à mesurer la patience uniquement une fois en file intérieure
        self.spawn_time = None if self.state != "waiting" else time.time()
        self.patience = 45
        
        # Pour le wandering
        self.wander_dir_x = 0
        self.wander_dir_y = 0
        self.wander_change_time = time.time()
        
        # Animations
        self.death_animation = None
        self.flee_animation = None
        self.wobble = 0
        
        # Pour l'animation de peur
        self.fear_level = 0
        self.shake_offset = (0, 0)
        
    def _generate_absurd_request(self):
        requests = [
            "Sans gluten mais avec double pain",
            "Cuit à la vapeur de chicha",
            "Avec supplément gras",
            "Pas trop chaud, je suis sensible",
            "Coupez le en 12 svp",
            "Avec de la mayo halal",
            "Sans oignons mais avec oignons frits",
            "Sauce algérienne-samuraï mix",
            "Réchauffé au micro-ondes 3 fois",
            "Avec de la sauce piquante mais pas trop",
            "Emballé dans du papier biodégradable"
        ]
        return random.choice(requests)
        
    def _move_towards(self, target_x, target_y):
        """Déplacement simple en ligne droite vers une position en pixels."""
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 1:
            return
        step = min(self.speed, dist)
        self.rect.centerx += int(dx / dist * step)
        self.rect.centery += int(dy / dist * step)

    def _clamp_to_street_zone(self, zone):
        """Maintient le client dans les limites walkables de la rue (évite de sortir en bas)."""
        # Rue : trottoir/route = lignes 3 à 7 (pixels 3*TILE_SIZE à 8*TILE_SIZE)
        min_x = 0
        max_x = zone.width * TILE_SIZE
        min_y = 3 * TILE_SIZE  # première ligne walkable (trottoir)
        max_y = zone.height * TILE_SIZE  # bas de la map
        self.rect.left = max(min_x, self.rect.left)
        self.rect.right = min(max_x, self.rect.right)
        self.rect.top = max(min_y, self.rect.top)
        self.rect.bottom = min(max_y, self.rect.bottom)

    def update(self, world_map=None, game_state=None):
        """Mise à jour du client avec logique de déplacement"""
        
        # États terminaux - animations de mort/fuite
        if self.state == "dying":
            if self.death_animation:
                result = self.death_animation.update()
                if self.death_animation.completed:
                    self.state = "dead"
            return
                    
        if self.state == "fleeing":
            if self.flee_animation:
                result = self.flee_animation.update()
                if result:
                    self.rect.x = result['position'][0]
                    self.rect.y = result['position'][1]
                if self.flee_animation.completed:
                    self.state = "gone"
            return
        
        if self.state in ['dead', 'gone']:
            return
                    
        # Animation de tremblement si peur
        if self.fear_level > 0:
            self.shake_offset = (
                random.randint(-2, 2) * int(self.fear_level),
                random.randint(-2, 2) * int(self.fear_level)
            )
            self.fear_level = max(0, self.fear_level - 0.02)
        else:
            self.shake_offset = (0, 0)
            
        # Si pas de world_map, juste vérifier la patience
        if world_map is None:
            if self.state == "waiting" and self.spawn_time is not None:
                if time.time() - self.spawn_time > self.patience:
                    self.state = "angry"
                    play_sound('client_angry', 'client')
            return
        
        # === Logique de déplacement ===
        
        # 1) Clients qui se baladent dans la rue
        if self.state == "wandering":
            zone = world_map.get_zone(self.zone)
            if not zone:
                return

            # Change de direction de temps en temps
            if time.time() - self.wander_change_time > 1.0:
                self.wander_change_time = time.time()
                self.wander_dir_x, self.wander_dir_y = random.choice(
                    [(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)]
                )

            if self.wander_dir_x != 0 or self.wander_dir_y != 0:
                new_cx = self.rect.centerx + self.wander_dir_x * self.speed
                new_cy = self.rect.centery + self.wander_dir_y * self.speed
                tile_x = int(new_cx // TILE_SIZE)
                tile_y = int(new_cy // TILE_SIZE)
                if zone.is_walkable(tile_x, tile_y):
                    self.rect.centerx = new_cx
                    self.rect.centery = new_cy

            # Vérifie si une place est dispo dans une file extérieure de resto
            if game_state:
                # Déterminer les restaurants avec de la place
                available_restaurants = []
                for restaurant in ["tacos", "kebab"]:
                    outside_clients = [
                        c for c in game_state.clients
                        if c.zone == "street" and getattr(c, "target_zone", None) == restaurant
                    ]
                    if len(outside_clients) < 3:
                        available_restaurants.append(restaurant)
                
                if available_restaurants:
                    # Choisir le restaurant en fonction de la réputation du propriétaire
                    tacos_owner = game_state._get_restaurant_owner("tacos")
                    kebab_owner = game_state._get_restaurant_owner("kebab")
                    tacos_rep = tacos_owner.reputation if tacos_owner else 50
                    kebab_rep = kebab_owner.reputation if kebab_owner else 50
                    
                    if len(available_restaurants) == 1:
                        chosen_restaurant = available_restaurants[0]
                    else:
                        # Les deux sont disponibles, choisir selon la réputation
                        total_rep = tacos_rep + kebab_rep
                        if total_rep <= 0:
                            chosen_restaurant = random.choice(available_restaurants)
                        else:
                            tacos_probability = tacos_rep / total_rep
                            chosen_restaurant = "tacos" if random.random() < tacos_probability else "kebab"
                    
                    # Ce client rejoint la file de ce restaurant
                    self.target_zone = chosen_restaurant
                    self.is_wanderer = False
                    self.state = "walking_to_restaurant"
                    # Nouveau plat dédié à ce client (toujours une instance fraîche)
                    self.dish = create_dish_for_restaurant(chosen_restaurant)
                    if hasattr(game_state, '_recompute_queues'):
                        game_state._recompute_queues()
                    return

        # 2) Clients qui se dirigent vers un restaurant
        if self.state == "walking_to_restaurant":
            zone = world_map.get_zone(self.zone)
            if not zone:
                return

            # Cherche la porte de rue qui mène à notre restaurant cible
            door_to_restaurant = None
            for door in zone.doors:
                dx, dy, target_zone, _, _ = door
                if target_zone == self.target_zone:
                    door_to_restaurant = door
                    break

            if door_to_restaurant:
                dx, dy, target_zone, target_x, target_y = door_to_restaurant
                target_px = dx * TILE_SIZE + TILE_SIZE // 2
                target_py = dy * TILE_SIZE + TILE_SIZE // 2
                self._move_towards(target_px, target_py)

                # Vérifie si on est sur la tuile de la porte
                tile_x = int(self.rect.centerx // TILE_SIZE)
                tile_y = int(self.rect.centery // TILE_SIZE)
                if tile_x == dx and tile_y == dy and game_state:
                    # Vérifie la capacité à l'intérieur (max 3 clients par resto)
                    inside_clients = [
                        c for c in game_state.clients
                        if c.target_zone == self.target_zone
                        and c.zone == self.target_zone
                    ]
                    if len(inside_clients) < 3:
                        # Il peut rentrer
                        self.zone = target_zone
                        self.rect.centerx = target_x * TILE_SIZE + TILE_SIZE // 2
                        self.rect.centery = target_y * TILE_SIZE + TILE_SIZE // 2
                        self.state = "walking_to_queue"
                    else:
                        # Il attend devant la porte
                        self.state = "waiting_outside"

        # 3) Client qui attend dehors
        if self.state == "waiting_outside":
            zone = world_map.get_zone(self.zone)
            if not zone:
                return

            # Retrouve la porte vers son restaurant cible
            door_to_restaurant = None
            for door in zone.doors:
                dx, dy, target_zone, target_x, target_y = door
                if target_zone == self.target_zone:
                    door_to_restaurant = door
                    break

            if not door_to_restaurant:
                return

            dx, dy, target_zone, target_x, target_y = door_to_restaurant
            door_cx = dx * TILE_SIZE + TILE_SIZE // 2
            door_cy = dy * TILE_SIZE + TILE_SIZE // 2

            # Position cible dans la file extérieure (si définie)
            if self.outside_tile_x is not None and self.outside_tile_y is not None:
                target_px = self.outside_tile_x * TILE_SIZE + TILE_SIZE // 2
                target_py = self.outside_tile_y * TILE_SIZE + TILE_SIZE // 2
            else:
                target_px = door_cx
                target_py = door_cy + TILE_SIZE // 2

            self._move_towards(target_px, target_py)

            # Vérifie si de la place s'est libérée
            if game_state:
                inside_clients = [
                    c for c in game_state.clients
                    if c.target_zone == self.target_zone
                    and c.zone == self.target_zone
                ]
                if len(inside_clients) >= 3:
                    return

                outside_queue = [
                    c for c in game_state.clients
                    if c is not self
                    and c.target_zone == self.target_zone
                    and c.zone == "street"
                    and c.state in ("walking_to_restaurant", "waiting_outside")
                ]

                def dist_to_door(client):
                    cx = client.rect.centerx
                    cy = client.rect.centery
                    return ((cx - door_cx) ** 2 + (cy - door_cy) ** 2) ** 0.5

                if outside_queue:
                    closest = min(outside_queue, key=dist_to_door)
                    # Si quelqu'un est plus proche de la porte, on attend
                    if dist_to_door(closest) < dist_to_door(self):
                        return

                # C'est à lui de rentrer
                self.zone = target_zone
                self.rect.centerx = target_x * TILE_SIZE + TILE_SIZE // 2
                self.rect.centery = target_y * TILE_SIZE + TILE_SIZE // 2
                self.state = "walking_to_queue"

        # 4) Client qui marche vers sa position dans la file
        if self.state == "walking_to_queue":
            if self.queue_tile_x is None or self.queue_tile_y is None:
                return

            target_px = self.queue_tile_x * TILE_SIZE + TILE_SIZE // 2
            target_py = self.queue_tile_y * TILE_SIZE + TILE_SIZE // 2
            self._move_towards(target_px, target_py)

            dist = ((self.rect.centerx - target_px) ** 2 + (self.rect.centery - target_py) ** 2) ** 0.5
            if dist < 4:
                self.rect.centerx = target_px
                self.rect.centery = target_py
                self.state = "waiting"
                if self.spawn_time is None:
                    self.spawn_time = time.time()

        # Clamp en rue pour ne jamais sortir de la map (surtout en bas)
        if self.zone == "street" and world_map:
            zone = world_map.get_zone("street")
            if zone:
                self._clamp_to_street_zone(zone)

        # 5) Gestion de la patience uniquement lorsqu'il est en file
        if self.state == "waiting" and self.spawn_time is not None:
            if time.time() - self.spawn_time > self.patience:
                self.state = "angry"
                play_sound('client_angry', 'client')
            
    def take_damage(self, damage, weapon_type='knife'):
        """Le client reçoit des dégâts (attaque avec arme)"""
        if self.state in ['dying', 'dead', 'gone']:
            return False
            
        # Les clients meurent en un coup
        self.state = "dying"
        self.death_animation = DeathAnimation(
            (self.rect.x, self.rect.y),
            death_type='stab'
        )
        play_sound('client_death', 'client')
        return True
        
    def scare(self, intensity=1.0):
        """Effraye le client (peut le faire fuir)"""
        if self.state in ['dying', 'dead', 'gone', 'fleeing']:
            return False
            
        self.fear_level = min(3, self.fear_level + intensity)
        
        # Si trop effrayé, fuit
        if self.fear_level >= 2.5:
            self.flee()
            return True
            
        return False
        
    def flee(self, direction=None):
        """Le client fuit"""
        if self.state in ['dying', 'dead', 'gone', 'fleeing']:
            return
            
        if direction is None:
            direction = 'right' if random.random() > 0.5 else 'left'
            
        self.state = "fleeing"
        self.flee_animation = FleeAnimation(
            (self.rect.x, self.rect.y),
            direction
        )
        play_sound('client_flee', 'client')
        
    def is_alive(self):
        """Vérifie si le client est encore en vie et présent"""
        return self.state not in ['dead', 'gone']
        
    def is_targetable(self):
        """Vérifie si le client peut être ciblé (pour servir ou attaquer)"""
        return self.state in ['waiting', 'angry', 'walking_to_queue']
                
    def draw(self, surface, camera):
        draw_x = self.rect.x - camera.x + self.shake_offset[0]
        draw_y = self.rect.y - camera.y + self.shake_offset[1]
        
        # Animation de mort
        if self.state == "dying" and self.death_animation:
            self.death_animation.draw(surface, camera, self.base_image)
            return
            
        # Ne pas dessiner si mort ou parti
        if self.state in ['dead', 'gone']:
            return
            
        # Animation de fuite
        if self.state == "fleeing":
            # Sprite qui court avec effet de mouvement
            if self.flee_animation:
                wobble = math.sin(time.time() * 20) * 3
                draw_y += wobble
        
        surface.blit(self.image, (draw_x, draw_y))
        
        # Order bubble - uniquement pour le premier client de la file
        if self.state in ['waiting', 'walking_to_queue', 'angry'] and self.is_first_in_queue:
            font = pygame.font.SysFont(None, 24)
            order_text = font.render(self.dish.name, True, BLACK)
            bubble_rect = pygame.Rect(draw_x - 10, draw_y - 35, order_text.get_width() + 16, 28)
            pygame.draw.rect(surface, WHITE, bubble_rect, border_radius=8)
            pygame.draw.rect(surface, BLACK, bubble_rect, 2, border_radius=8)
            surface.blit(order_text, (draw_x - 2, draw_y - 32))
        
        # Angry indicator
        if self.state == "angry":
            pygame.draw.circle(surface, (255, 0, 0), (draw_x + self.rect.width + 5, draw_y), 12)
            angry_font = pygame.font.SysFont(None, 20)
            angry_text = angry_font.render("!", True, WHITE)
            surface.blit(angry_text, (draw_x + self.rect.width + 1, draw_y - 8))
            
        # Indicateur de peur
        if self.fear_level > 1:
            fear_font = pygame.font.SysFont(None, 18)
            fear_text = fear_font.render("😰", True, WHITE)
            surface.blit(fear_text, (draw_x + self.rect.width - 5, draw_y - 15))