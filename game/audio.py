"""
Système audio pour SnackAnarchy
Gère les sons et la musique du jeu
"""
import pygame
import os
import sys
from config import *
from game.assets_loader import get_resource_path

class AudioManager:
    _instance = None
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = AudioManager()
        return cls._instance
    
    def __init__(self):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)  # Plus de canaux pour les effets
        
        self.sounds = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        self.muted = False
        
        # Canaux dédiés
        self.channels = {
            'ui': pygame.mixer.Channel(0),
            'player1': pygame.mixer.Channel(1),
            'player2': pygame.mixer.Channel(2),
            'client': pygame.mixer.Channel(3),
            'ambient': pygame.mixer.Channel(4),
            'combat': pygame.mixer.Channel(5),
            'sabotage': pygame.mixer.Channel(6),
        }
        
        self._load_sounds()
        
    def _load_sounds(self):
        """Charge tous les sons du jeu ou crée des sons synthétiques"""
        sound_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sounds')
        
        # Créer les sons synthétiques si les fichiers n'existent pas
        self._create_synthetic_sounds()
        
    def _create_synthetic_sounds(self):
        """Crée des sons synthétiques avec pygame"""
        import numpy as np
        
        sample_rate = 44100
        
        # Son de pas
        self.sounds['footstep'] = self._generate_sound(
            frequency=200, duration=0.1, wave_type='noise', volume=0.3
        )
        
        # Son d'interaction/service
        self.sounds['serve'] = self._generate_sound(
            frequency=800, duration=0.2, wave_type='sine', volume=0.5
        )
        
        # Son de caisse enregistreuse (cha-ching!)
        self.sounds['money'] = self._generate_sound(
            frequency=1200, duration=0.15, wave_type='square', volume=0.4
        )
        
        # Son de client content
        self.sounds['client_happy'] = self._generate_sound(
            frequency=600, duration=0.3, wave_type='sine', volume=0.4
        )
        
        # Son de client mécontent
        self.sounds['client_angry'] = self._generate_sound(
            frequency=150, duration=0.4, wave_type='sawtooth', volume=0.5
        )
        
        # Son de minijeu réussi
        self.sounds['minigame_success'] = self._generate_chord(
            frequencies=[523, 659, 784], duration=0.4, volume=0.5
        )
        
        # Son de minijeu raté
        self.sounds['minigame_fail'] = self._generate_sound(
            frequency=150, duration=0.5, wave_type='sawtooth', volume=0.4
        )
        
        # Son de touche dans le minijeu
        self.sounds['key_press'] = self._generate_sound(
            frequency=440, duration=0.05, wave_type='square', volume=0.3
        )
        
        # Son de sabotage
        self.sounds['sabotage'] = self._generate_sound(
            frequency=100, duration=0.6, wave_type='noise', volume=0.5
        )
        
        # Son de vol de broche
        self.sounds['steal_spit'] = self._generate_sound(
            frequency=300, duration=0.3, wave_type='sawtooth', volume=0.6
        )
        
        # Son de ramassage d'objet
        self.sounds['pickup'] = self._generate_sound(
            frequency=600, duration=0.15, wave_type='sine', volume=0.4
        )
        
        # Son de coup de couteau/fourchette
        self.sounds['stab'] = self._generate_sound(
            frequency=80, duration=0.2, wave_type='noise', volume=0.7
        )
        
        # Son de client qui fuit
        self.sounds['client_flee'] = self._generate_sound(
            frequency=400, duration=0.3, wave_type='sine', volume=0.4
        )
        
        # Son de client qui meurt (plus dramatique)
        self.sounds['client_death'] = self._generate_sound(
            frequency=120, duration=0.8, wave_type='sawtooth', volume=0.6
        )
        
        # Son d'équipement qui casse
        self.sounds['break'] = self._generate_sound(
            frequency=80, duration=0.5, wave_type='noise', volume=0.6
        )
        
        # Son de réparation
        self.sounds['repair'] = self._generate_chord(
            frequencies=[400, 500, 600], duration=0.3, volume=0.4
        )
        
        # Son de spawn client
        self.sounds['client_spawn'] = self._generate_sound(
            frequency=500, duration=0.2, wave_type='sine', volume=0.3
        )
        
        # Son de transition de zone (porte)
        self.sounds['door'] = self._generate_sound(
            frequency=300, duration=0.25, wave_type='square', volume=0.4
        )
        
        # Son de timer warning
        self.sounds['timer_warning'] = self._generate_sound(
            frequency=880, duration=0.1, wave_type='square', volume=0.5
        )
        
        # Son de game over
        self.sounds['game_over'] = self._generate_chord(
            frequencies=[200, 150, 100], duration=1.0, volume=0.6
        )
        
        # Son de victoire
        self.sounds['victory'] = self._generate_chord(
            frequencies=[523, 659, 784, 1047], duration=0.8, volume=0.6
        )
        
        # Son de menu navigation
        self.sounds['menu_move'] = self._generate_sound(
            frequency=400, duration=0.05, wave_type='sine', volume=0.3
        )
        
        # Son de menu sélection
        self.sounds['menu_select'] = self._generate_sound(
            frequency=600, duration=0.1, wave_type='sine', volume=0.4
        )
        
        # Son de stock vide
        self.sounds['stock_empty'] = self._generate_sound(
            frequency=200, duration=0.3, wave_type='square', volume=0.4
        )
        
        # Son de réapprovisionnement
        self.sounds['restock'] = self._generate_chord(
            frequencies=[400, 600, 800], duration=0.2, volume=0.4
        )
        
    def _generate_sound(self, frequency, duration, wave_type='sine', volume=0.5):
        """Génère un son synthétique"""
        import numpy as np
        
        sample_rate = 44100
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == 'sawtooth':
            wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
        elif wave_type == 'noise':
            wave = np.random.uniform(-1, 1, num_samples)
            # Appliquer un filtre passe-bas simple
            for i in range(1, len(wave)):
                wave[i] = wave[i-1] * 0.9 + wave[i] * 0.1
        else:
            wave = np.sin(2 * np.pi * frequency * t)
        
        # Enveloppe ADSR simple
        attack = int(num_samples * 0.1)
        decay = int(num_samples * 0.1)
        release = int(num_samples * 0.3)
        
        envelope = np.ones(num_samples)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[-release:] = np.linspace(1, 0, release)
        
        wave = wave * envelope * volume
        
        # Convertir en format audio
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        
        sound = pygame.sndarray.make_sound(stereo_wave)
        return sound
    
    def _generate_chord(self, frequencies, duration, volume=0.5):
        """Génère un accord (plusieurs fréquences)"""
        import numpy as np
        
        sample_rate = 44100
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        wave = np.zeros(num_samples)
        for freq in frequencies:
            wave += np.sin(2 * np.pi * freq * t)
        
        wave = wave / len(frequencies)  # Normaliser
        
        # Enveloppe
        attack = int(num_samples * 0.05)
        release = int(num_samples * 0.4)
        
        envelope = np.ones(num_samples)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[-release:] = np.linspace(1, 0, release)
        
        wave = wave * envelope * volume
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    def play(self, sound_name, channel='ui', loops=0):
        """Joue un son"""
        if self.muted:
            return
            
        if sound_name not in self.sounds:
            return
            
        sound = self.sounds[sound_name]
        sound.set_volume(self.sfx_volume)
        
        if channel in self.channels:
            self.channels[channel].play(sound, loops=loops)
        else:
            sound.play(loops=loops)
            
    def play_music(self, music_name='ambient'):
        """Joue une musique de fond (loop)"""
        if self.muted:
            return
            
        # Chemin vers la musique (compatible PyInstaller)
        music_path = get_resource_path(os.path.join('assets', 'music_ambient.wav'))
        
        # Générer la musique si elle n'existe pas
        if not os.path.exists(music_path):
            try:
                self._generate_ambient_music(music_path)
            except Exception as e:
                print(f"Impossible de générer la musique: {e}")
                return
            
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)  # -1 = boucle infinie
            except Exception as e:
                print(f"Erreur chargement musique: {e}")
        
    def stop_music(self):
        """Arrête la musique"""
        pygame.mixer.music.stop()
        
    def _generate_ambient_music(self, filepath):
        """Génère une musique d'ambiance style fast-food/arcade"""
        import numpy as np
        import wave
        import struct
        
        sample_rate = 44100
        duration = 30  # 30 secondes de boucle
        
        num_samples = sample_rate * duration
        t = np.linspace(0, duration, num_samples, False)
        
        # Créer une musique funky/arcade pour fast-food
        music = np.zeros(num_samples)
        
        # Basse funky (groove de base)
        bass_pattern = [65.41, 0, 65.41, 0, 82.41, 0, 65.41, 0]  # C2, E2, C2 pattern
        beats_per_second = 2  # 120 BPM
        beat_duration = 1.0 / beats_per_second
        
        for i, note in enumerate(bass_pattern * int(duration * beats_per_second / len(bass_pattern))):
            if note > 0:
                start = int(i * beat_duration * sample_rate / 2)
                end = int((i + 0.4) * beat_duration * sample_rate / 2)
                if end <= num_samples:
                    segment_t = t[start:end] - t[start]
                    # Son de basse avec un peu de growl
                    bass_wave = np.sin(2 * np.pi * note * segment_t) * 0.4
                    bass_wave += np.sin(2 * np.pi * note * 2 * segment_t) * 0.1
                    # Envelope
                    env = np.exp(-segment_t * 4)
                    music[start:end] += bass_wave * env
        
        # Accords/pads (ambiance chaude)
        chord_freqs = [
            [261.63, 329.63, 392.00],  # C major
            [293.66, 369.99, 440.00],  # D major
            [261.63, 329.63, 392.00],  # C major
            [246.94, 311.13, 369.99],  # B minor
        ]
        
        chord_duration = duration / len(chord_freqs)
        for i, chord in enumerate(chord_freqs * 2):
            start = int(i * chord_duration * sample_rate / 2)
            end = int((i + 1) * chord_duration * sample_rate / 2)
            if end <= num_samples:
                segment_t = t[start:end] - t[start]
                chord_wave = np.zeros(end - start)
                for freq in chord:
                    chord_wave += np.sin(2 * np.pi * freq * segment_t) * 0.08
                # Envelope douce
                attack = int(0.1 * (end - start))
                release = int(0.2 * (end - start))
                env = np.ones(end - start)
                env[:attack] = np.linspace(0, 1, attack)
                env[-release:] = np.linspace(1, 0, release)
                music[start:end] += chord_wave * env
        
        # Mélodie simple et accrocheuse (style arcade)
        melody_notes = [
            523.25, 0, 587.33, 523.25, 0, 392.00, 440.00, 0,
            523.25, 0, 659.25, 587.33, 0, 523.25, 0, 0,
            698.46, 0, 659.25, 587.33, 0, 523.25, 587.33, 0,
            523.25, 0, 440.00, 392.00, 0, 349.23, 392.00, 0,
        ]
        
        note_duration = duration / len(melody_notes)
        for i, note in enumerate(melody_notes * 2):
            if note > 0:
                start = int(i * note_duration * sample_rate / 2)
                end = int((i + 0.7) * note_duration * sample_rate / 2)
                if end <= num_samples:
                    segment_t = t[start:end] - t[start]
                    # Son type synthé rétro
                    melody_wave = np.sin(2 * np.pi * note * segment_t) * 0.15
                    melody_wave += np.sin(2 * np.pi * note * 2 * segment_t) * 0.05  # Harmonique
                    # Envelope
                    attack = int(0.05 * (end - start))
                    release = int(0.3 * (end - start))
                    env = np.ones(end - start)
                    env[:attack] = np.linspace(0, 1, attack)
                    env[-release:] = np.linspace(1, 0.2, release)
                    music[start:end] += melody_wave * env
        
        # Percussion légère (hi-hat style)
        for i in range(int(duration * 4)):  # 4 hits par seconde
            start = int(i * sample_rate / 4)
            hit_length = int(sample_rate * 0.05)
            if start + hit_length <= num_samples:
                # Noise burst pour hi-hat
                noise = np.random.uniform(-1, 1, hit_length)
                env = np.exp(-np.linspace(0, 10, hit_length))
                music[start:start + hit_length] += noise * env * 0.08
        
        # Kick drum sur les temps forts
        for i in range(int(duration * 2)):  # 2 kicks par seconde
            start = int(i * sample_rate / 2)
            kick_length = int(sample_rate * 0.1)
            if start + kick_length <= num_samples:
                kick_t = np.linspace(0, 0.1, kick_length)
                # Kick avec pitch drop
                kick_freq = 150 * np.exp(-kick_t * 30)
                kick = np.sin(2 * np.pi * kick_freq * kick_t)
                env = np.exp(-kick_t * 20)
                music[start:start + kick_length] += kick * env * 0.25
        
        # Normaliser
        max_val = np.max(np.abs(music))
        if max_val > 0:
            music = music / max_val * 0.7
        
        # Convertir en 16-bit
        music_int = (music * 32767).astype(np.int16)
        
        # Sauvegarder en WAV
        try:
            with wave.open(filepath, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(music_int.tobytes())
            print(f"Musique d'ambiance générée: {filepath}")
        except Exception as e:
            print(f"Erreur génération musique: {e}")
        
    def stop_all(self):
        """Arrête tous les sons"""
        pygame.mixer.stop()
        
    def set_music_volume(self, volume):
        """Définit le volume de la musique (0.0 à 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
        
    def set_sfx_volume(self, volume):
        """Définit le volume des effets sonores (0.0 à 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))
        
    def toggle_mute(self):
        """Active/désactive le son"""
        self.muted = not self.muted
        if self.muted:
            self.stop_all()
        return self.muted


# Fonction utilitaire pour jouer un son rapidement
def play_sound(sound_name, channel='ui'):
    """Raccourci pour jouer un son"""
    AudioManager.get().play(sound_name, channel)
