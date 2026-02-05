"""
Cinématique d'intro / lore avant le début de la partie.
Personnages qui s'interpellent avec dialogues et animations.
Utilise les assets du jeu (rue, trottoir, façades, sprites).
"""
import pygame
import time
import math
from config import *
from game.assets_loader import Assets
from game.audio import play_sound


class IntroCutscene:
    """Scène d'intro avec personnages, dialogues et animations."""

    def __init__(self, screen, player_configs=None):
        self.screen = screen
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.player_configs = player_configs or [
            {"name": "Joueur 1", "side": "left", "restaurant": "tacos"},
            {"name": "Joueur 2", "side": "right", "restaurant": "kebab"},
        ]
        self.name_tacos = next(
            (c["name"] for c in self.player_configs if c.get("restaurant") == "tacos"),
            "Le vendeur Tacos",
        )
        self.name_kebab = next(
            (c["name"] for c in self.player_configs if c.get("restaurant") == "kebab"),
            "Le vendeur Kebab",
        )

        # Polices
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.dialogue_font = pygame.font.SysFont("Arial", 26)
        self.name_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.hint_font = pygame.font.SysFont("Arial", 20)

        # Assets : façades, rue, trottoir
        assets = Assets.get()
        self.facade_tacos = assets.get_image("facade_tacos")
        self.facade_kebab = assets.get_image("facade_kebab")
        self.tile_street = assets.get_image("road")
        self.tile_sidewalk = assets.get_image("sidewalk")
        self._scale_facades_for_intro()
        self._build_street_surface()
        if not hasattr(self, 'street_y') or self.street_surface is None:
            self.street_y = int(self.height * 0.38)

        # Sprites des personnages (taille jeu = TILE_SIZE*1.8) ; orientation pour qu'ils se font face
        self.img_tacos = assets.get_image("player1") or self._fallback_sprite(PLAYER_1_COLOR)   # regarde à droite
        self.img_kebab = assets.get_image("player2_left") or assets.get_image("player2") or self._fallback_sprite(PLAYER_2_COLOR)  # regarde à gauche
        self.char_w = self.img_tacos.get_width() if self.img_tacos else 64
        self.char_h = self.img_tacos.get_height() if self.img_tacos else 64

        # Positions cibles des personnages (centrées sur leur zone)
        self._target_tacos_x = self.width * 0.28 - self.char_w // 2
        self._target_kebab_x = self.width * 0.72 - self.char_w // 2
        self._base_char_y = int(self.height * 0.58)

        # Scénario : liste de répliques / moments
        self.beats = [
            {
                "duration": 3.5,
                "speaker": "narrator",
                "text": "Sur une rue animée, deux enseignes se font face...",
                "fade": 1.0,
            },
            {
                "duration": 4.0,
                "speaker": "tacos",
                "name": self.name_tacos,
                "text": "Ma sauce secrète va encore écraser ton kebab aujourd'hui !",
                "bob_tacos": True,
            },
            {
                "duration": 4.0,
                "speaker": "kebab",
                "name": self.name_kebab,
                "text": "Rêve ! Les clients font la queue chez moi, pas devant tes tacos !",
                "bob_kebab": True,
            },
            {
                "duration": 3.5,
                "speaker": "narrator",
                "text": "La guerre des snacks est sur le point de commencer...",
            },
            {
                "duration": 2.5,
                "speaker": "narrator",
                "text": "Servir. Saboter. Gagner.",
                "title_style": True,
            },
        ]

        self.current_beat = 0
        self.beat_start_time = time.time()
        self.finished = False
        self.skipped = False
        self.global_start = time.time()

        # Animation d'entrée des personnages (slide)
        self.slide_duration = 0.8
        self.dialogue_char_index = 0
        self.dialogue_last_update = 0
        self.typewriter_delay = 0.03
        self.overlay_alpha = 0  # fade in from black
        self.max_overlay_alpha = 200  # fond semi-transparent pour texte
        self.bob_offset = 0.0
        self.bob_speed = 5.0
        self.bob_amplitude = 6
        self.shake_amplitude = 0
        self.shake_decay = 8
        self.title_scale = 0.0
        self.title_scale_speed = 2.5

    def _scale_facades_for_intro(self):
        """Redimensionne les façades pour l'écran d'intro."""
        target_h = int(self.height * 0.32)
        for name, img in [("facade_tacos", self.facade_tacos), ("facade_kebab", self.facade_kebab)]:
            if img is None:
                continue
            w, h = img.get_size()
            scale = target_h / h
            new_w = int(w * scale)
            new_h = int(h * scale)
            if name == "facade_tacos":
                self.facade_tacos = pygame.transform.smoothscale(img, (new_w, new_h))
            else:
                self.facade_kebab = pygame.transform.smoothscale(img, (new_w, new_h))

    def _build_street_surface(self):
        """Construit une surface de rue + trottoir en tuiles pour le fond."""
        if self.tile_street is None and self.tile_sidewalk is None:
            self.street_surface = None
            return
        tw = TILE_SIZE
        th = TILE_SIZE
        # Bande trottoir en haut (2 lignes), puis rue
        street_y_start = int(self.height * 0.38)
        self.street_surface = pygame.Surface((self.width, self.height))
        self.street_surface.fill((30, 30, 35))
        # Ciel dégradé
        for i in range(0, street_y_start + 1, 2):
            r = int(25 + (i / street_y_start) * 10)
            g = int(20 + (i / street_y_start) * 12)
            b = int(45 + (i / street_y_start) * 15)
            pygame.draw.line(self.street_surface, (r, g, b), (0, i), (self.width, i), 3)
        # Trottoir (2 lignes de tuiles)
        if self.tile_sidewalk:
            for ty in range(2):
                for tx in range(0, self.width + tw, tw):
                    self.street_surface.blit(self.tile_sidewalk, (tx, street_y_start + ty * th))
        # Rue (tuiles jusqu'en bas)
        if self.tile_street:
            for ty in range(2, (self.height - street_y_start) // th + 2):
                for tx in range(0, self.width + tw, tw):
                    self.street_surface.blit(self.tile_street, (tx, street_y_start + ty * th))
        self.street_y = street_y_start

    def _fallback_sprite(self, color):
        s = pygame.Surface((128, 128), pygame.SRCALPHA)
        pygame.draw.rect(s, color, (16, 16, 96, 96), border_radius=12)
        pygame.draw.circle(s, (255, 255, 255), (64, 50), 18)
        return s

    def handle_input(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    play_sound('menu_select', 'ui')
                    self.skipped = True
                    self.finished = True
                    return True
            if e.type == pygame.MOUSEBUTTONDOWN:
                play_sound('menu_select', 'ui')
                self.skipped = True
                self.finished = True
                return True
        return False

    def update(self, dt=1/60):
        if self.finished:
            return True

        t = time.time() - self.global_start
        self.bob_offset = math.sin(t * self.bob_speed) * self.bob_amplitude
        if self.shake_amplitude > 0:
            self.shake_amplitude = max(0, self.shake_amplitude - self.shake_decay * dt)

        beat = self.beats[self.current_beat]
        beat_elapsed = time.time() - self.beat_start_time

        # Typewriter pour le dialogue
        if beat.get("speaker") in ("tacos", "kebab") and beat.get("text"):
            full_len = len(beat["text"])
            if self.dialogue_last_update > 0 and (time.time() - self.dialogue_last_update) >= self.typewriter_delay:
                self.dialogue_char_index = min(full_len, self.dialogue_char_index + 1)
                self.dialogue_last_update = time.time()
            elif self.dialogue_last_update == 0:
                self.dialogue_last_update = time.time()

        # Animation "title_style" (texte qui grossit)
        if beat.get("title_style"):
            self.title_scale = min(1.0, self.title_scale + self.title_scale_speed * dt)

        # Passer au beat suivant
        if beat_elapsed >= beat["duration"]:
            self.current_beat += 1
            self.dialogue_char_index = 0
            self.dialogue_last_update = 0
            if not beat.get("title_style"):
                self.title_scale = 0.0
            if self.current_beat >= len(self.beats):
                self.finished = True
                return True
            play_sound('menu_move', 'ui')
            self.beat_start_time = time.time()

        return False

    def draw(self):
        if self.finished:
            return

        beat = self.beats[self.current_beat]
        beat_elapsed = time.time() - self.beat_start_time

        # Fond (assets : rue + façades)
        self._draw_background()

        # Personnages : slide d'entrée uniquement au premier beat
        if self.current_beat == 0 and beat_elapsed < self.slide_duration:
            tacos_x = self._ease_slide(beat_elapsed, self.slide_duration, -self.char_w - 80, self._target_tacos_x)
            kebab_x = self._ease_slide(beat_elapsed, self.slide_duration, self.width + 80, self._target_kebab_x)
        else:
            tacos_x = self._target_tacos_x
            kebab_x = self._target_kebab_x

        tacos_y = self._base_char_y + (self.bob_offset if beat.get("bob_tacos") else 0)
        kebab_y = self._base_char_y + (self.bob_offset if beat.get("bob_kebab") else 0)

        shake_x = (math.sin(time.time() * 40) * self.shake_amplitude) if self.shake_amplitude else 0

        if self.img_tacos:
            self.screen.blit(self.img_tacos, (int(tacos_x + shake_x), int(tacos_y)))
        if self.img_kebab:
            self.screen.blit(self.img_kebab, (int(kebab_x - shake_x), int(kebab_y)))

        # Dialogue ou narration
        if beat.get("speaker") == "narrator":
            self._draw_narration(beat, beat_elapsed)
        elif beat.get("speaker") in ("tacos", "kebab"):
            self._draw_dialogue_box(beat)

        # Titre style (dernier beat)
        if beat.get("title_style") and beat.get("text"):
            self._draw_title_text(beat["text"])

        # Indication skip
        self._draw_skip_hint()

    def _ease_slide(self, elapsed, duration, from_pos, to_pos):
        if duration <= 0:
            return to_pos
        t = min(1.0, elapsed / duration)
        t = t * t * (3 - 2 * t)  # smoothstep
        return from_pos + (to_pos - from_pos) * t

    def _draw_background(self):
        # Fond : surface pré-construite (ciel + trottoir + rue en tuiles) ou dégradé de secours
        if self.street_surface:
            self.screen.blit(self.street_surface, (0, 0))
        else:
            for i in range(0, self.height + 1, 4):
                r = int(25 + (i / self.height) * 10)
                g = int(20 + (i / self.height) * 12)
                b = int(45 + (i / self.height) * 15)
                pygame.draw.line(self.screen, (r, g, b), (0, i), (self.width, i), 5)
            street_y = int(self.height * 0.4)
            pygame.draw.rect(self.screen, (40, 42, 48), (0, street_y, self.width, self.height - street_y))

        # Façades des deux restos (assets du jeu)
        if self.facade_tacos:
            ft_w, ft_h = self.facade_tacos.get_size()
            self.screen.blit(self.facade_tacos, (self.width * 0.02, self.street_y - ft_h if self.street_surface else 80))
        if self.facade_kebab:
            fk_w, fk_h = self.facade_kebab.get_size()
            self.screen.blit(self.facade_kebab, (self.width - self.width * 0.02 - fk_w, self.street_y - fk_h if self.street_surface else 80))

        # Légère vignette (bords assombris) pour effet cinématique
        self._draw_vignette()

    def _draw_vignette(self):
        """Bords légèrement assombris pour un rendu cinématique."""
        margin = int(min(self.width, self.height) * 0.08)
        v = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        v.fill((0, 0, 0, 0))
        for side, (x, y, w, h) in [
            (0, (0, 0, margin, self.height)),
            (1, (self.width - margin, 0, margin, self.height)),
            (2, (0, 0, self.width, margin)),
            (3, (0, self.height - margin, self.width, margin)),
        ]:
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill((0, 0, 0, 45))
            v.blit(s, (x, y))
        self.screen.blit(v, (0, 0))

    def _draw_narration(self, beat, beat_elapsed):
        text = beat.get("text", "")
        if not text:
            return
        alpha = min(255, int(255 * (beat_elapsed / 0.5)))
        surf = self.dialogue_font.render(text, True, (255, 255, 255))
        pad = 28
        box_w = surf.get_width() + pad * 2
        box_h = surf.get_height() + pad * 2
        box_x = self.width // 2 - box_w // 2
        box_y = int(self.height * 0.78)
        box = pygame.Rect(box_x, box_y, box_w, box_h)

        # Ombre
        shadow = box.inflate(6, 6)
        shadow.x += 4
        shadow.y += 4
        shadow_surf = pygame.Surface((shadow.w, shadow.h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 90))
        self.screen.blit(shadow_surf, shadow.topleft)

        # Fond opaque (lisibilité)
        bg = pygame.Surface((box.w, box.h))
        bg.fill((28, 30, 42))
        bg.set_alpha(alpha)
        self.screen.blit(bg, box.topleft)
        pygame.draw.rect(self.screen, (255, 180, 80), box, 2, border_radius=8)
        pygame.draw.rect(self.screen, (80, 85, 110), box, 1, border_radius=8)

        # Texte centré
        text_rect = surf.get_rect(center=(self.width // 2, box_y + box_h // 2))
        surf.set_alpha(alpha)
        self.screen.blit(surf, text_rect)

    def _draw_dialogue_box(self, beat):
        name = beat.get("name", "???")
        full_text = beat.get("text", "")
        display_text = full_text[: self.dialogue_char_index]
        if not display_text:
            return

        line_w = int(self.width * 0.58)
        pad_side = 32
        pad_vert = 20
        line_height = 30

        # Découpage en lignes
        words = display_text.split()
        lines = []
        current = ""
        for w in words:
            test = current + (" " if current else "") + w
            if self.dialogue_font.size(test)[0] <= line_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)

        # Dimensions de la boîte (nom au-dessus + texte)
        name_surf = self.name_font.render(name, True, (255, 255, 255))
        name_h = name_surf.get_height()
        box_content_h = name_h + 8 + len(lines) * line_height
        box_w = line_w + pad_side * 2
        box_h = box_content_h + pad_vert * 2
        box_x = self.width // 2 - box_w // 2
        box_y = int(self.height * 0.72)
        box = pygame.Rect(box_x, box_y, box_w, box_h)

        # 1) Ombre portée (décalée)
        shadow = box.inflate(8, 8)
        shadow.x += 5
        shadow.y += 5
        shadow_surf = pygame.Surface((shadow.w, shadow.h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        self.screen.blit(shadow_surf, shadow.topleft)

        # 2) Fond de la boîte (opaque pour bonne lisibilité)
        bg_surf = pygame.Surface((box.w, box.h))
        bg_surf.fill((28, 30, 42))
        # Bordure intérieure claire
        pygame.draw.rect(bg_surf, (60, 65, 85), (0, 0, box.w, box.h), 1)
        self.screen.blit(bg_surf, box.topleft)

        # 3) Bandeau du nom (couleur accent)
        name_band = pygame.Rect(box.x, box.y, box.w, name_h + 14)
        band_surf = pygame.Surface((name_band.w, name_band.h))
        band_surf.fill((255, 140, 0))  # MENU_ACCENT / orange Tacos
        if beat.get("speaker") == "kebab":
            band_surf.fill((76, 175, 80))  # vert Kebab
        self.screen.blit(band_surf, name_band.topleft)
        pygame.draw.line(self.screen, (255, 255, 255), (name_band.left, name_band.bottom - 1), (name_band.right, name_band.bottom - 1), 2)

        # 4) Nom
        name_rect = name_surf.get_rect(midleft=(box.x + 20, box.y + (name_h + 14) // 2))
        # Contour noir pour lisible sur bandeau coloré
        name_outline = self.name_font.render(name, True, (0, 0, 0))
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1),(0,-1),(0,1),(-1,0),(1,0)]:
            self.screen.blit(name_outline, (name_rect.x + dx, name_rect.y + dy))
        self.screen.blit(name_surf, name_rect)

        # 5) Texte du dialogue (blanc, bien lisible)
        y_start = box.y + name_h + 14 + 12
        x_start = box.x + pad_side
        for i, line in enumerate(lines):
            line_surf = self.dialogue_font.render(line, True, (255, 255, 255))
            self.screen.blit(line_surf, (x_start, y_start + i * line_height))

        # 6) Curseur clignotant
        last_line_w = self.dialogue_font.size(lines[-1])[0]
        cursor_x = x_start + last_line_w + 6
        cursor_y = y_start + (len(lines) - 1) * line_height
        if int(time.time() * 4) % 2 == 0:
            pygame.draw.rect(self.screen, (255, 255, 255), (cursor_x, cursor_y, 3, line_height - 4))

        # 7) Contour de la boîte (accent)
        pygame.draw.rect(self.screen, (255, 180, 80), box, 3, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), box, 1, border_radius=8)

    def _draw_title_text(self, text):
        scale = self.title_scale
        if scale <= 0:
            return
        size = int(38 + 22 * scale)
        font = pygame.font.SysFont("Arial", size, bold=True)
        # Texte blanc pour une bonne visibilité
        surf = font.render(text, True, (255, 255, 255))
        text_rect = surf.get_rect(center=(self.width // 2, self.height * 0.32))
        pad_x, pad_y = 40, 24
        box = text_rect.inflate(pad_x * 2, pad_y * 2)
        alpha = int(255 * scale)

        # Ombre
        shadow = box.inflate(8, 8)
        shadow.x += 6
        shadow.y += 6
        shadow_surf = pygame.Surface((shadow.w, shadow.h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, int(120 * scale)))
        self.screen.blit(shadow_surf, shadow.topleft)

        # Fond semi-opaque (lisibilité sur tout arrière-plan)
        bg = pygame.Surface((box.w, box.h))
        bg.fill((22, 24, 38))
        bg.set_alpha(alpha)
        self.screen.blit(bg, box.topleft)
        # Contour orange + blanc (style jeu)
        pygame.draw.rect(self.screen, (255, 140, 0), box, 3, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), box, 1, border_radius=12)

        # Contour noir du texte pour le détacher
        outline = font.render(text, True, (0, 0, 0))
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
            self.screen.blit(outline, (text_rect.x + dx, text_rect.y + dy))
        surf.set_alpha(alpha)
        self.screen.blit(surf, text_rect)

    def _draw_skip_hint(self):
        hint = self.hint_font.render("Espace / Entrée pour passer", True, (140, 140, 160))
        r = hint.get_rect(bottomright=(self.width - 20, self.height - 12))
        self.screen.blit(hint, r)

    def is_finished(self):
        return self.finished
