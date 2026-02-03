import pygame
import sys
import time
from config import *
from game.state import GameState
from rendering.split_screen import SplitScreenRenderer
from rendering.menu import MenuRenderer
from rendering.inventory_menu import InventoryMenu
from rendering.keybind_menu import KeybindMenu
from input.controls import InputHandler, get_key_bindings
from game.assets_loader import Assets
from game.audio import AudioManager, play_sound

# Game States
STATE_MENU = "menu"
STATE_SETUP = "setup"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_KEYBIND = "keybind"


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()  # Initialiser le mixer audio
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("SnackAnarchy")
        
        # Load Assets
        Assets.get().load_images()
        
        # Initialiser l'audio
        self.audio = AudioManager.get()
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state management
        self.current_state = STATE_MENU
        self.game_state = None
        self.pause_start_time = None
        self.total_pause_time = 0
        
        # Renderers
        self.renderer = SplitScreenRenderer(self.screen)
        self.menu_renderer = MenuRenderer(self.screen)
        self.inventory_menu = InventoryMenu(self.screen)
        self.keybind_menu = KeybindMenu(self.screen)
        self.input_handler = InputHandler()
        
        # Key bindings
        self.key_bindings = get_key_bindings()
        
    def start_game(self, player_configs=None):
        """Start a new game with player configurations"""
        self.game_state = GameState(player_configs)
        self.current_state = STATE_PLAYING
        self.total_pause_time = 0
        play_sound('menu_select', 'ui')
        
        # Démarrer la musique d'ambiance
        self.audio.play_music('ambient')
        
    def restart(self):
        """Restart the game with same configs"""
        configs = None
        if self.game_state:
            configs = self.game_state.player_configs
        self.start_game(configs)
        
    def pause_game(self):
        """Pause the game"""
        if self.current_state == STATE_PLAYING and self.game_state is not None:
            self.current_state = STATE_PAUSED
            self.pause_start_time = time.time()
            self.menu_renderer.reset_pause_selection()
            play_sound('menu_select', 'ui')
            
    def resume_game(self):
        """Resume the game from pause"""
        if self.current_state == STATE_PAUSED and self.pause_start_time:
            pause_duration = time.time() - self.pause_start_time
            self.total_pause_time += pause_duration
            if self.game_state:
                self.game_state.start_time += pause_duration
            self.pause_start_time = None
        self.current_state = STATE_PLAYING
        
    def return_to_menu(self):
        """Return to main menu"""
        self.current_state = STATE_MENU
        self.game_state = None
        self.menu_renderer.reset_to_main_menu()
        self.audio.stop_music()
        
    def toggle_inventory(self, player_idx):
        """Ouvre/ferme l'inventaire pour un joueur"""
        was_visible = self.inventory_menu.is_visible_for(player_idx)
        self.inventory_menu.toggle(player_idx)
        if not was_visible:
            play_sound('menu_select', 'ui')
        
    def run(self):
        while self.running:
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    continue
                
                # Gérer le menu des touches en priorité s'il est ouvert
                if self.keybind_menu.visible:
                    result = self.keybind_menu.handle_input(event)
                    if result == "close":
                        self.keybind_menu.close()
                    continue
                
                # Handle input based on current state
                if self.current_state == STATE_MENU:
                    # Check if menu switched to setup state internally
                    if self.menu_renderer.menu_state == MenuRenderer.STATE_PLAYER_SETUP:
                        self.current_state = STATE_SETUP
                    else:
                        action = self.menu_renderer.handle_menu_input(event)
                        if action == "QUITTER":
                            self.running = False
                        elif action == "TOUCHES":
                            self.keybind_menu.toggle()
                        # Check again after handling input
                        if self.menu_renderer.menu_state == MenuRenderer.STATE_PLAYER_SETUP:
                            self.current_state = STATE_SETUP
                
                elif self.current_state == STATE_SETUP:
                    action = self.menu_renderer.handle_setup_input(event)
                    if action == "START":
                        configs = self.menu_renderer.get_player_configs()
                        self.start_game(configs)
                    elif self.menu_renderer.menu_state == MenuRenderer.STATE_MAIN:
                        self.current_state = STATE_MENU
                        
                elif self.current_state == STATE_PAUSED:
                    action = self.menu_renderer.handle_pause_input(event)
                    if action == "REPRENDRE":
                        self.resume_game()
                    elif action == "TOUCHES":
                        self.keybind_menu.toggle()
                    elif action == "MENU PRINCIPAL":
                        self.return_to_menu()
                    elif action == "QUITTER":
                        self.running = False
                        
                elif self.current_state == STATE_PLAYING:
                    # Gérer les inventaires - chaque joueur peut ouvrir/fermer le sien
                    if event.type == pygame.KEYDOWN:
                        # Touches d'inventaire (toujours actives)
                        if event.key == self.key_bindings.get_key('player1', 'inventory'):
                            self.toggle_inventory(0)
                            continue
                        elif event.key == self.key_bindings.get_key('player2', 'inventory'):
                            self.toggle_inventory(1)
                            continue
                        # Pause
                        elif event.key == pygame.K_ESCAPE:
                            # Si un inventaire est ouvert, le fermer d'abord
                            if self.inventory_menu.visible:
                                self.inventory_menu.close()
                            else:
                                self.pause_game()
                            continue
                        elif event.key == pygame.K_SPACE and self.game_state and self.game_state.game_over:
                            self.restart()
                            continue
                    
                    # Gérer les inputs des inventaires ouverts
                    if self.inventory_menu.visible:
                        result = self.inventory_menu.handle_input(event, self.game_state)
                        if result == "close":
                            play_sound('menu_move', 'ui')
                        elif result == "navigate":
                            play_sound('menu_move', 'ui')

            # Update and draw based on current state
            if self.current_state == STATE_MENU:
                self.menu_renderer.draw_main_menu()
                # Dessiner le menu des touches par-dessus si ouvert
                if self.keybind_menu.visible:
                    self.keybind_menu.draw()
                
            elif self.current_state == STATE_SETUP:
                self.menu_renderer.draw_player_setup()
                
            elif self.current_state == STATE_PLAYING:
                if self.game_state:
                    # Le jeu continue même si un inventaire est ouvert
                    # mais les inputs du joueur avec inventaire ouvert sont ignorés
                    action = self.input_handler.handle_input(
                        self.game_state.players, 
                        events,
                        blocked_players=[
                            i for i in range(2) 
                            if self.inventory_menu.is_visible_for(i)
                        ]
                    )
                    self.game_state.update(events, action)
                    
                    self.renderer.draw(self.game_state)
                    
                    # Dessiner les inventaires par-dessus si ouverts
                    if self.inventory_menu.visible:
                        self.inventory_menu.draw(self.game_state)
                    
            elif self.current_state == STATE_PAUSED:
                if self.game_state:
                    self.renderer.draw(self.game_state)
                    self.menu_renderer.draw_pause_menu(self.game_state)
                # Dessiner le menu des touches par-dessus si ouvert
                if self.keybind_menu.visible:
                    self.keybind_menu.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
