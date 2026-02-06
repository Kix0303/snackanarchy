"""
Affichage des missions en jeu - HUD pour montrer la progression des missions
"""
import pygame
import math
import time
from config import *


class MissionDisplay:
    """Affiche les missions actives et leur progression pendant le jeu"""
    
    def __init__(self):
        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 14, bold=True)
        self.normal_font = pygame.font.SysFont("Arial", 12)
        self.small_font = pygame.font.SysFont("Arial", 10)
        self.icon_font = pygame.font.SysFont("Arial", 16)
        
        # Colors
        self.bg_color = (30, 30, 40, 180)
        self.border_color = (80, 80, 100)
        self.progress_bg = (50, 50, 60)
        self.progress_fill = (255, 140, 0)
        self.complete_color = (76, 175, 80)
        self.text_color = (200, 200, 200)
        
        # Animation
        self.completion_animations = {}  # mission_id -> animation_start_time
        
        # Mode compact (réduit pour ne pas cacher la carte)
        self.compact_mode = True
    
    def _draw_mission_icon(self, surface, icon_type, x, y, size, color):
        """Dessine une icône pour les missions"""
        cx, cy = x + size // 2, y + size // 2
        
        if icon_type == "tacos":
            # Demi-cercle pour tacos
            pygame.draw.arc(surface, color, (x + 2, y + 2, size - 4, size - 4), 0, 3.14, 2)
            pygame.draw.line(surface, color, (x + 2, cy), (x + size - 2, cy), 2)
        elif icon_type == "kebab":
            # Broche verticale
            pygame.draw.line(surface, color, (cx, y + 2), (cx, y + size - 2), 2)
            for i in range(3):
                pygame.draw.ellipse(surface, color, (x + 4, y + 3 + i * 5, size - 8, 4), 1)
        elif icon_type == "clients":
            # Deux silhouettes
            for offset in [-4, 4]:
                pygame.draw.circle(surface, color, (cx + offset, y + 5), 3)
                pygame.draw.line(surface, color, (cx + offset, y + 8), (cx + offset, y + size - 2), 2)
        elif icon_type == "money":
            # Symbole euro
            pygame.draw.circle(surface, color, (cx, cy), size // 2 - 2, 1)
            small_font = pygame.font.SysFont("Arial", 12, bold=True)
            dollar = small_font.render("€", True, color)
            surface.blit(dollar, dollar.get_rect(center=(cx, cy)))
        elif icon_type == "star":
            # Étoile simple
            points = []
            for i in range(5):
                angle = math.radians(-90 + i * 72)
                points.append((cx + int((size // 2 - 2) * math.cos(angle)), 
                              cy + int((size // 2 - 2) * math.sin(angle))))
                angle = math.radians(-90 + i * 72 + 36)
                points.append((cx + int((size // 4) * math.cos(angle)), 
                              cy + int((size // 4) * math.sin(angle))))
            pygame.draw.polygon(surface, color, points)
        elif icon_type == "sabotage":
            # Tête de diable (cornes)
            pygame.draw.circle(surface, color, (cx, cy + 2), size // 3, 1)
            pygame.draw.line(surface, color, (cx - 5, cy - 2), (cx - 7, y + 2), 2)
            pygame.draw.line(surface, color, (cx + 5, cy - 2), (cx + 7, y + 2), 2)
        elif icon_type == "clean":
            # Balai
            pygame.draw.line(surface, color, (cx, y + 2), (cx, y + size - 6), 2)
            pygame.draw.line(surface, color, (x + 4, y + size - 4), (x + size - 4, y + size - 4), 2)
            pygame.draw.line(surface, color, (x + 4, y + size - 4), (cx, y + size - 8), 1)
            pygame.draw.line(surface, color, (x + size - 4, y + size - 4), (cx, y + size - 8), 1)
        elif icon_type == "attack":
            # Épée croisée
            pygame.draw.line(surface, color, (x + 3, y + 3), (x + size - 3, y + size - 3), 2)
            pygame.draw.line(surface, color, (x + size - 3, y + 3), (x + 3, y + size - 3), 2)
        elif icon_type == "streak":
            # Flamme
            pygame.draw.polygon(surface, color, [
                (cx, y + 2),
                (x + size - 4, cy + 4),
                (cx + 2, y + size - 2),
                (cx - 2, cy + 2),
                (x + 4, cy + 4)
            ])
        elif icon_type == "trophy":
            # Coupe/trophée
            pygame.draw.arc(surface, color, (x + 3, y + 3, size - 6, size - 8), 0, 3.14, 2)
            pygame.draw.line(surface, color, (cx, cy + 2), (cx, y + size - 4), 2)
            pygame.draw.line(surface, color, (x + 5, y + size - 3), (x + size - 5, y + size - 3), 2)
        else:
            # Icône par défaut: cercle avec point
            pygame.draw.circle(surface, color, (cx, cy), size // 2 - 2, 1)
            pygame.draw.circle(surface, color, (cx, cy), 2, 0)
    
    def draw(self, surface, player, x, y, width=220):
        """Dessine les missions d'un joueur en mode compact
        
        Args:
            surface: Surface pygame sur laquelle dessiner
            player: Le joueur dont on affiche les missions
            x, y: Position du coin supérieur gauche
            width: Largeur du panneau
        """
        if not hasattr(player, 'mission_manager'):
            return
        
        missions = player.mission_manager.get_active_missions()
        if not missions:
            return
        
        if self.compact_mode:
            self._draw_compact(surface, player, missions, x, y, width)
        else:
            self._draw_full(surface, player, missions, x, y, width)
    
    def _draw_compact(self, surface, player, missions, x, y, width):
        """Mode compact: barre horizontale avec texte entier, badges élargis"""
        # Affichage sous forme de badges horizontaux (largeur augmentée pour noms complets)
        padding = 4
        max_missions = min(3, len(missions))
        badge_width = (width - (max_missions - 1) * padding) // max_missions if max_missions else width
        badge_height = 45
        
        # Position en haut à droite de chaque écran (sous le HUD)
        start_y = y
        
        # Nombre de missions en attente de réclamation
        unclaimed = player.mission_manager.get_unclaimed_count()
        
        current_time = time.time()
        
        for i, mission in enumerate(missions[:max_missions]):
            badge_x = x + i * (badge_width + padding)
            self._draw_mission_badge(surface, mission, badge_x, start_y, 
                                    badge_width, badge_height, current_time)
        
        # Indicateur si plus de missions
        if len(missions) > max_missions:
            more_x = x + max_missions * (badge_width + padding)
            more_surface = pygame.Surface((25, badge_height), pygame.SRCALPHA)
            pygame.draw.rect(more_surface, (50, 50, 60, 180), (0, 0, 25, badge_height), border_radius=4)
            more_text = self.small_font.render(f"+{len(missions) - max_missions}", True, (150, 150, 150))
            more_surface.blit(more_text, (5, badge_height // 2 - 5))
            surface.blit(more_surface, (more_x, start_y))
            
    def _draw_mission_badge(self, surface, mission, x, y, width, height, current_time):
        """Dessine un badge compact pour une mission (sans fond noir)"""
        # Animation de completion
        is_animating = False
        if mission.completed and mission.id in self.completion_animations:
            anim_start = self.completion_animations[mission.id]
            elapsed = current_time - anim_start
            if elapsed < 1.0:
                is_animating = True
            else:
                del self.completion_animations[mission.id]
        elif mission.completed and mission.id not in self.completion_animations:
            self.completion_animations[mission.id] = current_time
            is_animating = True
        
        # Couleur de bordure selon l'état
        if mission.completed:
            if is_animating:
                pulse = (math.sin(current_time * 10) + 1) / 2
                border_color = (int(76 + 50 * pulse), int(175 + 50 * pulse), int(80 + 50 * pulse))
            else:
                border_color = self.complete_color
            icon_color = self.complete_color
        else:
            border_color = (100, 100, 120)
            icon_color = WHITE
        
        # Dessiner directement sur la surface (pas de fond noir)
        # Bordure fine arrondie
        badge_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, border_color, badge_rect, 2, border_radius=5)
        
        # Icône de la mission (petit)
        icon_size = 14
        self._draw_mission_icon(surface, mission.icon, x + 4, y + 4, icon_size, icon_color)
        
        # Nom complet (tronqué seulement si trop long pour la largeur du badge)
        name_display = mission.name
        text_max_width = width - 24  # place pour icône + marge
        name_text = self.small_font.render(name_display, True, (0, 0, 0))
        if name_text.get_width() > text_max_width:
            while name_display and self.small_font.render(name_display + "..", True, (0, 0, 0)).get_width() > text_max_width:
                name_display = name_display[:-1]
            name_display = name_display + ".." if len(name_display) < len(mission.name) else name_display
        # Ombre
        shadow_text = self.small_font.render(name_display, True, (0, 0, 0))
        surface.blit(shadow_text, (x + 22, y + 21))
        # Texte
        name_color = self.complete_color if mission.completed else (220, 220, 220)
        name_text = self.small_font.render(name_display, True, name_color)
        surface.blit(name_text, (x + 21, y + 20))
        
        # Barre de progression mini
        bar_width = width - 8
        bar_height = 5
        bar_y = y + height - bar_height - 3
        
        # Fond de barre semi-transparent
        bar_bg = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
        bar_bg.fill((50, 50, 60, 150))
        surface.blit(bar_bg, (x + 4, bar_y))
        
        progress_ratio = min(1.0, mission.progress / mission.target)
        fill_width = int(bar_width * progress_ratio)
        if fill_width > 0:
            fill_color = self.complete_color if mission.completed else self.progress_fill
            pygame.draw.rect(surface, fill_color, (x + 4, bar_y, fill_width, bar_height), border_radius=2)
    
    def _draw_full(self, surface, player, missions, x, y, width):
        """Mode complet: panneau détaillé (ancien mode)"""
        mission_height = 50
        header_height = 22
        padding = 6
        total_height = header_height + len(missions) * mission_height + padding * 2
        
        # Fond du panneau
        panel_surface = pygame.Surface((width, total_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, self.bg_color, 
                        (0, 0, width, total_height), border_radius=8)
        pygame.draw.rect(panel_surface, self.border_color, 
                        (0, 0, width, total_height), 2, border_radius=8)
        
        # Titre
        title = self.title_font.render("MISSIONS", True, (255, 140, 0))
        panel_surface.blit(title, (padding, padding))
        
        # Nombre de missions complétées non réclamées
        unclaimed = player.mission_manager.get_unclaimed_count()
        if unclaimed > 0:
            notif_text = self.small_font.render(f"({unclaimed}!)", True, self.complete_color)
            panel_surface.blit(notif_text, (width - 35, padding + 2))
        
        # Ligne séparatrice
        pygame.draw.line(panel_surface, self.border_color,
                        (padding, header_height + padding - 2),
                        (width - padding, header_height + padding - 2), 1)
        
        # Missions
        current_y = header_height + padding
        current_time = time.time()
        
        for mission in missions:
            self._draw_mission(panel_surface, mission, padding, current_y, 
                             width - padding * 2, mission_height - 4, current_time)
            current_y += mission_height
        
        surface.blit(panel_surface, (x, y))
    
    def _draw_mission(self, surface, mission, x, y, width, height, current_time):
        """Dessine une mission individuelle"""
        # Animation de completion
        is_animating = False
        anim_progress = 0
        if mission.completed and mission.id in self.completion_animations:
            anim_start = self.completion_animations[mission.id]
            elapsed = current_time - anim_start
            if elapsed < 1.0:
                is_animating = True
                anim_progress = elapsed
            else:
                # Animation terminée
                del self.completion_animations[mission.id]
        elif mission.completed and mission.id not in self.completion_animations:
            # Démarrer l'animation
            self.completion_animations[mission.id] = current_time
            is_animating = True
            anim_progress = 0
        
        # Couleur de fond selon l'état
        if mission.completed:
            if is_animating:
                pulse = (math.sin(anim_progress * 10) + 1) / 2
                bg_color = (
                    int(40 + 30 * pulse),
                    int(60 + 40 * pulse),
                    int(40 + 30 * pulse),
                    220
                )
            else:
                bg_color = (40, 60, 40, 220)
        else:
            bg_color = (40, 40, 50, 200)
        
        # Rectangle de la mission
        mission_rect = pygame.Rect(x, y, width, height)
        mission_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(mission_surface, bg_color, (0, 0, width, height), border_radius=5)
        
        border_color = self.complete_color if mission.completed else self.border_color
        pygame.draw.rect(mission_surface, border_color, (0, 0, width, height), 1, border_radius=5)
        
        # Icône dessinée
        self._draw_mission_icon(mission_surface, mission.icon, 6, 8, 20, WHITE)
        
        # Nom de la mission
        name_color = self.complete_color if mission.completed else (220, 220, 220)
        name_text = self.title_font.render(mission.name, True, name_color)
        mission_surface.blit(name_text, (35, 5))
        
        # Barre de progression
        progress_width = width - 95
        progress_height = 12
        progress_x = 35
        progress_y = 28
        
        # Fond de la barre
        pygame.draw.rect(mission_surface, self.progress_bg,
                        (progress_x, progress_y, progress_width, progress_height),
                        border_radius=3)
        
        # Remplissage
        fill_width = int((mission.progress / mission.target) * progress_width)
        if fill_width > 0:
            fill_color = self.complete_color if mission.completed else self.progress_fill
            pygame.draw.rect(mission_surface, fill_color,
                            (progress_x, progress_y, fill_width, progress_height),
                            border_radius=3)
        
        # Texte de progression
        progress_text = self.small_font.render(mission.get_progress_text(), True, WHITE)
        mission_surface.blit(progress_text, (width - 45, progress_y - 2))
        
        # Récompense
        if not mission.claimed:
            reward_text = self.small_font.render(
                f"+{mission.reward_money}e" + (f" +{mission.reward_reputation}%" if mission.reward_reputation > 0 else ""),
                True, (255, 215, 0) if mission.completed else (150, 150, 150)
            )
            mission_surface.blit(reward_text, (width - 75, 5))
        else:
            # Checkmark dessiné au lieu de ✓
            pygame.draw.lines(mission_surface, self.complete_color, False, [
                (width - 75, 12),
                (width - 70, 17),
                (width - 62, 7)
            ], 2)
            claimed_text = self.small_font.render("OK", True, self.complete_color)
            mission_surface.blit(claimed_text, (width - 58, 5))
        
        surface.blit(mission_surface, (x, y))
    
    def trigger_completion_animation(self, mission_id):
        """Déclenche l'animation de complétion pour une mission"""
        self.completion_animations[mission_id] = time.time()


class MissionNotification:
    """Affiche des notifications temporaires pour les événements de mission"""
    
    def __init__(self):
        self.notifications = []  # [(text, color, start_time, x, y)]
        self.duration = 2.0
        self.title_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.normal_font = pygame.font.SysFont("Arial", 16)
    
    def add_notification(self, text, color, x, y):
        """Ajoute une notification"""
        self.notifications.append({
            'text': text,
            'color': color,
            'start_time': time.time(),
            'x': x,
            'y': y
        })
    
    def add_mission_complete(self, mission, x, y):
        """Ajoute une notification de mission completee"""
        text = f"Mission: {mission.name} OK!"
        self.add_notification(text, (76, 175, 80), x, y)
    
    def add_reward_claimed(self, money, reputation, x, y):
        """Ajoute une notification de récompense réclamée"""
        text = f"+{money}€"
        if reputation > 0:
            text += f" +{reputation}%"
        self.add_notification(text, (255, 215, 0), x, y)
    
    def update(self):
        """Met à jour les notifications (supprime les expirées)"""
        current_time = time.time()
        self.notifications = [
            n for n in self.notifications 
            if current_time - n['start_time'] < self.duration
        ]
    
    def draw(self, surface):
        """Dessine toutes les notifications actives"""
        current_time = time.time()
        
        for notif in self.notifications:
            elapsed = current_time - notif['start_time']
            
            # Animation de fondu et mouvement vers le haut
            alpha = int(255 * (1 - elapsed / self.duration))
            y_offset = int(elapsed * 30)  # Monte de 30 pixels par seconde
            
            # Texte
            text_surface = self.title_font.render(notif['text'], True, notif['color'])
            text_surface.set_alpha(alpha)
            
            # Position avec animation
            x = notif['x'] - text_surface.get_width() // 2
            y = notif['y'] - y_offset
            
            # Ombre
            shadow_surface = self.title_font.render(notif['text'], True, (0, 0, 0))
            shadow_surface.set_alpha(alpha // 2)
            surface.blit(shadow_surface, (x + 2, y + 2))
            
            surface.blit(text_surface, (x, y))
