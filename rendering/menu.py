import pygame
import math
import time
import random
import cv2
import os
import sys
from config import *
from game.assets_loader import Assets, get_resource_path


class MenuRenderer:
    """Handles main menu, player setup and pause menu rendering"""
    
    # Menu states
    STATE_MAIN = "main"
    STATE_PLAYER_SETUP = "player_setup"
    
    def __init__(self, screen):
        self.screen = screen
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        
        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 72, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 28)
        self.menu_font = pygame.font.SysFont("Arial", 36)
        self.small_font = pygame.font.SysFont("Arial", 22)
        self.hint_font = pygame.font.SysFont("Arial", 18)
        self.input_font = pygame.font.SysFont("Arial", 28)
        
        # Menu state
        self.menu_state = self.STATE_MAIN
        self.selected_option = 0
        self.main_menu_options = ["JOUER", "TOUCHES", "QUITTER"]
        self.pause_options = ["REPRENDRE", "TOUCHES", "MENU PRINCIPAL", "QUITTER"]
        self.pause_selected = 0
        
        # Player setup state
        self.player_configs = [
            {"name": "Joueur 1", "side": "left", "restaurant": "tacos"},
            {"name": "Joueur 2", "side": "right", "restaurant": "kebab"}
        ]
        self.setup_focus = 0  # 0=P1 name, 1=P1 side, 2=P2 name, 3=P2 side, 4=start button
        self.text_input_active = False
        self.editing_player = None
        
        # Animation
        self.start_time = time.time()
        
        # Colors - Theme colors
        self.tacos_color = (255, 140, 0)  # Orange
        self.kebab_color = (76, 175, 80)  # Green
        self.bg_dark = (25, 25, 35)
        self.bg_medium = (35, 35, 50)
        self.highlight_color = (255, 200, 100)
        self.button_bg = (45, 45, 60)
        self.button_hover = (60, 60, 80)
        self.button_border = (100, 100, 120)
        
        # Load menu-specific images
        self._load_menu_assets()
        
        # Background particles
        self.particles = []
        self._init_particles()
        
        # Background video
        self.video_capture = None
        self.video_frame = None
        self._load_background_video()
    
    def _load_background_video(self):
        """Load background video for main menu"""
        video_path = get_resource_path(os.path.join("assets", "background-menu.mp4"))
        print(f"[DEBUG] Chemin vidéo: {video_path}")
        print(f"[DEBUG] Fichier existe: {os.path.exists(video_path)}")
        
        if os.path.exists(video_path):
            try:
                self.video_capture = cv2.VideoCapture(video_path)
                if self.video_capture.isOpened():
                    self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
                    self.last_frame_time = 0
                    print(f"[DEBUG] Vidéo chargée avec succès, FPS: {self.video_fps}")
                else:
                    print(f"[DEBUG] OpenCV n'a pas pu ouvrir la vidéo")
                    self.video_capture = None
            except Exception as e:
                print(f"[DEBUG] Erreur chargement vidéo: {e}")
                self.video_capture = None
        else:
            print(f"[DEBUG] Fichier vidéo non trouvé")
    
    def _update_video_frame(self):
        """Update and return the current video frame as a pygame surface"""
        if self.video_capture is None:
            return None
        
        current_time = time.time()
        # Control frame rate based on video FPS
        if self.video_fps > 0 and (current_time - self.last_frame_time) < 1.0 / self.video_fps:
            return self.video_frame
        
        self.last_frame_time = current_time
        
        ret, frame = self.video_capture.read()
        if not ret:
            # Loop video
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_capture.read()
            if not ret:
                return None
        
        # Convert BGR to RGB and resize to screen size
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (self.width, self.height))
        
        # Convert to pygame surface
        self.video_frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        return self.video_frame
    
    def _load_menu_assets(self):
        """Load images for menu display"""
        self.menu_images = {}
        assets = Assets.get()
        
        # Facades - scaled for display
        for name in ["facade_tacos", "facade_kebab"]:
            img = assets.get_image(name)
            if img:
                scale = 0.8
                new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                self.menu_images[name] = pygame.transform.scale(img, new_size)
        
        # Players - scaled
        for name in ["player1", "player2"]:
            img = assets.get_image(name)
            if img:
                scale = 1.8
                new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                self.menu_images[name] = pygame.transform.scale(img, new_size)
        
        # Client for particles
        client = assets.get_image("client")
        if client:
            scale = 0.8
            new_size = (int(client.get_width() * scale), int(client.get_height() * scale))
            self.menu_images["client"] = pygame.transform.scale(client, new_size)
        
        # Floor tiles
        for name in ["interior_tacos", "interior_kebab", "sidewalk"]:
            img = assets.get_image(name)
            if img:
                self.menu_images[name] = img
    
    def _init_particles(self):
        """Initialize background particles"""
        for _ in range(6):
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'speed': random.uniform(0.15, 0.4),
                'scale': random.uniform(0.2, 0.4),
                'offset': random.uniform(0, 6.28)
            })
    
    def _update_particles(self):
        """Update particle positions"""
        for p in self.particles:
            p['y'] -= p['speed']
            p['x'] += math.sin(time.time() * 1.5 + p['offset']) * 0.2
            if p['y'] < -80:
                p['y'] = self.height + 80
                p['x'] = random.randint(0, self.width)
    
    def _draw_background(self):
        """Draw themed background"""
        # Gradient background
        for y in range(self.height):
            ratio = y / self.height
            r = int(25 + ratio * 8)
            g = int(25 + ratio * 6)
            b = int(35 + ratio * 12)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))
        
        # Draw particles
        self._update_particles()
        client_img = self.menu_images.get("client")
        for p in self.particles:
            if client_img:
                size = (int(client_img.get_width() * p['scale']),
                       int(client_img.get_height() * p['scale']))
                scaled = pygame.transform.scale(client_img, size)
                scaled.set_alpha(25)
                self.screen.blit(scaled, (int(p['x']), int(p['y'])))
    
    def _draw_themed_button(self, rect, text, is_selected, color=None):
        """Draw a themed button with game style"""
        elapsed = time.time() - self.start_time
        
        if color is None:
            color = self.button_border
        
        # Button background
        bg_color = self.button_hover if is_selected else self.button_bg
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        
        # Animated border for selected
        if is_selected:
            pulse = (math.sin(elapsed * 4) + 1) / 2
            border_color = (
                int(color[0] * 0.7 + 255 * 0.3 * pulse),
                int(color[1] * 0.7 + 255 * 0.3 * pulse),
                int(color[2] * 0.7 + 255 * 0.3 * pulse)
            )
            pygame.draw.rect(self.screen, border_color, rect, 3, border_radius=8)
            
            # Glow effect
            glow_rect = rect.inflate(6, 6)
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*color, 40), glow_surface.get_rect(), border_radius=10)
            self.screen.blit(glow_surface, glow_rect.topleft)
        else:
            pygame.draw.rect(self.screen, self.button_border, rect, 2, border_radius=8)
        
        # Text
        text_color = self.highlight_color if is_selected else (180, 180, 180)
        text_surface = self.menu_font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def _draw_input_field(self, rect, text, is_focused, label, color):
        """Draw a text input field"""
        elapsed = time.time() - self.start_time
        
        # Label above
        label_surface = self.small_font.render(label, True, color)
        self.screen.blit(label_surface, (rect.x, rect.y - 25))
        
        # Input background
        bg_color = (50, 50, 65) if is_focused else self.button_bg
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=6)
        
        # Border
        if is_focused:
            pygame.draw.rect(self.screen, color, rect, 2, border_radius=6)
        else:
            pygame.draw.rect(self.screen, self.button_border, rect, 1, border_radius=6)
        
        # Text with cursor
        display_text = text
        if is_focused and self.text_input_active:
            if int(elapsed * 2) % 2 == 0:
                display_text += "|"
        
        text_surface = self.input_font.render(display_text, True, WHITE)
        text_rect = text_surface.get_rect(midleft=(rect.x + 10, rect.centery))
        
        # Clip text to fit
        clip_rect = rect.inflate(-20, 0)
        self.screen.set_clip(clip_rect)
        self.screen.blit(text_surface, text_rect)
        self.screen.set_clip(None)
    
    def _draw_side_selector(self, rect, current_side, is_focused, color):
        """Draw side selection (left/right)"""
        elapsed = time.time() - self.start_time
        
        # Background
        pygame.draw.rect(self.screen, self.button_bg, rect, border_radius=6)
        
        if is_focused:
            pygame.draw.rect(self.screen, color, rect, 2, border_radius=6)
        else:
            pygame.draw.rect(self.screen, self.button_border, rect, 1, border_radius=6)
        
        # Split into two halves
        half_width = rect.width // 2
        left_rect = pygame.Rect(rect.x, rect.y, half_width, rect.height)
        right_rect = pygame.Rect(rect.x + half_width, rect.y, half_width, rect.height)
        
        # Stocker les rects pour le clic souris
        self._left_side_rect = left_rect
        self._right_side_rect = right_rect
        
        # Highlight selected side avec surface alpha (compatible macOS)
        highlight_surface = pygame.Surface((half_width, rect.height), pygame.SRCALPHA)
        highlight_surface.fill((*color, 100))
        if current_side == "left":
            self.screen.blit(highlight_surface, left_rect.topleft)
        else:
            self.screen.blit(highlight_surface, right_rect.topleft)
        
        # Arrows
        left_text = self.small_font.render("<- GAUCHE", True, 
                                           WHITE if current_side == "left" else (120, 120, 120))
        right_text = self.small_font.render("DROITE ->", True,
                                            WHITE if current_side == "right" else (120, 120, 120))
        
        self.screen.blit(left_text, left_text.get_rect(center=left_rect.center))
        self.screen.blit(right_text, right_text.get_rect(center=right_rect.center))
    
    def _draw_title(self):
        """Draw the game title"""
        elapsed = time.time() - self.start_time
        y_offset = math.sin(elapsed * 2) * 3
        
        # Unified title color (#f47b21)
        title_color = (244, 123, 33)
        snack = self.title_font.render("SNACK", True, title_color)
        anarchy = self.title_font.render("ANARCHY", True, title_color)
        
        total_width = snack.get_width() + 15 + anarchy.get_width()
        start_x = (self.width - total_width) // 2
        title_y = 50 + y_offset
        
        # Glow effects
        for surface, color, x in [(snack, (255, 180, 100), start_x), 
                                   (anarchy, (120, 220, 120), start_x + snack.get_width() + 15)]:
            glow = self.title_font.render(surface.get_rect().width and surface.get_rect().height and 
                                          "SNACK" if x == start_x else "ANARCHY", True, color)
            for off in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                glow_copy = glow.copy()
                glow_copy.set_alpha(40)
                self.screen.blit(glow_copy, (x + off[0], title_y + off[1]))
        
        self.screen.blit(snack, (start_x, title_y))
        self.screen.blit(anarchy, (start_x + snack.get_width() + 15, title_y))
    
    # ==================== MAIN MENU ====================
    
    def draw_main_menu(self):
        """Draw the main menu"""
        # Draw video background if available, otherwise fallback to default background
        video_frame = self._update_video_frame()
        if video_frame:
            self.screen.blit(video_frame, (0, 0))
            # Add a semi-transparent overlay for better text readability
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.screen.blit(overlay, (0, 0))
        else:
            self._draw_background()
        self._draw_title()
        
        # Menu buttons - centered
        button_width = 280
        button_height = 55
        button_spacing = 20
        start_y = 200
        
        for i, option in enumerate(self.main_menu_options):
            rect = pygame.Rect(
                self.width // 2 - button_width // 2,
                start_y + i * (button_height + button_spacing),
                button_width,
                button_height
            )
            color = self.tacos_color if i == 0 else (200, 80, 80)
            self._draw_themed_button(rect, option, i == self.selected_option, color)
        
        # VS display with players below buttons
        self._draw_vs_preview()
        
        # Controls hint
        hint = "↑↓ Naviguer  |  ENTRÉE Sélectionner  |  ÉCHAP Quitter"
        hint_surface = self.hint_font.render(hint, True, (100, 100, 120))
        self.screen.blit(hint_surface, hint_surface.get_rect(center=(self.width // 2, self.height - 25)))
    
    def _draw_vs_preview(self):
        """Draw VS preview with players"""
        elapsed = time.time() - self.start_time
        center_y = 450
        
        player1 = self.menu_images.get("player1")
        player2 = self.menu_images.get("player2")
        
        # Left player
        if player1:
            bounce = abs(math.sin(elapsed * 2.5)) * 4
            rect = player1.get_rect(center=(self.width // 4, center_y - bounce))
            self.screen.blit(player1, rect)
        
        tacos_label = self.subtitle_font.render("TACOS", True, self.tacos_color)
        self.screen.blit(tacos_label, tacos_label.get_rect(center=(self.width // 4, center_y + 70)))
        
        # VS
        vs_scale = 1 + math.sin(elapsed * 3) * 0.08
        vs_font = pygame.font.SysFont("Arial", int(48 * vs_scale), bold=True)
        vs_text = vs_font.render("VS", True, WHITE)
        self.screen.blit(vs_text, vs_text.get_rect(center=(self.width // 2, center_y)))
        
        # Right player
        if player2:
            bounce = abs(math.sin(elapsed * 2.5 + 1.5)) * 4
            rect = player2.get_rect(center=(3 * self.width // 4, center_y - bounce))
            self.screen.blit(player2, rect)
        
        kebab_label = self.subtitle_font.render("KEBAB", True, self.kebab_color)
        self.screen.blit(kebab_label, kebab_label.get_rect(center=(3 * self.width // 4, center_y + 70)))
    
    # ==================== PLAYER SETUP ====================
    
    def draw_player_setup(self):
        """Draw the player setup screen"""
        self._draw_background()
        
        # Title
        title = self.title_font.render("CONFIGURATION", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 50)))
        
        # Two player panels side by side
        panel_width = 400
        panel_height = 350
        panel_spacing = 80
        panel_y = 120
        
        # Player 1 panel (left)
        p1_x = self.width // 2 - panel_width - panel_spacing // 2
        self._draw_player_panel(p1_x, panel_y, panel_width, panel_height, 0, self.tacos_color)
        
        # Player 2 panel (right)
        p2_x = self.width // 2 + panel_spacing // 2
        self._draw_player_panel(p2_x, panel_y, panel_width, panel_height, 1, self.kebab_color)
        
        # Start button
        start_rect = pygame.Rect(self.width // 2 - 150, panel_y + panel_height + 30, 300, 60)
        self._draw_themed_button(start_rect, "COMMENCER", self.setup_focus == 4, self.kebab_color)
        
        # Controls hint
        if self.text_input_active:
            hint = "Tapez votre nom  |  ENTRÉE pour confirmer  |  ÉCHAP pour annuler"
        else:
            hint = "↑↓←→ Naviguer  |  ENTRÉE Modifier/Confirmer  |  ÉCHAP Retour"
        hint_surface = self.hint_font.render(hint, True, (100, 100, 120))
        self.screen.blit(hint_surface, hint_surface.get_rect(center=(self.width // 2, self.height - 25)))
    
    def _draw_player_panel(self, x, y, width, height, player_idx, color):
        """Draw a player configuration panel"""
        config = self.player_configs[player_idx]
        
        # Panel background
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, self.bg_medium, panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, color, panel_rect, 2, border_radius=12)
        
        # Player image
        player_img = self.menu_images.get(f"player{player_idx + 1}")
        if player_img:
            img_rect = player_img.get_rect(center=(x + width // 2, y + 70))
            self.screen.blit(player_img, img_rect)
        
        # Restaurant label
        resto = "TACOS" if config["restaurant"] == "tacos" else "KEBAB"
        resto_color = self.tacos_color if config["restaurant"] == "tacos" else self.kebab_color
        resto_text = self.subtitle_font.render(resto, True, resto_color)
        self.screen.blit(resto_text, resto_text.get_rect(center=(x + width // 2, y + 130)))
        
        # Name input
        name_rect = pygame.Rect(x + 30, y + 175, width - 60, 40)
        name_focus_idx = player_idx * 2  # 0 for P1, 2 for P2
        self._draw_input_field(
            name_rect, 
            config["name"], 
            self.setup_focus == name_focus_idx and self.text_input_active,
            "Pseudo:",
            color
        )
        
        # Highlight if focused but not editing
        if self.setup_focus == name_focus_idx and not self.text_input_active:
            pygame.draw.rect(self.screen, color, name_rect, 2, border_radius=6)
        
        # Side selector
        side_rect = pygame.Rect(x + 30, y + 260, width - 60, 45)
        side_label = self.small_font.render("Côté de l'écran:", True, color)
        self.screen.blit(side_label, (side_rect.x, side_rect.y - 25))
        
        side_focus_idx = player_idx * 2 + 1  # 1 for P1, 3 for P2
        self._draw_side_selector(side_rect, config["side"], self.setup_focus == side_focus_idx, color)
    
    # ==================== PAUSE MENU ====================
    
    def draw_pause_menu(self, game_state):
        """Draw pause menu overlay"""
        # Overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        elapsed = time.time() - self.start_time
        
        # Title
        pause_text = self.title_font.render("PAUSE", True, WHITE)
        y_offset = math.sin(elapsed * 2) * 3
        self.screen.blit(pause_text, pause_text.get_rect(center=(self.width // 2, 100 + y_offset)))
        
        # Score panel
        if game_state:
            p1 = game_state.players[0]
            p2 = game_state.players[1]
            
            panel_rect = pygame.Rect(self.width // 2 - 220, 160, 440, 100)
            pygame.draw.rect(self.screen, self.bg_medium, panel_rect, border_radius=10)
            pygame.draw.rect(self.screen, self.button_border, panel_rect, 2, border_radius=10)
            
            # Player names and scores
            p1_name = getattr(p1, 'username', 'Joueur 1')
            p2_name = getattr(p2, 'username', 'Joueur 2')
            
            p1_text = self.subtitle_font.render(f"{p1_name}: ${p1.money}", True, self.tacos_color)
            p2_text = self.subtitle_font.render(f"{p2_name}: ${p2.money}", True, self.kebab_color)
            vs_text = self.small_font.render("VS", True, (150, 150, 150))
            
            self.screen.blit(p1_text, p1_text.get_rect(center=(self.width // 2 - 100, 195)))
            self.screen.blit(vs_text, vs_text.get_rect(center=(self.width // 2, 195)))
            self.screen.blit(p2_text, p2_text.get_rect(center=(self.width // 2 + 100, 195)))
            
            # Time
            remaining = game_state.get_remaining_time()
            time_text = self.small_font.render(
                f"Temps: {remaining // 60:02d}:{remaining % 60:02d}", True, (180, 180, 180))
            self.screen.blit(time_text, time_text.get_rect(center=(self.width // 2, 235)))
        
        # Players on sides
        player1 = self.menu_images.get("player1")
        player2 = self.menu_images.get("player2")
        if player1:
            self.screen.blit(player1, player1.get_rect(center=(120, self.height // 2)))
        if player2:
            self.screen.blit(player2, player2.get_rect(center=(self.width - 120, self.height // 2)))
        
        # Menu buttons
        button_width = 280
        button_height = 50
        start_y = 320
        
        for i, option in enumerate(self.pause_options):
            rect = pygame.Rect(
                self.width // 2 - button_width // 2,
                start_y + i * 55,
                button_width,
                button_height
            )
            colors = [self.kebab_color, (100, 100, 200), self.tacos_color, (200, 80, 80)]
            self._draw_themed_button(rect, option, i == self.pause_selected, colors[i] if i < len(colors) else self.button_border)
        
        # Hint
        hint = "↑↓ Naviguer  |  ENTRÉE Sélectionner  |  ÉCHAP Reprendre"
        hint_surface = self.hint_font.render(hint, True, (100, 100, 120))
        self.screen.blit(hint_surface, hint_surface.get_rect(center=(self.width // 2, self.height - 30)))
    
    # ==================== INPUT HANDLING ====================
    
    def handle_menu_input(self, event):
        """Handle main menu input"""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_option = (self.selected_option - 1) % len(self.main_menu_options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_option = (self.selected_option + 1) % len(self.main_menu_options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.main_menu_options[self.selected_option] == "JOUER":
                    self.menu_state = self.STATE_PLAYER_SETUP
                    self.setup_focus = 0
                    return None
                return self.main_menu_options[self.selected_option]
            elif event.key == pygame.K_ESCAPE:
                return "QUITTER"
        
        # Support souris
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            button_width = 280
            button_height = 55
            button_spacing = 20
            start_y = 200
            
            for i in range(len(self.main_menu_options)):
                rect = pygame.Rect(
                    self.width // 2 - button_width // 2,
                    start_y + i * (button_height + button_spacing),
                    button_width,
                    button_height
                )
                if rect.collidepoint(mouse_pos):
                    self.selected_option = i
                    break
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                mouse_pos = event.pos
                button_width = 280
                button_height = 55
                button_spacing = 20
                start_y = 200
                
                for i, option in enumerate(self.main_menu_options):
                    rect = pygame.Rect(
                        self.width // 2 - button_width // 2,
                        start_y + i * (button_height + button_spacing),
                        button_width,
                        button_height
                    )
                    if rect.collidepoint(mouse_pos):
                        if option == "JOUER":
                            self.menu_state = self.STATE_PLAYER_SETUP
                            self.setup_focus = 0
                            return None
                        return option
        
        return None
    
    def handle_setup_input(self, event):
        """Handle player setup input. Returns 'START' when ready to play"""
        if self.text_input_active:
            return self._handle_text_input(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.menu_state = self.STATE_MAIN
                return None
            
            # Navigation
            if event.key in (pygame.K_UP, pygame.K_w):
                self._navigate_setup(-2)  # Move up (skip to same field in other column or up)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._navigate_setup(2)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                # Si sur un sélecteur de côté, changer directement le côté
                if self.setup_focus in (1, 3):
                    player_idx = self.setup_focus // 2
                    if self.player_configs[player_idx]["side"] != "left":
                        self._set_side(player_idx, "left")
                else:
                    self._navigate_setup(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                # Si sur un sélecteur de côté, changer directement le côté
                if self.setup_focus in (1, 3):
                    player_idx = self.setup_focus // 2
                    if self.player_configs[player_idx]["side"] != "right":
                        self._set_side(player_idx, "right")
                else:
                    self._navigate_setup(1)
            
            # Selection
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.setup_focus in (0, 2):  # Name fields
                    self.text_input_active = True
                    self.editing_player = self.setup_focus // 2
                elif self.setup_focus in (1, 3):  # Side selectors
                    self._toggle_side(self.setup_focus // 2)
                elif self.setup_focus == 4:  # Start button
                    return "START"
        
        # Support souris
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                return self._handle_setup_mouse_click(event.pos)
        
        return None
    
    def _handle_setup_mouse_click(self, mouse_pos):
        """Gère le clic souris dans le menu de configuration"""
        panel_width = 400
        panel_height = 350
        panel_spacing = 80
        panel_y = 120
        
        # Panel Joueur 1 (gauche)
        p1_x = self.width // 2 - panel_width - panel_spacing // 2
        # Panel Joueur 2 (droite)
        p2_x = self.width // 2 + panel_spacing // 2
        
        for player_idx, panel_x in enumerate([p1_x, p2_x]):
            # Zone du nom
            name_rect = pygame.Rect(panel_x + 30, panel_y + 175, panel_width - 60, 40)
            if name_rect.collidepoint(mouse_pos):
                self.setup_focus = player_idx * 2
                self.text_input_active = True
                self.editing_player = player_idx
                return None
            
            # Zone du sélecteur de côté
            side_rect = pygame.Rect(panel_x + 30, panel_y + 260, panel_width - 60, 45)
            if side_rect.collidepoint(mouse_pos):
                self.setup_focus = player_idx * 2 + 1
                # Déterminer si clic gauche ou droite
                half_width = side_rect.width // 2
                if mouse_pos[0] < side_rect.x + half_width:
                    if self.player_configs[player_idx]["side"] != "left":
                        self._set_side(player_idx, "left")
                else:
                    if self.player_configs[player_idx]["side"] != "right":
                        self._set_side(player_idx, "right")
                return None
        
        # Bouton Commencer
        start_rect = pygame.Rect(self.width // 2 - 150, panel_y + panel_height + 30, 300, 60)
        if start_rect.collidepoint(mouse_pos):
            return "START"
        
        return None
    
    def _set_side(self, player_idx, new_side):
        """Définit le côté d'un joueur et met à jour l'autre joueur"""
        other_idx = 1 - player_idx
        other_side = "right" if new_side == "left" else "left"
        
        self.player_configs[player_idx]["side"] = new_side
        self.player_configs[other_idx]["side"] = other_side
    
    def _navigate_setup(self, direction):
        """Navigate through setup fields"""
        # Fields: 0=P1 name, 1=P1 side, 2=P2 name, 3=P2 side, 4=start
        if direction == -1:  # Left
            if self.setup_focus in (2, 3):
                self.setup_focus -= 2
            elif self.setup_focus == 4:
                self.setup_focus = 1
        elif direction == 1:  # Right
            if self.setup_focus in (0, 1):
                self.setup_focus += 2
            elif self.setup_focus == 4:
                self.setup_focus = 3
        elif direction == -2:  # Up
            if self.setup_focus in (1, 3):
                self.setup_focus -= 1
            elif self.setup_focus == 4:
                self.setup_focus = 1
        elif direction == 2:  # Down
            if self.setup_focus in (0, 2):
                self.setup_focus += 1
            elif self.setup_focus in (1, 3):
                self.setup_focus = 4
    
    def _toggle_side(self, player_idx):
        """Toggle player side and update the other player accordingly"""
        config = self.player_configs[player_idx]
        other_idx = 1 - player_idx
        
        # Swap sides
        if config["side"] == "left":
            config["side"] = "right"
            self.player_configs[other_idx]["side"] = "left"
        else:
            config["side"] = "left"
            self.player_configs[other_idx]["side"] = "right"
    
    def _handle_text_input(self, event):
        """Handle text input for name fields"""
        if event.type == pygame.KEYDOWN:
            player_idx = self.editing_player
            
            if event.key == pygame.K_RETURN:
                self.text_input_active = False
                self.editing_player = None
            elif event.key == pygame.K_ESCAPE:
                self.text_input_active = False
                self.editing_player = None
            elif event.key == pygame.K_BACKSPACE:
                self.player_configs[player_idx]["name"] = self.player_configs[player_idx]["name"][:-1]
            else:
                # Add character if printable and not too long
                if event.unicode.isprintable() and len(self.player_configs[player_idx]["name"]) < 15:
                    self.player_configs[player_idx]["name"] += event.unicode
        
        return None
    
    def handle_pause_input(self, event):
        """Handle pause menu input"""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.pause_selected = (self.pause_selected - 1) % len(self.pause_options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.pause_selected = (self.pause_selected + 1) % len(self.pause_options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.pause_options[self.pause_selected]
            elif event.key == pygame.K_ESCAPE:
                return "REPRENDRE"
        
        # Support souris
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            button_width = 280
            button_height = 50
            start_y = 320
            
            for i in range(len(self.pause_options)):
                rect = pygame.Rect(
                    self.width // 2 - button_width // 2,
                    start_y + i * 55,
                    button_width,
                    button_height
                )
                if rect.collidepoint(mouse_pos):
                    self.pause_selected = i
                    break
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                mouse_pos = event.pos
                button_width = 280
                button_height = 50
                start_y = 320
                
                for i, option in enumerate(self.pause_options):
                    rect = pygame.Rect(
                        self.width // 2 - button_width // 2,
                        start_y + i * 55,
                        button_width,
                        button_height
                    )
                    if rect.collidepoint(mouse_pos):
                        return option
        
        return None
    
    def reset_pause_selection(self):
        """Reset pause menu selection"""
        self.pause_selected = 0
    
    def reset_to_main_menu(self):
        """Reset menu state to main menu"""
        self.menu_state = self.STATE_MAIN
        self.selected_option = 0
        self.setup_focus = 0
        self.text_input_active = False
    
    def get_player_configs(self):
        """Get the player configurations"""
        return self.player_configs
