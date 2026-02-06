"""
Système d'inventaire et de stock de nourriture pour SnackAnarchy
Gère les ingrédients disponibles et les armes ramassables
"""
import pygame
import time
import random
from config import *

class FoodStock:
    """Stock de nourriture pour un restaurant"""
    
    def __init__(self, restaurant_type='tacos'):
        self.restaurant_type = restaurant_type
        
        # Stock initial
        if restaurant_type == 'tacos':
            self.ingredients = {
                'galette': {'quantity': 20, 'max': 30, 'price': 2},
                'viande': {'quantity': 15, 'max': 25, 'price': 5},
                'sauce_fromagere': {'quantity': 25, 'max': 40, 'price': 1},
                'frites': {'quantity': 30, 'max': 50, 'price': 2},
                'sel': {'quantity': 50, 'max': 100, 'price': 0.5},
            }
        else:  # kebab
            self.ingredients = {
                'pain_pita': {'quantity': 20, 'max': 30, 'price': 2},
                'viande_kebab': {'quantity': 15, 'max': 25, 'price': 6},
                'salade': {'quantity': 25, 'max': 40, 'price': 1},
                'tomates': {'quantity': 20, 'max': 35, 'price': 1},
                'oignons': {'quantity': 25, 'max': 40, 'price': 1},
                'sauce_blanche': {'quantity': 30, 'max': 50, 'price': 1},
            }
            
        # Pour le sabotage de vol de broche
        self.has_spit = True
        self.spit_stolen_until = 0
        
    def use_ingredient(self, ingredient_name, amount=1):
        """Utilise un ingrédient du stock. Retourne True si succès."""
        if ingredient_name not in self.ingredients:
            return False
            
        ing = self.ingredients[ingredient_name]
        if ing['quantity'] >= amount:
            ing['quantity'] -= amount
            return True
        return False
        
    def use_recipe(self, recipe_ingredients):
        """Utilise les ingrédients d'une recette.
        recipe_ingredients: dict { nom_ingrédient: quantité } ou liste (1 par élément).
        Retourne (True, None) si OK, (False, nom_ingrédient_manquant) sinon."""
        # Normaliser en dict { ing_name: quantité }
        if isinstance(recipe_ingredients, dict):
            need = list(recipe_ingredients.items())
        else:
            from collections import Counter
            need = list(Counter(recipe_ingredients).items())
        # Vérifier que tout est disponible
        for ing_name, amount in need:
            if ing_name in self.ingredients and self.ingredients[ing_name]['quantity'] < amount:
                return False, ing_name
        # Utiliser les ingrédients
        for ing_name, amount in need:
            if ing_name in self.ingredients:
                self.ingredients[ing_name]['quantity'] -= amount
        return True, None
        
    def restock(self, ingredient_name, amount=None, dry_run=False):
        """Réapprovisionne un ingrédient (coûte de l'argent).
        Si dry_run=True, calcule et retourne (amount, cost) sans modifier le stock."""
        if ingredient_name not in self.ingredients:
            return 0, 0
            
        ing = self.ingredients[ingredient_name]
        if amount is None:
            amount = ing['max'] - ing['quantity']
            
        amount = min(amount, ing['max'] - ing['quantity'])
        if amount <= 0:
            return 0, 0
            
        cost = int(amount * ing['price'])
        if not dry_run:
            ing['quantity'] += amount
        return amount, cost
        
    def restock_all(self, dry_run=False):
        """Réapprovisionne tout (coûte de l'argent).
        Si dry_run=True, calcule le coût total sans modifier le stock."""
        total_cost = 0
        for ing_name in self.ingredients:
            _, cost = self.restock(ing_name, dry_run=dry_run)
            total_cost += cost
        return total_cost
        
    def get_low_stock(self, threshold=5):
        """Retourne les ingrédients en rupture de stock"""
        low = []
        for name, data in self.ingredients.items():
            if data['quantity'] <= threshold:
                low.append((name, data['quantity'], data['max']))
        return low
        
    def is_spit_available(self):
        """Vérifie si la broche est disponible"""
        if not self.has_spit:
            return False
        if time.time() < self.spit_stolen_until:
            return False
        return True
        
    def steal_spit(self, duration=30):
        """Vole la broche pour une durée donnée"""
        self.spit_stolen_until = time.time() + duration
        return True
        
    def get_spit_cooldown(self):
        """Retourne le temps restant avant récupération de la broche"""
        remaining = self.spit_stolen_until - time.time()
        return max(0, remaining)


class Weapon:
    """Arme ramassable (couteau ou fourchette)"""
    
    def __init__(self, weapon_type, x, y, zone):
        self.weapon_type = weapon_type  # 'knife' ou 'fork'
        self.x = x
        self.y = y
        self.zone = zone
        self.picked_up = False
        self.spawn_time = time.time()
        self.despawn_time = 30  # Disparaît après 30 secondes
        
        # Stats
        if weapon_type == 'knife':
            self.damage = 100  # Tue instantanément
            self.range = TILE_SIZE * 1.5
            self.name = "Couteau"
            self.color = (180, 180, 180)
        else:  # fork
            self.damage = 100
            self.range = TILE_SIZE * 2
            self.name = "Fourchette"
            self.color = (150, 150, 150)
            
        # Rect pour collision
        self.rect = pygame.Rect(x, y, 32, 32)
        
    def update(self):
        """Met à jour l'arme (vérifie le despawn)"""
        if time.time() - self.spawn_time > self.despawn_time:
            return False  # Doit être supprimée
        return True
        
    def draw(self, surface, camera):
        """Dessine l'arme au sol"""
        if self.picked_up:
            return
            
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y
        
        # Ombre
        pygame.draw.ellipse(surface, (50, 50, 50, 100), 
                          (draw_x + 4, draw_y + 24, 24, 8))
        
        # Animation de flottement
        bob = pygame.math.Vector2(0, 3 * pygame.math.Vector2(1, 0).rotate(time.time() * 200).y)
        
        if self.weapon_type == 'knife':
            # Dessiner un couteau
            # Lame
            pygame.draw.polygon(surface, self.color, [
                (draw_x + 8 + bob.x, draw_y + 5 + bob.y),
                (draw_x + 24 + bob.x, draw_y + 5 + bob.y),
                (draw_x + 28 + bob.x, draw_y + 12 + bob.y),
                (draw_x + 8 + bob.x, draw_y + 12 + bob.y),
            ])
            # Manche
            pygame.draw.rect(surface, (139, 90, 43), 
                           (draw_x + 2 + bob.x, draw_y + 7 + bob.y, 8, 6))
        else:
            # Dessiner une fourchette
            # Manche
            pygame.draw.rect(surface, (139, 90, 43),
                           (draw_x + 4 + bob.x, draw_y + 15 + bob.y, 6, 12))
            # Dents
            for i in range(4):
                pygame.draw.rect(surface, self.color,
                               (draw_x + 3 + i * 5 + bob.x, draw_y + 2 + bob.y, 3, 15))
                               
        # Indicateur de ramassage
        font = pygame.font.SysFont(None, 18)
        text = font.render("[E]", True, WHITE)
        surface.blit(text, (draw_x + 5, draw_y - 15))


class PlayerInventory:
    """Inventaire d'un joueur"""
    
    def __init__(self, player_id):
        self.player_id = player_id
        self.weapon = None  # Arme équipée
        self.stolen_spit = None  # Broche volée (si applicable)
        self.weapon_uses = 0  # Nombre d'utilisations restantes
        self.max_weapon_uses = 3
        
    def pickup_weapon(self, weapon):
        """Ramasse une arme"""
        if self.weapon is not None:
            return False  # Déjà une arme
        self.weapon = weapon
        self.weapon_uses = self.max_weapon_uses
        weapon.picked_up = True
        return True
        
    def use_weapon(self):
        """Utilise l'arme (réduit le compteur)"""
        if self.weapon is None:
            return None
            
        self.weapon_uses -= 1
        weapon = self.weapon
        
        if self.weapon_uses <= 0:
            self.weapon = None
            
        return weapon
        
    def has_weapon(self):
        return self.weapon is not None
        
    def get_weapon_info(self):
        if self.weapon is None:
            return None
        return {
            'type': self.weapon.weapon_type,
            'name': self.weapon.name,
            'uses': self.weapon_uses
        }
        
    def drop_weapon(self):
        """Lâche l'arme actuelle"""
        weapon = self.weapon
        self.weapon = None
        self.weapon_uses = 0
        return weapon


class WeaponSpawner:
    """Gère le spawn des armes sur la carte"""
    
    def __init__(self):
        self.weapons = []
        self.spawn_interval = 10  # Spawn toutes les 10 secondes
        self.last_spawn = time.time()
        self.max_weapons = 4
        
        # Positions de spawn possibles par zone
        self.spawn_points = {
            'tacos': [(3, 5), (7, 3), (5, 6)],
            'kebab': [(3, 5), (7, 3), (5, 6)],
            'street': [(5, 4), (9, 4), (7, 6)],
        }
        # Compteur de spawns par zone pour répartition équitable (tacos, kebab, rue)
        self.spawn_counts = {zone: 0 for zone in self.spawn_points}
        
    def update(self):
        """Met à jour le spawner"""
        # Nettoyer les armes expirées ou ramassées
        self.weapons = [w for w in self.weapons if w.update() and not w.picked_up]
        
        # Spawn périodique
        if time.time() - self.last_spawn > self.spawn_interval:
            if len(self.weapons) < self.max_weapons:
                self.spawn_weapon()
            self.last_spawn = time.time()
            
    def spawn_weapon(self, zone=None, position=None):
        """Spawn une arme aléatoire, de façon équitable entre tacos, kebab et rue."""
        if zone is None:
            # Choisir une zone parmi celles qui ont le moins de spawns (équité)
            min_count = min(self.spawn_counts.values())
            zones_equitables = [z for z in self.spawn_points if self.spawn_counts[z] == min_count]
            zone = random.choice(zones_equitables)
            self.spawn_counts[zone] += 1
            
        if position is None:
            positions = self.spawn_points.get(zone, [(5, 5)])
            pos = random.choice(positions)
            x, y = pos[0] * TILE_SIZE, pos[1] * TILE_SIZE
        else:
            x, y = position
            
        weapon_type = random.choice(['knife', 'fork'])
        weapon = Weapon(weapon_type, x, y, zone)
        self.weapons.append(weapon)
        return weapon
        
    def get_weapons_in_zone(self, zone):
        """Retourne les armes dans une zone donnée"""
        return [w for w in self.weapons if w.zone == zone and not w.picked_up]
        
    def check_pickup(self, player_rect, zone):
        """Vérifie si le joueur peut ramasser une arme"""
        for weapon in self.weapons:
            if weapon.zone != zone or weapon.picked_up:
                continue
            if player_rect.colliderect(weapon.rect):
                return weapon
        return None
        
    def draw(self, surface, camera, zone):
        """Dessine les armes d'une zone"""
        for weapon in self.get_weapons_in_zone(zone):
            weapon.draw(surface, camera)


# Recettes : dict { nom_ingrédient: quantité } — chaque plat consomme un nombre d'ingrédients différent
RECIPES = {
    # Tacos (galette, viande, sauce_fromagere, frites, sel)
    'Tacos S': {'galette': 1, 'viande': 1, 'sauce_fromagere': 1, 'frites': 1},  # 4
    'Tacos M': {'galette': 1, 'viande': 1, 'sauce_fromagere': 1, 'frites': 1, 'sel': 1},  # 5
    'Tacos L': {'galette': 2, 'viande': 1, 'sauce_fromagere': 1, 'frites': 2, 'sel': 1},  # 7
    'Tacos XXL': {'galette': 2, 'viande': 2, 'sauce_fromagere': 2, 'frites': 2, 'sel': 1},  # 9
    'Burritos': {'galette': 2, 'viande': 1, 'sauce_fromagere': 1, 'frites': 1, 'sel': 1},  # 6
    'Nachos': {'galette': 1, 'viande': 1, 'sauce_fromagere': 2, 'frites': 2, 'sel': 1},  # 7
    # Kebab (pain_pita, viande_kebab, salade, tomates, oignons)
    'Kebab': {'pain_pita': 1, 'viande_kebab': 1, 'salade': 1, 'tomates': 1, 'oignons': 1},  # 5
    'Kebab Wrap': {'pain_pita': 2, 'viande_kebab': 1, 'salade': 1, 'tomates': 1, 'oignons': 1},  # 6
    'Assiettes': {'pain_pita': 1, 'viande_kebab': 2, 'salade': 2, 'tomates': 1, 'oignons': 1},  # 7
}
