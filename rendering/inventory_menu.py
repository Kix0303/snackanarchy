"""
Menu d'inventaire pour afficher le stock de nourriture et les équipements
"""
import pygame
from config import *

class InventoryMenu:
    """Gestionnaire des inventaires pour les deux joueurs"""
    
    def __init__(self, screen):
        self.screen = screen
        
        # Deux inventaires séparés, un pour chaque joueur
        self.player_menus = [
            PlayerInventoryMenu(screen, 0),  # Joueur 1 (gauche)
            PlayerInventoryMenu(screen, 1),  # Joueur 2 (droite)
        ]
        
    @property
    def visible(self):
        """Retourne True si au moins un inventaire est ouvert"""
        return any(menu.visible for menu in self.player_menus)
    
    def is_visible_for(self, player_idx):
        """Vérifie si l'inventaire est ouvert pour un joueur spécifique"""
        return self.player_menus[player_idx].visible
        
    def toggle(self, player_idx):
        """Ouvre/ferme l'inventaire pour un joueur"""
        self.player_menus[player_idx].toggle()
            
    def close(self, player_idx=None):
        """Ferme l'inventaire d'un joueur ou tous les inventaires"""
        if player_idx is not None:
            self.player_menus[player_idx].close()
        else:
            for menu in self.player_menus:
                menu.close()
        
    def handle_input(self, event, game_state):
        """Gère les inputs pour les deux inventaires"""
        results = []
        for menu in self.player_menus:
            if menu.visible:
                result = menu.handle_input(event, game_state)
                if result:
                    results.append((menu.player_idx, result))
        
        # Retourner le premier résultat significatif
        for player_idx, result in results:
            if result:
                return result
        return None
        
    def draw(self, game_state):
        """Dessine les inventaires ouverts"""
        for menu in self.player_menus:
            if menu.visible:
                menu.draw(game_state)


class PlayerInventoryMenu:
    """Menu d'inventaire pour un joueur spécifique"""
    
    def __init__(self, screen, player_idx):
        self.screen = screen
        self.player_idx = player_idx
        self.visible = False
        
        # Fonts
        self.title_font = pygame.font.SysFont(None, 36)
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 20)
        
        # Position du menu (sur la moitié d'écran du joueur)
        self.menu_width = 350
        self.menu_height = 450
        
        # Calcul de la position selon le joueur
        half_screen = SCREEN_WIDTH // 2
        if player_idx == 0:
            # Joueur 1: moitié gauche
            self.menu_x = (half_screen - self.menu_width) // 2
        else:
            # Joueur 2: moitié droite
            self.menu_x = half_screen + (half_screen - self.menu_width) // 2
        self.menu_y = (SCREEN_HEIGHT - self.menu_height) // 2
        
        # Tab sélectionné
        self.current_tab = 0  # 0 = Stock, 1 = Équipement, 2 = Sabotages
        self.tabs = ["Stock", "Équipement", "Sabotages"]
        
        # Scroll
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Sélection pour réappro
        self.selected_ingredient = 0
        
    def toggle(self):
        """Ouvre/ferme l'inventaire"""
        self.visible = not self.visible
        if self.visible:
            self.scroll_offset = 0
            self.selected_ingredient = 0
            
    def close(self):
        self.visible = False
        
    def handle_input(self, event, game_state):
        """Gère les inputs dans le menu d'inventaire"""
        if not self.visible:
            return None
        
        # Touches spécifiques selon le joueur
        if self.player_idx == 0:
            # Joueur 1: ZQSD + E + Tab/I
            key_up = pygame.K_w
            key_down = pygame.K_s
            key_left = pygame.K_a
            key_right = pygame.K_d
            key_action = pygame.K_e
            key_close = [pygame.K_ESCAPE, pygame.K_i, pygame.K_TAB]
        else:
            # Joueur 2: Flèches + Entrée + L
            key_up = pygame.K_UP
            key_down = pygame.K_DOWN
            key_left = pygame.K_LEFT
            key_right = pygame.K_RIGHT
            key_action = pygame.K_RETURN
            key_close = [pygame.K_ESCAPE, pygame.K_l, pygame.K_RSHIFT]
            
        if event.type == pygame.KEYDOWN:
            # Fermer le menu
            if event.key in key_close:
                self.close()
                return "close"
                
            # Navigation tabs
            if event.key == key_left:
                self.current_tab = (self.current_tab - 1) % len(self.tabs)
                self.scroll_offset = 0
                self.selected_ingredient = 0
                return "navigate"
                
            if event.key == key_right:
                self.current_tab = (self.current_tab + 1) % len(self.tabs)
                self.scroll_offset = 0
                self.selected_ingredient = 0
                return "navigate"
                
            # Navigation verticale dans le stock
            if self.current_tab == 0:
                player = game_state.players[self.player_idx]
                ingredients = list(player.food_stock.ingredients.keys())
                
                if event.key == key_up:
                    self.selected_ingredient = max(0, self.selected_ingredient - 1)
                    return "navigate"
                    
                if event.key == key_down:
                    self.selected_ingredient = min(len(ingredients) - 1, self.selected_ingredient + 1)
                    return "navigate"
                    
                # Réapprovisionner l'ingrédient sélectionné
                if event.key == key_action:
                    if ingredients:
                        ing_name = ingredients[self.selected_ingredient]
                        amount, cost = player.restock(ing_name)
                        if amount > 0:
                            return f"restock_{ing_name}"
                    return None
                    
            # Sabotages
            if self.current_tab == 2:
                sabotages = game_state.get_available_sabotages(self.player_idx)
                
                if event.key == key_up:
                    self.selected_ingredient = max(0, self.selected_ingredient - 1)
                    return "navigate"
                    
                if event.key == key_down:
                    self.selected_ingredient = min(len(sabotages) - 1, self.selected_ingredient + 1)
                    return "navigate"
                    
                # Exécuter le sabotage sélectionné
                if event.key == key_action:
                    if sabotages and self.selected_ingredient < len(sabotages):
                        sabotage = sabotages[self.selected_ingredient]
                        if sabotage['cooldown'] <= 0:
                            success, msg = game_state.handle_sabotage(self.player_idx, sabotage['name'])
                            if success:
                                self.close()
                                return f"sabotage_{sabotage['name']}"
                    return None
                    
        return None
        
    def draw(self, game_state):
        """Dessine le menu d'inventaire"""
        if not self.visible:
            return
            
        player = game_state.players[self.player_idx]
        
        # Overlay semi-transparent uniquement sur la moitié d'écran du joueur
        half_screen = SCREEN_WIDTH // 2
        if self.player_idx == 0:
            overlay_x = 0
        else:
            overlay_x = half_screen
        
        overlay = pygame.Surface((half_screen, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (overlay_x, 0))
        
        # Fond du menu
        menu_rect = pygame.Rect(self.menu_x, self.menu_y, self.menu_width, self.menu_height)
        pygame.draw.rect(self.screen, (30, 30, 40), menu_rect, border_radius=15)
        pygame.draw.rect(self.screen, MENU_ACCENT, menu_rect, 3, border_radius=15)
        
        # Titre
        title_color = ORANGE if self.player_idx == 0 else GREEN
        title = self.title_font.render(f"Inventaire - {player.username}", True, title_color)
        self.screen.blit(title, (self.menu_x + 15, self.menu_y + 12))
        
        # Argent disponible
        money_text = self.font.render(f"${player.money}", True, YELLOW)
        self.screen.blit(money_text, (self.menu_x + self.menu_width - 80, self.menu_y + 15))
        
        # Tabs
        tab_y = self.menu_y + 50
        tab_width = (self.menu_width - 30) // len(self.tabs)
        for i, tab in enumerate(self.tabs):
            tab_x = self.menu_x + 15 + i * tab_width
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width - 5, 30)
            
            if i == self.current_tab:
                pygame.draw.rect(self.screen, MENU_ACCENT, tab_rect, border_radius=5)
                text_color = BLACK
            else:
                pygame.draw.rect(self.screen, (50, 50, 60), tab_rect, border_radius=5)
                pygame.draw.rect(self.screen, (80, 80, 90), tab_rect, 1, border_radius=5)
                text_color = WHITE
                
            tab_text = self.small_font.render(tab, True, text_color)
            text_x = tab_x + (tab_width - 5 - tab_text.get_width()) // 2
            self.screen.blit(tab_text, (text_x, tab_y + 6))
            
        # Contenu selon le tab
        content_y = tab_y + 40
        content_height = self.menu_height - 120
        
        if self.current_tab == 0:
            self._draw_stock_tab(player, content_y, content_height)
        elif self.current_tab == 1:
            self._draw_equipment_tab(player, content_y, content_height)
        else:
            self._draw_sabotage_tab(game_state, content_y, content_height)
            
        # Instructions en bas (selon le joueur)
        if self.player_idx == 0:
            instructions = "WS Nav | AD Tabs | E Select | I/Tab Fermer"
        else:
            instructions = "↑↓ Nav | ←→ Tabs | Entrée Select | L Fermer"
        inst_text = self.small_font.render(instructions, True, GRAY)
        self.screen.blit(inst_text, (self.menu_x + 15, self.menu_y + self.menu_height - 25))
        
    def _draw_stock_tab(self, player, start_y, height):
        """Dessine l'onglet du stock"""
        x = self.menu_x + 15
        y = start_y
        
        ingredients = list(player.food_stock.ingredients.items())
        
        for i, (name, data) in enumerate(ingredients):
            if y > self.menu_y + self.menu_height - 50:
                break
                
            # Highlight si sélectionné
            item_rect = pygame.Rect(x - 3, y - 2, self.menu_width - 30, 30)
            if i == self.selected_ingredient:
                pygame.draw.rect(self.screen, (60, 60, 80), item_rect, border_radius=5)
                pygame.draw.rect(self.screen, MENU_ACCENT, item_rect, 2, border_radius=5)
                
            # Nom de l'ingrédient (traduit)
            display_name = self._translate_ingredient(name)
            name_text = self.small_font.render(display_name, True, WHITE)
            self.screen.blit(name_text, (x, y + 2))
            
            # Barre de stock
            bar_x = x + 120
            bar_width = 100
            bar_height = 14
            
            # Fond
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, y + 5, bar_width, bar_height), border_radius=3)
            
            # Remplissage
            fill_pct = data['quantity'] / data['max']
            fill_width = int(bar_width * fill_pct)
            
            if fill_pct > 0.5:
                fill_color = GREEN
            elif fill_pct > 0.2:
                fill_color = ORANGE
            else:
                fill_color = RED
                
            if fill_width > 0:
                pygame.draw.rect(self.screen, fill_color, (bar_x, y + 5, fill_width, bar_height), border_radius=3)
                
            # Texte quantité
            qty_text = self.small_font.render(f"{data['quantity']}/{data['max']}", True, WHITE)
            self.screen.blit(qty_text, (bar_x + bar_width + 5, y + 3))
                    
            y += 32
            
        # Prix réappro si sélectionné
        if self.selected_ingredient < len(ingredients):
            name, data = ingredients[self.selected_ingredient]
            needed = data['max'] - data['quantity']
            cost = int(needed * data['price'])
            if needed > 0:
                restock_text = self.small_font.render(f"Réappro: ${cost}", True, YELLOW)
                self.screen.blit(restock_text, (x, y + 5))
            
        # Status broche
        y += 25
        if player.food_stock.is_spit_available():
            spit_text = self.small_font.render("Broche: OK", True, GREEN)
        else:
            cooldown = int(player.food_stock.get_spit_cooldown())
            spit_text = self.small_font.render(f"Broche volee! ({cooldown}s)", True, RED)
        self.screen.blit(spit_text, (x, y))
        
    def _draw_equipment_tab(self, player, start_y, height):
        """Dessine l'onglet des équipements"""
        x = self.menu_x + 15
        y = start_y
        
        equipment_names = {
            'fryer': 'Friteuse',
            'spit': 'Broche',
            'menu': 'Menu',
            'register': 'Caisse',
            'toilets': 'Toilettes'
        }
        
        for eq_key, eq in player.equipment.items():
            name = equipment_names.get(eq_key, eq_key)
            status = eq.get_status()
            
            # Couleur selon status
            if status == "OK":
                status_color = GREEN
            else:
                status_color = RED
                
            # Ligne équipement
            eq_text = self.small_font.render(name, True, WHITE)
            self.screen.blit(eq_text, (x, y))
            
            status_text = self.small_font.render(status, True, status_color)
            self.screen.blit(status_text, (x + 140, y))
            
            # Description (tronquée si trop longue)
            desc = eq.description[:35] + "..." if len(eq.description) > 35 else eq.description
            desc_text = self.small_font.render(desc, True, GRAY)
            self.screen.blit(desc_text, (x + 10, y + 18))
            
            y += 42
            
        # Arme équipée
        y += 5
        weapon_info = player.get_weapon_info()
        if weapon_info:
            weapon_text = self.small_font.render(f"Arme: {weapon_info['name']} ({weapon_info['uses']})", True, RED)
        else:
            weapon_text = self.small_font.render("Arme: Aucune", True, GRAY)
        self.screen.blit(weapon_text, (x, y))
        
    def _draw_sabotage_tab(self, game_state, start_y, height):
        """Dessine l'onglet des sabotages"""
        x = self.menu_x + 15
        y = start_y
        
        player = game_state.players[self.player_idx]
        sabotages = game_state.get_available_sabotages(self.player_idx)
        
        if not sabotages:
            no_sab = self.small_font.render("Aucun sabotage disponible", True, GRAY)
            self.screen.blit(no_sab, (x, y))
            return
            
        for i, sab in enumerate(sabotages):
            if y > self.menu_y + self.menu_height - 60:
                break
                
            # Highlight si sélectionné
            item_rect = pygame.Rect(x - 3, y - 2, self.menu_width - 30, 42)
            if i == self.selected_ingredient:
                pygame.draw.rect(self.screen, (60, 60, 80), item_rect, border_radius=5)
                pygame.draw.rect(self.screen, RED, item_rect, 2, border_radius=5)
                
            # Nom et coût
            can_afford = player.money >= sab['cost']
            name_color = WHITE if can_afford else GRAY
            name_text = self.small_font.render(sab['display_name'], True, name_color)
            self.screen.blit(name_text, (x, y))
            
            cost_color = YELLOW if can_afford else RED
            cost_text = self.small_font.render(f"${sab['cost']}", True, cost_color)
            self.screen.blit(cost_text, (x + 180, y))
            
            # Cooldown
            if sab['cooldown'] > 0:
                cd_text = self.small_font.render(f"Recharge: {int(sab['cooldown'])}s", True, ORANGE)
                self.screen.blit(cd_text, (x + 10, y + 20))
            else:
                ready_text = self.small_font.render("Pret!", True, GREEN)
                self.screen.blit(ready_text, (x + 10, y + 20))
                
            # Indicateur de proximité requise
            if sab['requires_proximity']:
                prox_text = self.small_font.render("Proximite requise", True, ORANGE)
                self.screen.blit(prox_text, (x + 100, y + 20))
                
            y += 48
            
    def _translate_ingredient(self, name):
        """Traduit les noms d'ingrédients en français lisible"""
        translations = {
            'galette': 'Galette',
            'viande': 'Viande',
            'sauce_fromagere': 'Sauce Fromagère',
            'frites': 'Frites',
            'sel': 'Sel',
            'pain_pita': 'Pain Pita',
            'viande_kebab': 'Viande Kebab',
            'salade': 'Salade',
            'tomates': 'Tomates',
            'oignons': 'Oignons',
            'sauce_blanche': 'Sauce Blanche',
        }
        return translations.get(name, name.replace('_', ' ').title())
