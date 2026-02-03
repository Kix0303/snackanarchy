import pygame
import json
import os
from game.audio import play_sound


class KeyBindings:
    """Classe pour gérer les touches configurables"""
    
    # Touches par défaut
    DEFAULT_BINDINGS = {
        'player1': {
            'up': pygame.K_w,
            'down': pygame.K_s,
            'left': pygame.K_a,
            'right': pygame.K_d,
            'interact': pygame.K_e,
            'attack': pygame.K_q,
            'sabotage': pygame.K_r,
            'inventory': pygame.K_i,
        },
        'player2': {
            'up': pygame.K_UP,
            'down': pygame.K_DOWN,
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'interact': pygame.K_RETURN,
            'attack': pygame.K_RCTRL,
            'sabotage': pygame.K_BACKSPACE,
            'inventory': pygame.K_BACKSLASH,
        }
    }
    
    # Noms affichables des touches
    KEY_NAMES = {
        pygame.K_w: 'W', pygame.K_a: 'A', pygame.K_s: 'S', pygame.K_d: 'D',
        pygame.K_e: 'E', pygame.K_q: 'Q', pygame.K_r: 'R', pygame.K_f: 'F',
        pygame.K_i: 'I', pygame.K_TAB: 'TAB', pygame.K_SPACE: 'ESPACE',
        pygame.K_UP: '↑', pygame.K_DOWN: '↓', pygame.K_LEFT: '←', pygame.K_RIGHT: '→',
        pygame.K_RETURN: 'ENTRÉE', pygame.K_RSHIFT: 'R-SHIFT', pygame.K_LSHIFT: 'L-SHIFT',
        pygame.K_RCTRL: 'R-CTRL', pygame.K_LCTRL: 'L-CTRL',
        pygame.K_BACKSPACE: 'RETOUR', pygame.K_BACKSLASH: '\\',
        pygame.K_RALT: 'R-ALT', pygame.K_LALT: 'L-ALT',
        pygame.K_1: '1', pygame.K_2: '2', pygame.K_3: '3', pygame.K_4: '4',
        pygame.K_5: '5', pygame.K_6: '6', pygame.K_7: '7', pygame.K_8: '8',
        pygame.K_9: '9', pygame.K_0: '0',
        pygame.K_z: 'Z', pygame.K_x: 'X', pygame.K_c: 'C', pygame.K_v: 'V',
        pygame.K_b: 'B', pygame.K_n: 'N', pygame.K_m: 'M',
        pygame.K_g: 'G', pygame.K_h: 'H', pygame.K_j: 'J', pygame.K_k: 'K',
        pygame.K_l: 'L', pygame.K_p: 'P', pygame.K_o: 'O', pygame.K_u: 'U',
        pygame.K_y: 'Y', pygame.K_t: 'T',
        pygame.K_COMMA: ',', pygame.K_PERIOD: '.', pygame.K_SLASH: '/',
        pygame.K_SEMICOLON: ';', pygame.K_QUOTE: "'",
        pygame.K_LEFTBRACKET: '[', pygame.K_RIGHTBRACKET: ']',
        pygame.K_KP0: 'PAD0', pygame.K_KP1: 'PAD1', pygame.K_KP2: 'PAD2',
        pygame.K_KP3: 'PAD3', pygame.K_KP4: 'PAD4', pygame.K_KP5: 'PAD5',
        pygame.K_KP6: 'PAD6', pygame.K_KP7: 'PAD7', pygame.K_KP8: 'PAD8',
        pygame.K_KP9: 'PAD9',
    }
    
    # Noms des actions en français
    ACTION_NAMES = {
        'up': 'Haut',
        'down': 'Bas',
        'left': 'Gauche',
        'right': 'Droite',
        'interact': 'Servir',
        'attack': 'Attaque',
        'sabotage': 'Sabotage',
        'inventory': 'Inventaire',
    }
    
    def __init__(self):
        self.bindings = {
            'player1': dict(self.DEFAULT_BINDINGS['player1']),
            'player2': dict(self.DEFAULT_BINDINGS['player2']),
        }
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'keybindings.json')
        self.load()
        
    def load(self):
        """Charge les touches depuis le fichier de config"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    for player in ['player1', 'player2']:
                        if player in data:
                            for action, key_code in data[player].items():
                                if action in self.bindings[player]:
                                    self.bindings[player][action] = key_code
        except Exception as e:
            print(f"Erreur chargement keybindings: {e}")
            
    def save(self):
        """Sauvegarde les touches dans le fichier de config"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.bindings, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde keybindings: {e}")
            
    def get_key(self, player, action):
        """Récupère la touche pour une action"""
        return self.bindings[player].get(action, 0)
        
    def set_key(self, player, action, key_code):
        """Définit une nouvelle touche pour une action"""
        if action in self.bindings[player]:
            self.bindings[player][action] = key_code
            self.save()
            
    def get_key_name(self, key_code):
        """Retourne le nom affichable d'une touche"""
        if key_code in self.KEY_NAMES:
            return self.KEY_NAMES[key_code]
        return pygame.key.name(key_code).upper()
        
    def get_action_name(self, action):
        """Retourne le nom français d'une action"""
        return self.ACTION_NAMES.get(action, action)
        
    def reset_to_default(self, player=None):
        """Remet les touches par défaut"""
        if player:
            self.bindings[player] = dict(self.DEFAULT_BINDINGS[player])
        else:
            self.bindings['player1'] = dict(self.DEFAULT_BINDINGS['player1'])
            self.bindings['player2'] = dict(self.DEFAULT_BINDINGS['player2'])
        self.save()
        
    def is_key_used(self, key_code, exclude_player=None, exclude_action=None):
        """Vérifie si une touche est déjà utilisée"""
        for player, actions in self.bindings.items():
            for action, key in actions.items():
                if key == key_code:
                    if exclude_player == player and exclude_action == action:
                        continue
                    return True, player, action
        return False, None, None


# Instance globale
_key_bindings = None

def get_key_bindings():
    global _key_bindings
    if _key_bindings is None:
        _key_bindings = KeyBindings()
    return _key_bindings


class InputHandler:
    def __init__(self):
        # Pour éviter les inputs répétés
        self.last_action_time = {0: 0, 1: 0}
        self.action_cooldown = 0.15  # 150ms entre les actions
        self.key_bindings = get_key_bindings()
        
    def handle_input(self, players, events):
        import time
        keys = pygame.key.get_pressed()
        current_time = time.time()
        
        kb = self.key_bindings
        
        # Movement Player 1
        p1_dx, p1_dy = 0, 0
        if keys[kb.get_key('player1', 'up')]: p1_dy = -1
        if keys[kb.get_key('player1', 'down')]: p1_dy = 1
        if keys[kb.get_key('player1', 'left')]: p1_dx = -1
        if keys[kb.get_key('player1', 'right')]: p1_dx = 1
        players[0].move(p1_dx, p1_dy)
        
        # Movement Player 2
        p2_dx, p2_dy = 0, 0
        if keys[kb.get_key('player2', 'up')]: p2_dy = -1
        if keys[kb.get_key('player2', 'down')]: p2_dy = 1
        if keys[kb.get_key('player2', 'left')]: p2_dx = -1
        if keys[kb.get_key('player2', 'right')]: p2_dx = 1
        players[1].move(p2_dx, p2_dy)
        
        # Actions avec les touches
        for event in events:
            if event.type == pygame.KEYDOWN:
                # === JOUEUR 1 ===
                if event.key == kb.get_key('player1', 'interact'):
                    if current_time - self.last_action_time[0] > self.action_cooldown:
                        self.last_action_time[0] = current_time
                        return (0, "interact")
                        
                if event.key == kb.get_key('player1', 'attack'):
                    if current_time - self.last_action_time[0] > self.action_cooldown:
                        self.last_action_time[0] = current_time
                        if players[0].inventory.has_weapon():
                            return (0, "attack")
                        else:
                            play_sound('stock_empty', 'player1')
                            
                if event.key == kb.get_key('player1', 'sabotage'):
                    if current_time - self.last_action_time[0] > self.action_cooldown:
                        self.last_action_time[0] = current_time
                        return (0, "sabotage")
                
                # === JOUEUR 2 ===
                if event.key == kb.get_key('player2', 'interact'):
                    if current_time - self.last_action_time[1] > self.action_cooldown:
                        self.last_action_time[1] = current_time
                        return (1, "interact")
                        
                if event.key == kb.get_key('player2', 'attack'):
                    if current_time - self.last_action_time[1] > self.action_cooldown:
                        self.last_action_time[1] = current_time
                        if players[1].inventory.has_weapon():
                            return (1, "attack")
                        else:
                            play_sound('stock_empty', 'player2')
                            
                if event.key == kb.get_key('player2', 'sabotage'):
                    if current_time - self.last_action_time[1] > self.action_cooldown:
                        self.last_action_time[1] = current_time
                        return (1, "sabotage")
                    
        return None
        
    def check_inventory_key(self, event, player_idx):
        """Vérifie si la touche d'inventaire est pressée"""
        kb = self.key_bindings
        player_key = f'player{player_idx + 1}'
        return event.key == kb.get_key(player_key, 'inventory')