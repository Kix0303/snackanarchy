import pygame
import time
from config import *
from rendering.camera import Camera
from input.controls import get_key_bindings
from rendering.mission_display import MissionDisplay

class SplitScreenRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.width = SCREEN_WIDTH // 2
        self.height = SCREEN_HEIGHT
        
        self.surface1 = pygame.Surface((self.width, self.height))
        self.surface2 = pygame.Surface((self.width, self.height))
        
        self.camera1 = Camera(self.width, self.height)
        self.camera2 = Camera(self.width, self.height)
        
        self.font = pygame.font.SysFont(None, 32)
        self.small_font = pygame.font.SysFont(None, 24)
        self.tiny_font = pygame.font.SysFont(None, 18)
        self.big_font = pygame.font.SysFont(None, 48)
        
        # Pour le clignotement des avertissements
        self.blink_timer = 0
        
        # Affichage des missions
        self.mission_display = MissionDisplay()
        
    def draw(self, game_state):
        self.blink_timer = time.time()
        
        p1 = game_state.players[0]
        p2 = game_state.players[1]
        
        # Get zones for each player
        zone1 = game_state.world_map.get_zone(p1.current_zone)
        zone2 = game_state.world_map.get_zone(p2.current_zone)
        
        # Update cameras
        self.camera1.update(p1, zone1)
        self.camera2.update(p2, zone2)
        
        # Draw P1 View (vue du joueur 1)
        self.surface1.fill(DARK_GRAY)
        game_state.draw_zone(self.surface1, self.camera1, p1.current_zone)
        # Dessiner P1 sur sa propre vue (box de service visible uniquement pour P1)
        p1.draw(self.surface1, self.camera1, viewport_owner_id=p1.id)
        # Si P2 est dans la même zone que P1, le dessiner aussi sur la vue P1 (sans sa box de service)
        if p2.current_zone == p1.current_zone:
            p2.draw(self.surface1, self.camera1, viewport_owner_id=p1.id)
            p2.animation_manager.draw(self.surface1, self.camera1)
        # Dessiner les animations du joueur 1
        p1.animation_manager.draw(self.surface1, self.camera1)
        
        # Draw P2 View (vue du joueur 2)
        self.surface2.fill(DARK_GRAY)
        game_state.draw_zone(self.surface2, self.camera2, p2.current_zone)
        # Dessiner P2 sur sa propre vue (box de service visible uniquement pour P2)
        p2.draw(self.surface2, self.camera2, viewport_owner_id=p2.id)
        # Si P1 est dans la même zone que P2, le dessiner aussi sur la vue P2 (sans sa box de service)
        if p1.current_zone == p2.current_zone:
            p1.draw(self.surface2, self.camera2, viewport_owner_id=p2.id)
            p1.animation_manager.draw(self.surface2, self.camera2)
        # Dessiner les animations du joueur 2
        p2.animation_manager.draw(self.surface2, self.camera2)
        
        # Blit to main screen
        self.screen.blit(self.surface1, (0, 0))
        self.screen.blit(self.surface2, (self.width, 0))
        
        # Draw Divider
        pygame.draw.line(self.screen, BORDER_COLOR, (self.width, 0), (self.width, self.height), BORDER_THICKNESS)
        
        # Draw HUD
        self._draw_hud(game_state, p1, p2)
        
        # Draw missions
        self._draw_missions(p1, p2)
        
        # Box de service (minigame) au-dessus du HUD pour qu'elle ne soit jamais cachée
        self._draw_minigames_on_top(p1, p2)
        
        # Draw controls hint at bottom
        self._draw_controls_hint()
        
        # Draw game over screen if needed
        if game_state.game_over:
            self._draw_game_over(game_state)
        
    def _draw_hud(self, game_state, p1, p2):
        # Timer at center top
        remaining = game_state.get_remaining_time()
        minutes = remaining // 60
        seconds = remaining % 60
        timer_text = self.big_font.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)
        timer_rect = timer_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
        
        # Timer background
        bg_rect = timer_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, BLACK, bg_rect, border_radius=5)
        self.screen.blit(timer_text, timer_rect)
        
        # P1 HUD (left) - use username
        p1_name = getattr(p1, 'username', 'TACOS')
        self._draw_player_hud(10, 50, p1, p1_name, ORANGE)
        
        # P2 HUD (right) - use username
        p2_name = getattr(p2, 'username', 'KEBAB')
        self._draw_player_hud(self.width + 10, 50, p2, p2_name, GREEN)
        
    def _draw_player_hud(self, x, y, player, resto_name, color):
        # Background panel - plus grand pour les nouvelles infos
        panel_rect = pygame.Rect(x, y, 200, 120)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, color, panel_rect, 2, border_radius=8)
        
        # Restaurant name
        name_text = self.small_font.render(resto_name, True, color)
        self.screen.blit(name_text, (x + 10, y + 5))
        
        # Zone indicator
        zone_text = self.small_font.render(f"[{player.current_zone.upper()}]", True, (150, 150, 150))
        self.screen.blit(zone_text, (x + 120, y + 5))
        
        # Money
        money_text = self.font.render(f"{player.money} €", True, (255, 215, 0))
        self.screen.blit(money_text, (x + 10, y + 25))
        
        # Reputation bar
        rep_label = self.small_font.render("Rep:", True, WHITE)
        self.screen.blit(rep_label, (x + 10, y + 55))
        
        # Rep bar background
        bar_x = x + 50
        bar_width = 130
        pygame.draw.rect(self.screen, GRAY, (bar_x, y + 57, bar_width, 15), border_radius=3)
        
        # Rep bar fill
        fill_width = int(bar_width * player.reputation / 100)
        rep_color = GREEN if player.reputation > 50 else ORANGE if player.reputation > 25 else RED
        pygame.draw.rect(self.screen, rep_color, (bar_x, y + 57, fill_width, 15), border_radius=3)
        
        # Rep text
        rep_text = self.small_font.render(f"{player.reputation}%", True, WHITE)
        self.screen.blit(rep_text, (bar_x + bar_width // 2 - 15, y + 55))
        
        # === Nouvelles infos ===
        
        # Arme équipée (icône dessinée, pas d'emoji)
        weapon_info = player.get_weapon_info()
        if weapon_info:
            weapon_color = (200, 50, 50)
            self._draw_weapon_icon(self.screen, x + 10, y + 78, 14, weapon_color)
            weapon_text = self.tiny_font.render(f"{weapon_info['name']} ({weapon_info['uses']})", True, weapon_color)
            self.screen.blit(weapon_text, (x + 28, y + 80))
        else:
            no_weapon_text = self.tiny_font.render("Pas d'arme", True, GRAY)
            self.screen.blit(no_weapon_text, (x + 10, y + 80))
            
        # Stock bas - clignotant (icône triangle avertissement)
        low_stock = player.get_low_stock_warning()
        if low_stock and int(self.blink_timer * 3) % 2 == 0:
            self._draw_warning_icon(self.screen, x + 100, y + 79, 12, RED)
            stock_text = self.tiny_font.render("STOCK BAS!", True, RED)
            self.screen.blit(stock_text, (x + 116, y + 80))
            
        # Broche volée indicator
        if not player.food_stock.is_spit_available():
            cooldown = player.food_stock.get_spit_cooldown()
            spit_text = self.tiny_font.render(f"Broche volee: {int(cooldown)}s", True, RED)
            self.screen.blit(spit_text, (x + 10, y + 98))
        # Cooldown balai
        elif hasattr(player, 'sweep_cooldown') and player.sweep_cooldown > 0:
            sweep_text = self.tiny_font.render(f"Balai: {int(player.sweep_cooldown)}s", True, ORANGE)
            self.screen.blit(sweep_text, (x + 10, y + 98))
        elif hasattr(player, 'can_sweep') and player.can_sweep():
            sweep_text = self.tiny_font.render("Balai pret!", True, GREEN)
            self.screen.blit(sweep_text, (x + 10, y + 98))
    
    def _draw_arrow_icon(self, surface, direction, x, y, size, color):
        """Dessine une icône de flèche directionnelle (sans emoji)."""
        cx, cy = x + size // 2, y + size // 2
        if direction == 'up':
            points = [(cx, y + 2), (x + size - 2, y + size - 4), (x + 2, y + size - 4)]
        elif direction == 'down':
            points = [(cx, y + size - 2), (x + 2, y + 4), (x + size - 2, y + 4)]
        elif direction == 'left':
            points = [(x + 2, cy), (x + size - 4, y + 2), (x + size - 4, y + size - 2)]
        elif direction == 'right':
            points = [(x + size - 2, cy), (x + 4, y + 2), (x + 4, y + size - 2)]
        else:
            return
        pygame.draw.polygon(surface, color, points)
    
    def _draw_action_icon(self, surface, action, x, y, size, color):
        """Dessine une icône pour chaque type d'action (sans emoji)."""
        cx, cy = x + size // 2, y + size // 2
        if action in ['up', 'down', 'left', 'right']:
            self._draw_arrow_icon(surface, action, x, y, size, color)
        elif action == 'interact':
            pygame.draw.circle(surface, color, (cx, cy - 2), size // 3, 2)
            pygame.draw.line(surface, color, (cx, cy + 2), (cx, y + size - 2), 2)
        elif action == 'attack':
            pygame.draw.line(surface, color, (x + 3, y + size - 3), (x + size - 3, y + 3), 2)
            pygame.draw.line(surface, color, (x + size - 6, y + 6), (x + size - 3, y + 9), 2)
        elif action == 'sweep':
            pygame.draw.line(surface, color, (cx, y + 2), (cx, y + size - 6), 2)
            pygame.draw.line(surface, color, (x + 3, y + size - 3), (x + size - 3, y + size - 3), 3)
        elif action == 'inventory':
            pygame.draw.rect(surface, color, (x + 4, y + 5, size - 8, size - 8), 2, border_radius=2)
            pygame.draw.line(surface, color, (x + 7, y + 2), (x + 7, y + 6), 2)
            pygame.draw.line(surface, color, (x + size - 7, y + 2), (x + size - 7, y + 6), 2)
            pygame.draw.line(surface, color, (x + 7, y + 2), (x + size - 7, y + 2), 2)
    
    def _draw_key_cap(self, surface, key_name, x, y, color, w=None, h=20):
        """Dessine une touche clavier (cap) avec le nom de la touche."""
        pad = 6
        text_surf = self.tiny_font.render(key_name, True, color)
        tw, th = text_surf.get_width(), text_surf.get_height()
        min_w = 24
        preferred = tw + pad * 2
        if w is None:
            bw = max(min_w, preferred)
        else:
            bw = min(max(w, preferred), 44)
        bh = max(h, th + 4)
        rect = pygame.Rect(x, y, bw, bh)
        pygame.draw.rect(surface, (35, 35, 45), rect, border_radius=4)
        pygame.draw.rect(surface, color, rect, 1, border_radius=4)
        tr = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, (rect.x + (bw - tw) // 2, rect.y + (bh - th) // 2))
        return rect.right
    
    def _draw_weapon_icon(self, surface, x, y, size, color):
        """Petite icône couteau/arme (sans emoji)."""
        cx, cy = x + size // 2, y + size // 2
        pygame.draw.line(surface, color, (x + 2, y + size - 2), (cx + 2, y + 2), 2)
        pygame.draw.line(surface, color, (cx + 2, y + 2), (x + size - 2, y + size - 4), 2)
    
    def _draw_warning_icon(self, surface, x, y, size, color):
        """Petite icône triangle avertissement (sans emoji)."""
        cx, cy = x + size // 2, y + size // 2
        points = [(cx, y + 2), (x + size - 2, y + size - 2), (x + 2, y + size - 2)]
        pygame.draw.polygon(surface, color, points, 2)
        
    def _draw_missions(self, p1, p2):
        """Affiche les missions des deux joueurs en haut à droite de chaque vue (texte entier, badges élargis)."""
        # Missions Joueur 1 (en haut à droite de la vue gauche)
        mission_y = 55  # Au même niveau que le HUD
        mission_width = 400  # Largeur agrandie pour afficher les noms de missions en entier
        mission_x1 = self.width - mission_width - 5  # Côté droit de la vue 1
        self.mission_display.draw(self.screen, p1, mission_x1, mission_y, mission_width)
        
        # Missions Joueur 2 (en haut à droite de la vue droite)
        mission_x2 = SCREEN_WIDTH - mission_width - 5  # Côté droit de la vue 2
        self.mission_display.draw(self.screen, p2, mission_x2, mission_y, mission_width)
    
    def _draw_minigames_on_top(self, p1, p2):
        """Dessine les box de service (minigames) au-dessus du HUD pour qu'elles ne soient jamais cachées."""
        # Joueur 1 : position dans sa vue (viewport gauche), puis coordonnées écran
        if p1.active_minigame:
            draw_x = p1.rect.x - self.camera1.x
            draw_y = p1.rect.y - self.camera1.y + p1.bob_offset
            p1.active_minigame.draw(self.screen, draw_x - 50, draw_y - 140)
        # Joueur 2 : position dans sa vue (viewport droit), offset écran = self.width
        if p2.active_minigame:
            draw_x = p2.rect.x - self.camera2.x
            draw_y = p2.rect.y - self.camera2.y + p2.bob_offset
            p2.active_minigame.draw(self.screen, self.width + draw_x - 50, draw_y - 140)
    
    def _draw_controls_hint(self):
        """Déplacement en haut (icônes flèches en gris pour les touches flèches), autres touches en bas sans répéter J1:/J2:."""
        kb = get_key_bindings()
        hint_color = (180, 180, 190)
        arrow_icon_color = (120, 120, 130)
        arrow_icon_size = 12
        y_move = SCREEN_HEIGHT - 44
        y_actions = SCREEN_HEIGHT - 22
        move_actions = ['up', 'down', 'left', 'right']
        other_actions = ['interact', 'attack', 'sweep', 'inventory', 'carte']
        arrow_keys = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
        
        for i, (player_key, label) in enumerate([
            ('player1', 'J1:'),
            ('player2', 'J2:'),
        ]):
            x = 10 if i == 0 else self.width + 10
            # Ligne du haut : déplacements (J1:/J2: une seule fois, icônes flèches en gris si touche flèche)
            label_surf = self.tiny_font.render(f"{label}  ", True, hint_color)
            self.screen.blit(label_surf, (x, y_move))
            xx = x + label_surf.get_width()
            sep = self.tiny_font.render(" | ", True, hint_color)
            for j, a in enumerate(move_actions):
                key_code = kb.get_key(player_key, a)
                action_name = kb.get_action_name(a)
                if key_code in arrow_keys:
                    self._draw_arrow_icon(self.screen, a, xx, y_move + 2, arrow_icon_size, arrow_icon_color)
                    xx += arrow_icon_size
                else:
                    key_name = kb.get_key_name(key_code)
                    part_surf = self.tiny_font.render(key_name, True, hint_color)
                    self.screen.blit(part_surf, (xx, y_move))
                    xx += part_surf.get_width()
                eq_surf = self.tiny_font.render(f"={action_name}", True, hint_color)
                self.screen.blit(eq_surf, (xx, y_move))
                xx += eq_surf.get_width()
                if j < len(move_actions) - 1:
                    self.screen.blit(sep, (xx, y_move))
                    xx += sep.get_width()
            # Ligne du bas : autres touches (sans J1:/J2:)
            parts_other = [
                f"{kb.get_key_name(kb.get_key(player_key, a))}={kb.get_action_name(a)}"
                for a in other_actions
            ]
            line_other = " | ".join(parts_other)
            text_other = self.tiny_font.render(line_other, True, hint_color)
            self.screen.blit(text_other, (x, y_actions))
        
    def _draw_game_over(self, game_state):
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text
        go_font = pygame.font.SysFont(None, 72)
        go_text = go_font.render("FIN DE PARTIE!", True, WHITE)
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(go_text, go_rect)
        
        # Winner
        winner = game_state.get_winner()
        p1 = game_state.players[0]
        p2 = game_state.players[1]
        
        p1_name = getattr(p1, 'username', 'Joueur 1')
        p2_name = getattr(p2, 'username', 'Joueur 2')
        
        if winner == 1:
            winner_text = f"{p1_name} GAGNE!"
            winner_color = ORANGE
        elif winner == 2:
            winner_text = f"{p2_name} GAGNE!"
            winner_color = GREEN
        else:
            winner_text = "ÉGALITÉ!"
            winner_color = WHITE
            
        win_render = self.big_font.render(winner_text, True, winner_color)
        win_rect = win_render.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(win_render, win_rect)
        
        # Scores
        score_text = self.font.render(f"{p1_name}: {p1.money} €  |  {p2_name}: {p2.money} €", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(score_text, score_rect)
        
        # Stats détaillées
        stats_y = SCREEN_HEIGHT // 2 + 100
        
        # Stats Joueur 1
        p1_clients = getattr(p1, 'clients_served', 0)
        p1_missions = getattr(p1, 'missions_completed', 0)
        p1_stats = f"{p1_name}: Rep {p1.reputation}% | Clients: {p1_clients} | Missions: {p1_missions}"
        p1_stats_text = self.small_font.render(p1_stats, True, ORANGE)
        self.screen.blit(p1_stats_text, (SCREEN_WIDTH // 4 - 120, stats_y))
        
        # Stats Joueur 2
        p2_clients = getattr(p2, 'clients_served', 0)
        p2_missions = getattr(p2, 'missions_completed', 0)
        p2_stats = f"{p2_name}: Rep {p2.reputation}% | Clients: {p2_clients} | Missions: {p2_missions}"
        p2_stats_text = self.small_font.render(p2_stats, True, GREEN)
        self.screen.blit(p2_stats_text, (3 * SCREEN_WIDTH // 4 - 120, stats_y))
        
        # Restart hint
        hint_text = self.small_font.render("Appuyez sur ESPACE pour rejouer ou ÉCHAP pour quitter", True, GRAY)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(hint_text, hint_rect)
