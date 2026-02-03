"""
Menu de configuration des touches
"""
import pygame
from config import *
from input.controls import get_key_bindings
from game.audio import play_sound


class KeybindMenu:
    def __init__(self, screen):
        self.screen = screen
        self.visible = False
        
        # Fonts
        self.title_font = pygame.font.SysFont(None, 48)
        self.font = pygame.font.SysFont(None, 28)
        self.small_font = pygame.font.SysFont(None, 22)
        
        # Key bindings
        self.key_bindings = get_key_bindings()
        
        # État
        self.selected_player = 0  # 0 ou 1
        self.selected_action = 0
        self.waiting_for_key = False
        self.actions = ['up', 'down', 'left', 'right', 'interact', 'attack', 'sabotage', 'inventory']
        
        # Dimensions
        self.menu_width = 700
        self.menu_height = 500
        self.menu_x = (SCREEN_WIDTH - self.menu_width) // 2
        self.menu_y = (SCREEN_HEIGHT - self.menu_height) // 2
        
    def toggle(self):
        self.visible = not self.visible
        self.waiting_for_key = False
        if self.visible:
            play_sound('menu_select', 'ui')
            
    def close(self):
        self.visible = False
        self.waiting_for_key = False
        
    def handle_input(self, event):
        if not self.visible:
            return None
            
        if event.type == pygame.KEYDOWN:
            # Si on attend une touche
            if self.waiting_for_key:
                if event.key == pygame.K_ESCAPE:
                    self.waiting_for_key = False
                    play_sound('menu_move', 'ui')
                    return "cancel"
                    
                # Vérifier si la touche est déjà utilisée
                player = f'player{self.selected_player + 1}'
                action = self.actions[self.selected_action]
                used, used_player, used_action = self.key_bindings.is_key_used(
                    event.key, exclude_player=player, exclude_action=action
                )
                
                if used:
                    # Touche déjà utilisée
                    play_sound('stock_empty', 'ui')
                    return "key_used"
                    
                # Assigner la nouvelle touche
                self.key_bindings.set_key(player, action, event.key)
                self.waiting_for_key = False
                play_sound('menu_select', 'ui')
                return "key_set"
                
            # Navigation normale
            if event.key == pygame.K_ESCAPE:
                self.close()
                return "close"
                
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.selected_player = 0
                play_sound('menu_move', 'ui')
                return "navigate"
                
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.selected_player = 1
                play_sound('menu_move', 'ui')
                return "navigate"
                
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_action = (self.selected_action - 1) % len(self.actions)
                play_sound('menu_move', 'ui')
                return "navigate"
                
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_action = (self.selected_action + 1) % len(self.actions)
                play_sound('menu_move', 'ui')
                return "navigate"
                
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.waiting_for_key = True
                play_sound('menu_select', 'ui')
                return "wait_key"
                
            # Reset avec R
            if event.key == pygame.K_r:
                player = f'player{self.selected_player + 1}'
                self.key_bindings.reset_to_default(player)
                play_sound('menu_select', 'ui')
                return "reset"
                
        return None
        
    def draw(self):
        if not self.visible:
            return
            
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Fond du menu
        menu_rect = pygame.Rect(self.menu_x, self.menu_y, self.menu_width, self.menu_height)
        pygame.draw.rect(self.screen, (30, 30, 45), menu_rect, border_radius=15)
        pygame.draw.rect(self.screen, MENU_ACCENT, menu_rect, 3, border_radius=15)
        
        # Titre
        title = self.title_font.render("Configuration des Touches", True, WHITE)
        self.screen.blit(title, (self.menu_x + (self.menu_width - title.get_width()) // 2, self.menu_y + 15))
        
        # Tabs joueurs
        tab_y = self.menu_y + 70
        tab_width = (self.menu_width - 60) // 2
        
        for i, player_name in enumerate(["JOUEUR 1", "JOUEUR 2"]):
            tab_x = self.menu_x + 20 + i * (tab_width + 20)
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, 40)
            
            color = ORANGE if i == 0 else GREEN
            
            if i == self.selected_player:
                pygame.draw.rect(self.screen, color, tab_rect, border_radius=8)
                text_color = BLACK
            else:
                pygame.draw.rect(self.screen, (50, 50, 60), tab_rect, border_radius=8)
                pygame.draw.rect(self.screen, (80, 80, 90), tab_rect, 1, border_radius=8)
                text_color = GRAY
                
            tab_text = self.font.render(player_name, True, text_color)
            self.screen.blit(tab_text, (tab_x + (tab_width - tab_text.get_width()) // 2, tab_y + 10))
            
        # Liste des touches
        list_y = tab_y + 60
        player_key = f'player{self.selected_player + 1}'
        player_color = ORANGE if self.selected_player == 0 else GREEN
        
        for i, action in enumerate(self.actions):
            item_y = list_y + i * 40
            item_rect = pygame.Rect(self.menu_x + 40, item_y, self.menu_width - 80, 35)
            
            # Highlight si sélectionné
            if i == self.selected_action:
                pygame.draw.rect(self.screen, (50, 50, 70), item_rect, border_radius=5)
                pygame.draw.rect(self.screen, player_color, item_rect, 2, border_radius=5)
                
            # Nom de l'action
            action_name = self.key_bindings.get_action_name(action)
            name_text = self.font.render(action_name, True, WHITE)
            self.screen.blit(name_text, (item_rect.x + 15, item_y + 7))
            
            # Touche actuelle
            current_key = self.key_bindings.get_key(player_key, action)
            key_name = self.key_bindings.get_key_name(current_key)
            
            # Si on attend une touche pour cette action
            if self.waiting_for_key and i == self.selected_action:
                key_text = self.font.render("Appuyez sur une touche...", True, YELLOW)
            else:
                key_text = self.font.render(f"[ {key_name} ]", True, player_color)
                
            self.screen.blit(key_text, (item_rect.right - key_text.get_width() - 15, item_y + 7))
            
        # Instructions
        instructions_y = self.menu_y + self.menu_height - 60
        
        if self.waiting_for_key:
            inst_text = "Appuyez sur la nouvelle touche | ÉCHAP pour annuler"
        else:
            inst_text = "↑↓ Naviguer | ←→ Changer joueur | ENTRÉE Modifier | R Réinitialiser | ÉCHAP Fermer"
            
        inst_surface = self.small_font.render(inst_text, True, GRAY)
        self.screen.blit(inst_surface, (self.menu_x + (self.menu_width - inst_surface.get_width()) // 2, instructions_y))
        
        # Warning si touche déjà utilisée
        if self.waiting_for_key:
            warning = self.small_font.render("(Les touches déjà utilisées seront refusées)", True, (180, 100, 100))
            self.screen.blit(warning, (self.menu_x + (self.menu_width - warning.get_width()) // 2, instructions_y + 25))
