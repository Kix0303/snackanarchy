"""
Menu Carte : affiche la table des ingrédients et des plats pour chaque joueur.
Chaque joueur voit sa carte sur sa moitié d'écran (ingrédients + plats du restaurant).
"""
import pygame
from collections import Counter
from config import *
from game.inventory import RECIPES
from input.controls import get_key_bindings

# Plats par type de restaurant (noms affichés sur la carte)
TACOS_DISHES = ['Tacos XXL', 'Tacos M', 'Burritos', 'Nachos', 'Tacos S', 'Tacos L']
KEBAB_DISHES = ['Kebab', 'Kebab Wrap', 'Assiettes']

INGREDIENT_TRANSLATIONS = {
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


class CarteMenu:
    """Gestionnaire des menus Carte pour les deux joueurs."""

    def __init__(self, screen):
        self.screen = screen
        self.player_menus = [
            PlayerCarteMenu(screen, 0),
            PlayerCarteMenu(screen, 1),
        ]

    @property
    def visible(self):
        return any(m.visible for m in self.player_menus)

    def is_visible_for(self, player_idx):
        return self.player_menus[player_idx].visible

    def toggle(self, player_idx):
        self.player_menus[player_idx].toggle()

    def close(self, player_idx=None):
        if player_idx is not None:
            self.player_menus[player_idx].close()
        else:
            for m in self.player_menus:
                m.close()

    def handle_input(self, event, game_state):
        for menu in self.player_menus:
            if menu.visible:
                result = menu.handle_input(event, game_state)
                if result:
                    return result
        return None

    def draw(self, game_state):
        for menu in self.player_menus:
            if menu.visible:
                menu.draw(game_state)


class PlayerCarteMenu:
    """Menu Carte pour un joueur : ingrédients + plats (avec quantités), affiché sur sa moitié d'écran."""

    PADDING = 20
    SECTION_PAD = 10
    LINE_HEIGHT_SMALL = 18
    LINE_HEIGHT_NORMAL = 22

    def __init__(self, screen, player_idx):
        self.screen = screen
        self.player_idx = player_idx
        self.visible = False

        self.title_font = pygame.font.SysFont(None, 32)
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 19)

        self.menu_width = 340
        self.menu_height = 500
        half_screen = SCREEN_WIDTH // 2
        if player_idx == 0:
            self.menu_x = (half_screen - self.menu_width) // 2
        else:
            self.menu_x = half_screen + (half_screen - self.menu_width) // 2
        self.menu_y = (SCREEN_HEIGHT - self.menu_height) // 2
        self.content_width = self.menu_width - 2 * self.PADDING

    def toggle(self):
        self.visible = not self.visible

    def close(self):
        self.visible = False

    def _translate_ingredient(self, name):
        return INGREDIENT_TRANSLATIONS.get(name, name.replace('_', ' ').title())

    def _get_dishes_for_restaurant(self, restaurant_type):
        if restaurant_type == 'tacos':
            return TACOS_DISHES
        return KEBAB_DISHES

    def _wrap_text(self, text, font, max_width):
        """Découpe le texte en lignes ne dépassant pas max_width."""
        words = text.split()
        lines = []
        current = ""
        for w in words:
            test = f"{current} {w}".strip() if current else w
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines

    def _get_ingredient_counts_for_dish(self, dish_name):
        """Retourne les ingrédients du plat avec leur quantité (ex: {'galette': 2, 'viande': 1})."""
        ingredients = RECIPES.get(dish_name, {})
        if isinstance(ingredients, dict):
            return Counter(ingredients)
        return Counter(ingredients)  # liste (rétrocompat)

    def handle_input(self, event, game_state):
        if not self.visible:
            return None
        if event.type != pygame.KEYDOWN:
            return None

        kb = get_key_bindings()
        player_key = 'player1' if self.player_idx == 0 else 'player2'
        if event.key in (pygame.K_ESCAPE, kb.get_key(player_key, 'carte')):
            self.close()
            return "close"
        return None

    def draw(self, game_state):
        if not self.visible:
            return

        player = game_state.players[self.player_idx]
        half_screen = SCREEN_WIDTH // 2
        overlay_x = 0 if self.player_idx == 0 else half_screen
        overlay = pygame.Surface((half_screen, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (overlay_x, 0))

        accent = ORANGE if self.player_idx == 0 else GREEN
        menu_rect = pygame.Rect(self.menu_x, self.menu_y, self.menu_width, self.menu_height)

        # Fond principal + bandeau titre
        pygame.draw.rect(self.screen, (22, 22, 32), menu_rect, border_radius=14)
        pygame.draw.rect(self.screen, accent, menu_rect, 3, border_radius=14)
        header_rect = pygame.Rect(self.menu_x + 2, self.menu_y + 2, self.menu_width - 4, 42)
        pygame.draw.rect(self.screen, (38, 38, 52), header_rect, border_radius=10)

        # Titre
        title = self.title_font.render(f"Carte - {player.username}", True, accent)
        title_x = self.menu_x + (self.menu_width - title.get_width()) // 2
        self.screen.blit(title, (title_x, self.menu_y + 10))

        content_top = self.menu_y + 52
        content_bottom = self.menu_y + self.menu_height - 36
        clip_rect = pygame.Rect(self.menu_x, content_top, self.menu_width, content_bottom - content_top)
        self.screen.set_clip(clip_rect)

        y = content_top
        inner_left = self.menu_x + self.PADDING
        max_txt = self.content_width

        # ---- Section Ingrédients (encadrée) ----
        sect_h = 26
        sect_rect = pygame.Rect(self.menu_x + self.PADDING // 2, y, self.menu_width - self.PADDING, sect_h)
        pygame.draw.rect(self.screen, (35, 35, 48), sect_rect, border_radius=8)
        pygame.draw.rect(self.screen, (60, 60, 75), sect_rect, 1, border_radius=8)
        sect = self.font.render("Ingrédients", True, accent)
        self.screen.blit(sect, (inner_left, y + 4))
        y += sect_h + self.SECTION_PAD

        for name, data in player.food_stock.ingredients.items():
            if y > self.menu_y + self.menu_height - 180:
                break
            display_name = self._translate_ingredient(name)
            txt = f"  {display_name}: {data['quantity']}/{data['max']}"
            surf = self.small_font.render(txt, True, WHITE)
            if surf.get_width() > max_txt:
                surf = pygame.transform.scale(surf, (max_txt, surf.get_height()))
            self.screen.blit(surf, (inner_left, y))
            y += self.LINE_HEIGHT_SMALL

        y += self.SECTION_PAD

        # ---- Section Plats (encadrée) ----
        sect2_rect = pygame.Rect(self.menu_x + self.PADDING // 2, y, self.menu_width - self.PADDING, sect_h)
        pygame.draw.rect(self.screen, (35, 35, 48), sect2_rect, border_radius=8)
        pygame.draw.rect(self.screen, (60, 60, 75), sect2_rect, 1, border_radius=8)
        sect2 = self.font.render("Plats (ingrédients consommés)", True, accent)
        self.screen.blit(sect2, (inner_left, y + 4))
        y += sect_h + self.SECTION_PAD

        dishes = self._get_dishes_for_restaurant(player.food_stock.restaurant_type)
        for dish_name in dishes:
            if y > self.menu_y + self.menu_height - 50:
                break
            counts = self._get_ingredient_counts_for_dish(dish_name)
            parts = [f"{self._translate_ingredient(ing)} x{n}" for ing, n in sorted(counts.items())]
            ing_line = ", ".join(parts)

            name_surf = self.small_font.render(f"• {dish_name}", True, WHITE)
            if name_surf.get_width() > max_txt:
                name_surf = pygame.transform.scale(name_surf, (max_txt, name_surf.get_height()))
            self.screen.blit(name_surf, (inner_left, y))
            y += self.LINE_HEIGHT_SMALL

            indent_w = self.small_font.size("    ")[0]
            for wrapped in self._wrap_text(ing_line, self.small_font, max_txt - indent_w):
                sub = self.small_font.render(f"    {wrapped}", True, (160, 160, 170))
                if sub.get_width() > max_txt:
                    sub = pygame.transform.scale(sub, (max_txt, sub.get_height()))
                self.screen.blit(sub, (inner_left, y))
                y += self.LINE_HEIGHT_SMALL
            y += 4

        self.screen.set_clip(None)

        # Pied : instruction fermeture
        foot_rect = pygame.Rect(self.menu_x, self.menu_y + self.menu_height - 32, self.menu_width, 32)
        pygame.draw.rect(self.screen, (30, 30, 42), foot_rect, border_radius=0)
        pygame.draw.line(self.screen, (60, 60, 75), (self.menu_x, self.menu_y + self.menu_height - 32), (self.menu_x + self.menu_width, self.menu_y + self.menu_height - 32), 1)
        kb = get_key_bindings()
        player_key = 'player1' if self.player_idx == 0 else 'player2'
        key_name = kb.get_key_name(kb.get_key(player_key, 'carte'))
        hint = self.small_font.render(f"{key_name} ou ECHAP pour fermer", True, GRAY)
        hx = self.menu_x + (self.menu_width - hint.get_width()) // 2
        self.screen.blit(hint, (hx, self.menu_y + self.menu_height - 26))
