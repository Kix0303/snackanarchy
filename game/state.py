import pygame
import random
import time
from game.map import WorldMap
from game.player import Player
from game.client import Client
from game.minigames import MiniGame
from game.events import EventManager
from game.inventory import WeaponSpawner
from game.sabotage import SabotageManager, SABOTAGES
from game.animation import AnimationManager
from game.audio import AudioManager, play_sound
from game.history import GameHistory
from config import *

class GameState:
    def __init__(self, player_configs=None):
        self.world_map = WorldMap()
        
        # Default configs if not provided
        if player_configs is None:
            player_configs = [
                {"name": "Joueur 1", "side": "left", "restaurant": "tacos"},
                {"name": "Joueur 2", "side": "right", "restaurant": "kebab"}
            ]
        
        # Trouver quel joueur est à gauche et lequel est à droite
        left_config = next((c for c in player_configs if c["side"] == "left"), player_configs[0])
        right_config = next((c for c in player_configs if c["side"] == "right"), player_configs[1])
        
        # Joueur 1 (index 0) = écran gauche = restaurant tacos
        # Joueur 2 (index 1) = écran droit = restaurant kebab
        # Les joueurs sont toujours assignés à leur restaurant respectif
        self.players = [
            Player(1, 5, 5, PLAYER_1_COLOR, "tacos", username=left_config["name"]),
            Player(2, 5, 5, PLAYER_2_COLOR, "kebab", username=right_config["name"])
        ]
        
        # Assigner les restaurants aux joueurs
        self.players[0].owns_restaurant = "tacos"
        self.players[1].owns_restaurant = "kebab"
        
        # Store configs for reference
        self.player_configs = player_configs
        
        self.clients = []
        self.last_spawn_time = time.time()
        self.spawn_interval = 8.0
        
        # Clients qui se baladent dans la rue
        self.last_wander_spawn_time = time.time()
        self.wander_spawn_interval = 1.0
        self.wandering_clients_limit = 20
        
        self.event_manager = EventManager(self)
        
        # Nouveau: Gestionnaire d'armes
        self.weapon_spawner = WeaponSpawner()
        
        # Nouveau: Gestionnaire de sabotages
        self.sabotage_manager = SabotageManager()
        
        # Nouveau: Gestionnaire d'animations global
        self.animation_manager = AnimationManager()
        
        # Nouveau: Audio
        self.audio = AudioManager.get()
        
        self.start_time = time.time()
        self.game_duration = DEFAULT_DURATION
        self.game_over = False
        
        # Timer warning
        self.timer_warning_played = False
        
    def update(self, events, input_action):
        if self.game_over:
            return
            
        elapsed = time.time() - self.start_time
        remaining = self.game_duration - elapsed
        
        # Warning sonore à 30 secondes
        if remaining <= 30 and not self.timer_warning_played:
            play_sound('timer_warning', 'ui')
            self.timer_warning_played = True
            
        if elapsed >= self.game_duration:
            self.game_over = True
            # Son de fin de partie
            winner = self.get_winner()
            if winner > 0:
                play_sound('victory', 'ui')
            else:
                play_sound('game_over', 'ui')
            # Enregistrer la partie dans l'historique
            GameHistory.get().record_game(self)
            return
        
        # Mise à jour des armes
        self.weapon_spawner.update()
        
        # Mise à jour des animations globales
        self.animation_manager.update()
        
        for player in self.players:
            player.update(self.world_map, events)
            
            # Vérifier le ramassage d'armes
            weapon = self.weapon_spawner.check_pickup(player.rect, player.current_zone)
            if weapon and not player.inventory.has_weapon():
                player.pickup_weapon(weapon)
            
            if player.active_minigame and player.active_minigame.completed:
                if player.active_minigame.success:
                    # Vérifier le stock avant de servir
                    dish_name = player.current_client.dish.name if player.current_client else "Tacos XXL"
                    can_serve, missing = player.can_serve_dish(dish_name)
                    
                    if can_serve:
                        player.use_ingredients_for_dish(dish_name)
                        player.add_money(20)
                        player.modify_reputation(2)  # +2% réputation
                        play_sound('money', f'player{player.id}')
                        play_sound('client_happy', 'client')
                        
                        # Animation de texte flottant
                        player.animation_manager.add_floating_text(
                            "+20€ +2%",
                            (player.rect.centerx, player.rect.top - 30),
                            GREEN
                        )
                        
                        # Mise à jour des statistiques
                        player.clients_served += 1
                        if "Tacos" in dish_name:
                            player.tacos_served += 1
                            player.mission_manager.update('serve_tacos')
                        elif "Kebab" in dish_name:
                            player.kebabs_served += 1
                            player.mission_manager.update('serve_kebabs')
                        
                        # Mise à jour des missions
                        player.mission_manager.update('serve_clients')
                        player.mission_manager.update('serve_success')
                        player.mission_manager.update('earn_money', player.money)
                        player.mission_manager.update('reach_reputation', player.reputation)
                        
                        # Réclamer automatiquement les récompenses des missions
                        claimed, money, rep = player.mission_manager.claim_completed_missions()
                        if claimed > 0:
                            play_sound('mission_complete', 'ui')
                            player.animation_manager.add_floating_text(
                                f"Mission! +{money}€",
                                (player.rect.centerx, player.rect.top - 50),
                                YELLOW
                            )
                    else:
                        # Pas de stock = échec mais pas de pénalité de rep
                        play_sound('stock_empty', f'player{player.id}')
                        player.animation_manager.add_floating_text(
                            f"Rupture: {missing}!",
                            (player.rect.centerx, player.rect.top - 30),
                            RED
                        )
                else:
                    # Minigame raté - pas de pénalité, le client reste
                    play_sound('minigame_fail', f'player{player.id}')
                    player.animation_manager.add_floating_text(
                        "Raté!",
                        (player.rect.centerx, player.rect.top - 30),
                        RED
                    )
                    # Réinitialiser le streak pour les missions
                    player.mission_manager.update('serve_fail')
                    # Ne pas supprimer le client, il reste en attente
                    player.active_minigame = None
                    player.current_client = None
                    continue
                
                player.active_minigame = None
                if player.current_client in self.clients:
                    self.clients.remove(player.current_client)
                    self._recompute_queues()  # Réorganiser les files après avoir servi
                player.current_client = None

        if input_action:
            player_idx, action_type = input_action
            if action_type == "interact":
                self.handle_interaction(player_idx)
            elif action_type == "attack":
                self.handle_attack(player_idx)
            elif action_type == "sabotage":
                self.handle_sabotage_menu(player_idx)
            elif action_type == "sweep":
                self.handle_sweep(player_idx)

        if time.time() - self.last_spawn_time > self.spawn_interval:
            self.spawn_client()
            self.last_spawn_time = time.time()
            
        # Spawn de clients qui se baladent dans la rue
        if time.time() - self.last_wander_spawn_time > self.wander_spawn_interval:
            street_total = len([c for c in self.clients if c.zone == "street"])
            if street_total < self.wandering_clients_limit:
                self._spawn_wandering_client()
            self.last_wander_spawn_time = time.time()
            
        # Vérifier les clients qui ont perdu patience et partent
        for client in self.clients:
            if client.state == "angry" and not hasattr(client, '_left_penalty_applied'):
                # Client impatient qui s'en va
                client._left_penalty_applied = True
                client.flee()
                
                # Pénalité de réputation pour le propriétaire du restaurant
                restaurant_owner = self._get_restaurant_owner(client.zone)
                if restaurant_owner:
                    restaurant_owner.modify_reputation(-1)  # -1% réputation
                    restaurant_owner.animation_manager.add_floating_text(
                        "Client parti! -1%",
                        (restaurant_owner.rect.centerx, restaurant_owner.rect.top - 30),
                        RED
                    )
            
        # Nettoyer les clients morts ou partis
        self.clients = [c for c in self.clients if c.is_alive()]
            
        # Mettre à jour les clients avec la logique de déplacement
        for client in self.clients:
            client.update(self.world_map, self)
            
        self.event_manager.update()
        
    def _get_restaurant_owner(self, zone_name):
        """Retourne le joueur propriétaire d'un restaurant"""
        for player in self.players:
            if hasattr(player, 'owns_restaurant') and player.owns_restaurant == zone_name:
                return player
        # Fallback: player 1 = tacos, player 2 = kebab
        if zone_name == "tacos":
            return self.players[0]
        elif zone_name == "kebab":
            return self.players[1]
        return None
            
    def handle_interaction(self, player_idx):
        player = self.players[player_idx]
        if player.active_minigame: return
        
        # Vérifier que le joueur est dans SON propre restaurant
        player_restaurant = getattr(player, 'owns_restaurant', 'tacos' if player_idx == 0 else 'kebab')
        if player.current_zone != player_restaurant:
            # On ne peut pas servir dans le restaurant de l'autre
            play_sound('stock_empty', f'player{player.id}')
            player.animation_manager.add_floating_text(
                "Pas ton resto!",
                (player.rect.centerx, player.rect.top - 30),
                RED
            )
            return
        
        for client in self.clients:
            if client.zone != player.current_zone:
                continue
                
            if not client.is_targetable():
                continue
                
            # Use pixel-perfect collision OR distance check
            collision = False
            
            # First check if close enough for interaction range
            distance = player.get_distance_to(client)
            if distance < TILE_SIZE * 2:
                # Then check pixel-perfect collision for precise interaction
                if player.check_collision_with(client):
                    collision = True
                elif distance < TILE_SIZE * 1.5:
                    # Allow interaction if very close even without pixel overlap
                    collision = True
                    
            if collision:
                player.current_client = client
                player.active_minigame = MiniGame(client.dish.name)
                play_sound('serve', f'player{player.id}')
                return
                
    def handle_attack(self, player_idx):
        """Gère l'attaque d'un joueur avec son arme"""
        player = self.players[player_idx]
        
        if not player.inventory.has_weapon():
            return
            
        # Trouver le client le plus proche à portée
        closest_client = None
        closest_distance = float('inf')
        
        for client in self.clients:
            if client.zone != player.current_zone:
                continue
            if not client.is_targetable():
                continue
                
            distance = player.get_distance_to(client)
            if distance < closest_distance and player.can_attack_client(client):
                closest_client = client
                closest_distance = distance
                
        if closest_client:
            # Lancer l'attaque
            weapon = player.attack((closest_client.rect.centerx, closest_client.rect.centery))
            
            if weapon:
                # Statistiques
                player.attacks_made += 1
                player.mission_manager.update('attack')
                # Infliger les dégâts
                closest_client.take_damage(weapon.damage, weapon.weapon_type)
                
                # Déterminer qui subit la pénalité de réputation
                # Si on tue dans le restaurant de l'autre, c'est le propriétaire qui perd de la rep
                client_zone = closest_client.zone
                restaurant_owner = self._get_restaurant_owner(client_zone)
                player_restaurant = getattr(player, 'owns_restaurant', 'tacos' if player_idx == 0 else 'kebab')
                
                if client_zone != player_restaurant:
                    # On tue dans le restaurant de l'AUTRE = l'autre perd de la réputation
                    if restaurant_owner and restaurant_owner != player:
                        restaurant_owner.modify_reputation(-1)  # -1% pour le propriétaire
                        restaurant_owner.animation_manager.add_floating_text(
                            "Meurtre! -1%",
                            (restaurant_owner.rect.centerx, restaurant_owner.rect.top - 30),
                            RED
                        )
                        # Bonus de sabotage pour l'attaquant
                        player.animation_manager.add_floating_text(
                            "Sabotage!",
                            (player.rect.centerx, player.rect.top - 30),
                            ORANGE
                        )
                else:
                    # On tue dans son propre restaurant = on perd beaucoup de réputation
                    player.modify_reputation(-5)  # -5% pour avoir tué dans son propre resto
                    player.animation_manager.add_floating_text(
                        "Client tué! -5%",
                        (player.rect.centerx, player.rect.top - 30),
                        RED
                    )
                
                # Les autres clients à proximité ont peur
                for other_client in self.clients:
                    if other_client == closest_client:
                        continue
                    if other_client.zone != player.current_zone:
                        continue
                        
                    dist = ((other_client.rect.centerx - closest_client.rect.centerx)**2 + 
                           (other_client.rect.centery - closest_client.rect.centery)**2)**0.5
                    
                    if dist < TILE_SIZE * 4:
                        other_client.scare(intensity=1.5)
                
    def handle_sabotage(self, player_idx, sabotage_name):
        """Exécute un sabotage"""
        player = self.players[player_idx]
        target = self.players[1 - player_idx]  # L'autre joueur
        
        success, message = self.sabotage_manager.execute_sabotage(sabotage_name, player, target)
        
        if success:
            player.animation_manager.add_floating_text(
                message,
                (player.rect.centerx, player.rect.top - 30),
                ORANGE
            )
            # Statistiques et missions
            player.sabotages_done += 1
            player.mission_manager.update('sabotage')
        else:
            player.animation_manager.add_floating_text(
                message,
                (player.rect.centerx, player.rect.top - 30),
                RED
            )
            
        return success, message
        
    def handle_sabotage_menu(self, player_idx):
        """Affiche le menu de sabotage (appelé par input)"""
        # Cette méthode est appelée quand le joueur veut voir les sabotages disponibles
        # L'affichage réel se fait dans le renderer
        pass
        
    def handle_sweep(self, player_idx):
        """Gère l'action de balayage pour gagner de la réputation"""
        player = self.players[player_idx]
        
        # Vérifier que le joueur est dans SON propre restaurant
        player_restaurant = getattr(player, 'owns_restaurant', 'tacos' if player_idx == 0 else 'kebab')
        if player.current_zone != player_restaurant:
            play_sound('stock_empty', f'player{player.id}')
            player.animation_manager.add_floating_text(
                "Pas ton resto!",
                (player.rect.centerx, player.rect.top - 30),
                RED
            )
            return False
            
        if not player.can_sweep():
            cooldown = player.get_sweep_cooldown()
            if cooldown > 0:
                play_sound('stock_empty', f'player{player.id}')
                player.animation_manager.add_floating_text(
                    f"Cooldown: {int(cooldown)}s",
                    (player.rect.centerx, player.rect.top - 30),
                    ORANGE
                )
            return False
            
        # Démarrer le balayage
        if player.start_sweep():
            # Gain de réputation
            rep_gain = 3
            player.modify_reputation(rep_gain)
            player.cleaning_done += 1
            
            # Mise à jour des missions
            player.mission_manager.update('clean')
            player.mission_manager.update('reach_reputation', player.reputation)
            
            # Animation
            player.animation_manager.add_floating_text(
                f"Nettoyage! +{rep_gain}%",
                (player.rect.centerx, player.rect.top - 30),
                GREEN
            )
            
            # Réclamer automatiquement les récompenses des missions
            claimed, money, rep = player.mission_manager.claim_completed_missions()
            if claimed > 0:
                play_sound('mission_complete', 'ui')
                player.add_money(money)
                player.modify_reputation(rep)
                
            return True
            
        return False
        
    def try_steal_spit(self, player_idx):
        """Tente de voler la broche de l'adversaire"""
        player = self.players[player_idx]
        target = self.players[1 - player_idx]
        
        if player.can_steal_spit(target):
            success, message = self.sabotage_manager.execute_sabotage('steal_spit', player, target)
            return success, message
        return False, "Impossible de voler la broche ici"

    def _get_queue_config(self, target_restaurant):
        """Renvoie (queue_x, queue_start_y, max_length) pour un resto donné."""
        restaurant_zone = self.world_map.get_zone(target_restaurant)
        if not restaurant_zone:
            return None, None, 0

        # Porte intérieure du resto (en bas de la salle)
        door_inside_x = restaurant_zone.width // 2
        for door in restaurant_zone.doors:
            dx, dy, *_ = door
            if dy == restaurant_zone.height - 1:
                door_inside_x = dx
                break

        # File légèrement différente selon le resto
        if target_restaurant == "tacos":
            queue_x = max(1, door_inside_x - 1)
        else:
            queue_x = door_inside_x

        # Premier client de la file : juste devant le comptoir
        queue_start_y = 3
        max_queue_length = max(0, (restaurant_zone.height - 1) - queue_start_y)

        return queue_x, queue_start_y, max_queue_length

    def _recompute_queues(self):
        """Réorganise les files de chaque restaurant (dedans et dehors)."""
        street_zone = self.world_map.get_zone("street")

        for restaurant in ["tacos", "kebab"]:
            queue_x, queue_start_y, max_len = self._get_queue_config(restaurant)
            if queue_x is None:
                continue

            # --- File intérieure ---
            inside_clients = [
                c for c in self.clients
                if c.target_zone == restaurant
                and c.zone == restaurant
            ]

            # Trie par position verticale actuelle pour garder l'ordre naturel
            inside_clients.sort(key=lambda c: c.rect.centery)
            inside_clients = inside_clients[:3]  # Max 3 clients à l'intérieur

            for idx, client in enumerate(inside_clients):
                if idx >= max_len:
                    break
                client.queue_tile_x = queue_x
                client.queue_tile_y = queue_start_y + idx
                # S'il n'est pas déjà bien positionné, on le remet en mouvement
                target_px = client.queue_tile_x * TILE_SIZE + TILE_SIZE // 2
                target_py = client.queue_tile_y * TILE_SIZE + TILE_SIZE // 2
                dist = ((client.rect.centerx - target_px) ** 2 + (client.rect.centery - target_py) ** 2) ** 0.5
                if dist > 4 and client.state not in ['angry', 'fleeing', 'dying', 'dead', 'gone']:
                    client.state = "walking_to_queue"

            # --- File extérieure devant le resto ---
            if not street_zone:
                continue

            # Porte dans la rue vers ce restaurant
            street_door = None
            for door in street_zone.doors:
                dx, dy, target_zone, _, _ = door
                if target_zone == restaurant:
                    street_door = door
                    break

            if not street_door:
                continue

            door_x, door_y, _, _, _ = street_door

            outside_clients = [
                c for c in self.clients
                if c.zone == "street"
                and getattr(c, "target_zone", None) == restaurant
                and c.state in ("walking_to_restaurant", "waiting_outside")
            ]

            # Trie par distance à la porte pour ordonner la file
            def dist_to_door(client):
                cx = client.rect.centerx
                cy = client.rect.centery
                door_cx = door_x * TILE_SIZE + TILE_SIZE // 2
                door_cy = door_y * TILE_SIZE + TILE_SIZE // 2
                return ((cx - door_cx) ** 2 + (cy - door_cy) ** 2) ** 0.5

            outside_clients.sort(key=dist_to_door)

            # Place au maximum 3 clients dehors
            for idx, client in enumerate(outside_clients[:3]):
                client.outside_tile_x = door_x
                client.outside_tile_y = min(street_zone.height - 1, door_y + 1 + idx)
                if client.state in ("walking_to_restaurant", "waiting_outside"):
                    client.state = "waiting_outside"

    def spawn_client(self):
        """Fait apparaître un client qui va vers un restaurant.
        La probabilité de spawn dépend de la réputation de chaque restaurant.
        Plus la réputation est haute, plus de clients viennent.
        """
        # Calculer les probabilités basées sur la réputation
        tacos_rep = self.players[0].reputation
        kebab_rep = self.players[1].reputation
        
        # Au début (réputation égale à 50%), c'est 50/50
        # Ensuite, la probabilité est proportionnelle à la réputation
        total_rep = tacos_rep + kebab_rep
        
        if total_rep <= 0:
            # Fallback si les deux sont à 0
            target_restaurant = random.choice(["tacos", "kebab"])
        else:
            # Probabilité basée sur la réputation
            tacos_probability = tacos_rep / total_rep
            target_restaurant = "tacos" if random.random() < tacos_probability else "kebab"

        street_zone = self.world_map.get_zone("street")
        if not street_zone:
            return

        # Limite globale de clients présents dans la rue
        street_total = len([c for c in self.clients if c.zone == "street"])
        if street_total >= self.wandering_clients_limit:
            return

        # Maximum 3 clients qui attendent à l'extérieur pour ce resto
        outside_clients = [
            c for c in self.clients
            if c.zone == "street" and getattr(c, "target_zone", None) == target_restaurant
        ]
        if len(outside_clients) >= 3:
            return

        # Cherche la porte de rue qui mène à ce restaurant
        street_door = None
        for door in street_zone.doors:
            dx, dy, target_zone, _, _ = door
            if target_zone == target_restaurant:
                street_door = door
                break

        if not street_door:
            # Fallback: spawn directement dans le restaurant
            zone = self.world_map.get_zone(target_restaurant)
            if zone:
                x = random.randint(2, zone.width - 3)
                y = random.randint(4, zone.height - 2)
                client = Client(x * TILE_SIZE, y * TILE_SIZE, target_restaurant, target_zone=target_restaurant)
                client.state = "waiting"
                client.spawn_time = time.time()
                self.clients.append(client)
                play_sound('client_spawn', 'client')
            return

        door_x, door_y, _, _, _ = street_door

        # Position de spawn: un peu plus loin dans la rue
        spawn_x = door_x
        spawn_y = min(street_zone.height - 1, door_y + 2)

        # Calcule la file d'attente dans le restaurant
        queue_x, queue_start_y, max_queue_length = self._get_queue_config(target_restaurant)
        if queue_x is None:
            return

        # Tous les clients qui visent le même restaurant et sont à l'intérieur
        restaurant_clients = [
            c for c in self.clients
            if getattr(c, "target_zone", None) == target_restaurant
            and c.zone == target_restaurant
        ]
        queue_index = min(len(restaurant_clients), 2)  # max 3 clients (0,1,2)

        if queue_index >= max_queue_length:
            return

        queue_y = queue_start_y + queue_index

        # Création du client: il apparaît dans la rue
        client = Client(spawn_x * TILE_SIZE, spawn_y * TILE_SIZE, zone="street", target_zone=target_restaurant)
        client.queue_tile_x = queue_x
        client.queue_tile_y = queue_y

        self.clients.append(client)
        self._recompute_queues()
        play_sound('client_spawn', 'client')

    def _spawn_wandering_client(self):
        """Crée un client qui se balade dans la rue sans cible initiale."""
        street_zone = self.world_map.get_zone("street")
        if not street_zone:
            return

        # Essaie quelques positions aléatoires sur le trottoir / route
        for _ in range(10):
            x = random.randint(0, street_zone.width - 1)
            y = random.randint(4, street_zone.height - 1)
            if street_zone.is_walkable(x, y):
                client = Client(x * TILE_SIZE, y * TILE_SIZE, zone="street", target_zone=None)
                self.clients.append(client)
                return
        
    def get_remaining_time(self):
        elapsed = time.time() - self.start_time
        remaining = max(0, self.game_duration - elapsed)
        return int(remaining)
            
    def draw_zone(self, surface, camera, zone_name):
        zone = self.world_map.get_zone(zone_name)
        if zone:
            self.world_map.draw_zone(zone, surface, camera)
            
        # Dessiner les armes au sol
        self.weapon_spawner.draw(surface, camera, zone_name)
            
        # Dessiner les clients
        for client in self.clients:
            if client.zone == zone_name:
                client.draw(surface, camera)
                
        # Dessiner les animations globales
        self.animation_manager.draw(surface, camera)
                
    def get_winner(self):
        if self.players[0].money > self.players[1].money:
            return 1
        elif self.players[1].money > self.players[0].money:
            return 2
        else:
            return 0
            
    def get_available_sabotages(self, player_idx):
        """Retourne les sabotages disponibles pour un joueur"""
        player = self.players[player_idx]
        return self.sabotage_manager.get_available_sabotages(player)
        
    def get_player_stock_status(self, player_idx):
        """Retourne le statut du stock d'un joueur"""
        player = self.players[player_idx]
        return {
            'ingredients': player.food_stock.ingredients,
            'low_stock': player.get_low_stock_warning(),
            'spit_available': player.food_stock.is_spit_available(),
            'spit_cooldown': player.food_stock.get_spit_cooldown()
        }
