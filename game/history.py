"""
Système d'historique des parties - Sauvegarde et chargement des statistiques
"""
import json
import os
from datetime import datetime
from game.assets_loader import get_resource_path


class GameHistory:
    """Gère l'historique des parties et les statistiques des joueurs"""
    
    HISTORY_FILE = "game_history.json"
    MAX_GAMES = 50  # Nombre maximum de parties conservées
    
    _instance = None
    
    @classmethod
    def get(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = GameHistory()
        return cls._instance
    
    def __init__(self):
        self.history = []
        self.player_stats = {}  # Statistiques globales par joueur
        self._load()
    
    def _get_history_path(self):
        """Retourne le chemin du fichier d'historique"""
        # Cherche d'abord dans le dossier utilisateur pour la persistance
        user_data_dir = os.path.expanduser("~/.snackanarchy")
        if not os.path.exists(user_data_dir):
            try:
                os.makedirs(user_data_dir)
            except OSError:
                # Fallback vers le dossier du jeu
                return get_resource_path(self.HISTORY_FILE)
        return os.path.join(user_data_dir, self.HISTORY_FILE)
    
    def _load(self):
        """Charge l'historique depuis le fichier JSON"""
        path = self._get_history_path()
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get('games', [])
                    self.player_stats = data.get('player_stats', {})
        except (json.JSONDecodeError, IOError) as e:
            print(f"[History] Erreur chargement historique: {e}")
            self.history = []
            self.player_stats = {}
    
    def _save(self):
        """Sauvegarde l'historique dans le fichier JSON"""
        path = self._get_history_path()
        try:
            data = {
                'games': self.history[-self.MAX_GAMES:],  # Garde les N dernières parties
                'player_stats': self.player_stats
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[History] Erreur sauvegarde historique: {e}")
    
    def record_game(self, game_state):
        """Enregistre les résultats d'une partie terminée"""
        if not game_state or not game_state.game_over:
            return
        
        players = game_state.players
        winner_idx = game_state.get_winner()
        
        # Créer l'entrée de la partie
        game_record = {
            'date': datetime.now().isoformat(),
            'duration': game_state.game_duration,
            'winner': winner_idx,  # 0=égalité, 1=P1, 2=P2
            'players': []
        }
        
        for i, player in enumerate(players):
            player_data = {
                'name': getattr(player, 'username', f'Joueur {i+1}'),
                'restaurant': getattr(player, 'owns_restaurant', 'tacos' if i == 0 else 'kebab'),
                'money': player.money,
                'reputation': player.reputation,
                'clients_served': getattr(player, 'clients_served', 0),
                'tacos_served': getattr(player, 'tacos_served', 0),
                'kebabs_served': getattr(player, 'kebabs_served', 0),
                'attacks_made': getattr(player, 'attacks_made', 0),
                'sabotages_done': getattr(player, 'sabotages_done', 0),
                'missions_completed': getattr(player, 'missions_completed', 0),
                'is_winner': (winner_idx == i + 1)
            }
            game_record['players'].append(player_data)
            
            # Mettre à jour les statistiques globales du joueur
            self._update_player_stats(player_data)
        
        self.history.append(game_record)
        self._save()
    
    def _update_player_stats(self, player_data):
        """Met à jour les statistiques globales d'un joueur"""
        name = player_data['name']
        
        if name not in self.player_stats:
            self.player_stats[name] = {
                'games_played': 0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'total_money': 0,
                'total_clients_served': 0,
                'total_tacos': 0,
                'total_kebabs': 0,
                'total_attacks': 0,
                'total_sabotages': 0,
                'total_missions': 0,
                'best_money': 0,
                'best_reputation': 0
            }
        
        stats = self.player_stats[name]
        stats['games_played'] += 1
        
        if player_data['is_winner']:
            stats['wins'] += 1
        elif player_data.get('is_draw', False):
            stats['draws'] += 1
        else:
            stats['losses'] += 1
        
        stats['total_money'] += player_data['money']
        stats['total_clients_served'] += player_data.get('clients_served', 0)
        stats['total_tacos'] += player_data.get('tacos_served', 0)
        stats['total_kebabs'] += player_data.get('kebabs_served', 0)
        stats['total_attacks'] += player_data.get('attacks_made', 0)
        stats['total_sabotages'] += player_data.get('sabotages_done', 0)
        stats['total_missions'] += player_data.get('missions_completed', 0)
        
        if player_data['money'] > stats['best_money']:
            stats['best_money'] = player_data['money']
        if player_data['reputation'] > stats['best_reputation']:
            stats['best_reputation'] = player_data['reputation']
    
    def get_recent_games(self, limit=10):
        """Retourne les dernières parties"""
        return list(reversed(self.history[-limit:]))
    
    def get_player_stats(self, player_name):
        """Retourne les statistiques d'un joueur spécifique"""
        return self.player_stats.get(player_name, None)
    
    def get_all_player_stats(self):
        """Retourne les statistiques de tous les joueurs"""
        return self.player_stats
    
    def get_leaderboard(self, sort_by='wins'):
        """Retourne le classement des joueurs"""
        leaderboard = []
        for name, stats in self.player_stats.items():
            leaderboard.append({
                'name': name,
                **stats
            })
        
        # Trier par le critère demandé
        if sort_by == 'wins':
            leaderboard.sort(key=lambda x: (x['wins'], x['total_money']), reverse=True)
        elif sort_by == 'money':
            leaderboard.sort(key=lambda x: x['total_money'], reverse=True)
        elif sort_by == 'games':
            leaderboard.sort(key=lambda x: x['games_played'], reverse=True)
        
        return leaderboard
    
    def clear_history(self):
        """Efface tout l'historique (pour reset)"""
        self.history = []
        self.player_stats = {}
        self._save()
