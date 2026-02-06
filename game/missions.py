"""
Système de missions - Objectifs à accomplir durant la partie
"""
import random
import time
from config import *


class Mission:
    """Représente une mission individuelle"""
    
    def __init__(self, mission_id, name, description, target, reward_money, reward_reputation, 
                 mission_type="count", icon=None):
        self.id = mission_id
        self.name = name
        self.description = description
        self.target = target  # Objectif à atteindre
        self.progress = 0     # Progression actuelle
        self.reward_money = reward_money
        self.reward_reputation = reward_reputation
        self.mission_type = mission_type  # "count", "time", "streak"
        self.icon = icon
        self.completed = False
        self.claimed = False  # Si la récompense a été réclamée
        self.start_time = None
    
    def update_progress(self, amount=1):
        """Met à jour la progression"""
        if self.completed:
            return False
        
        self.progress = min(self.progress + amount, self.target)
        if self.progress >= self.target:
            self.completed = True
            return True
        return False
    
    def get_progress_percent(self):
        """Retourne le pourcentage de progression"""
        if self.target == 0:
            return 100
        return int((self.progress / self.target) * 100)
    
    def get_progress_text(self):
        """Retourne le texte de progression"""
        return f"{self.progress}/{self.target}"
    
    def claim_reward(self, player):
        """Réclame la récompense de la mission"""
        if not self.completed or self.claimed:
            return False
        
        player.add_money(self.reward_money)
        player.modify_reputation(self.reward_reputation)
        self.claimed = True
        return True


# Définitions des missions disponibles (icônes: noms pour dessin personnalisé)
MISSION_TEMPLATES = {
    # Missions de service
    'serve_tacos_5': {
        'name': "Apprenti Tacos",
        'description': "Servir 5 tacos",
        'target': 5,
        'reward_money': 30,
        'reward_reputation': 3,
        'type': 'serve_tacos',
        'icon': 'tacos'
    },
    'serve_tacos_10': {
        'name': "Expert Tacos",
        'description': "Servir 10 tacos",
        'target': 10,
        'reward_money': 75,
        'reward_reputation': 5,
        'type': 'serve_tacos',
        'icon': 'tacos'
    },
    'serve_kebabs_5': {
        'name': "Apprenti Kebab",
        'description': "Servir 5 kebabs",
        'target': 5,
        'reward_money': 30,
        'reward_reputation': 3,
        'type': 'serve_kebabs',
        'icon': 'kebab'
    },
    'serve_kebabs_10': {
        'name': "Expert Kebab",
        'description': "Servir 10 kebabs",
        'target': 10,
        'reward_money': 75,
        'reward_reputation': 5,
        'type': 'serve_kebabs',
        'icon': 'kebab'
    },
    'serve_clients_3': {
        'name': "Service Rapide",
        'description': "Servir 3 clients",
        'target': 3,
        'reward_money': 20,
        'reward_reputation': 2,
        'type': 'serve_clients',
        'icon': 'clients'
    },
    'serve_clients_10': {
        'name': "Rush Hour",
        'description': "Servir 10 clients",
        'target': 10,
        'reward_money': 60,
        'reward_reputation': 5,
        'type': 'serve_clients',
        'icon': 'clients'
    },
    'serve_clients_20': {
        'name': "Marathon du Service",
        'description': "Servir 20 clients",
        'target': 20,
        'reward_money': 150,
        'reward_reputation': 10,
        'type': 'serve_clients',
        'icon': 'trophy'
    },
    
    # Missions d'argent
    'earn_money_100': {
        'name': "Premiere Recette",
        'description': "Gagner 100 euros",
        'target': 100,
        'reward_money': 25,
        'reward_reputation': 2,
        'type': 'earn_money',
        'icon': 'money'
    },
    'earn_money_300': {
        'name': "Business Florissant",
        'description': "Gagner 300 euros",
        'target': 300,
        'reward_money': 50,
        'reward_reputation': 4,
        'type': 'earn_money',
        'icon': 'money'
    },
    'earn_money_500': {
        'name': "Magnat du Fast-Food",
        'description': "Gagner 500 euros",
        'target': 500,
        'reward_money': 100,
        'reward_reputation': 8,
        'type': 'earn_money',
        'icon': 'money'
    },
    
    # Missions de réputation
    'reach_reputation_60': {
        'name': "Bonne Reputation",
        'description': "Atteindre 60% de reputation",
        'target': 60,
        'reward_money': 40,
        'reward_reputation': 0,
        'type': 'reach_reputation',
        'icon': 'star'
    },
    'reach_reputation_80': {
        'name': "Restaurant Populaire",
        'description': "Atteindre 80% de reputation",
        'target': 80,
        'reward_money': 80,
        'reward_reputation': 0,
        'type': 'reach_reputation',
        'icon': 'star'
    },
    
    # Missions de sabotage
    'sabotage_1': {
        'name': "Premier Coup Bas",
        'description': "Effectuer 1 sabotage",
        'target': 1,
        'reward_money': 20,
        'reward_reputation': 0,
        'type': 'sabotage',
        'icon': 'sabotage'
    },
    'sabotage_3': {
        'name': "Saboteur",
        'description': "Effectuer 3 sabotages",
        'target': 3,
        'reward_money': 50,
        'reward_reputation': 0,
        'type': 'sabotage',
        'icon': 'sabotage'
    },
    
    # Missions de nettoyage
    'clean_restaurant_1': {
        'name': "Coup de Balai",
        'description': "Nettoyer le restaurant 1 fois",
        'target': 1,
        'reward_money': 15,
        'reward_reputation': 3,
        'type': 'clean',
        'icon': 'clean'
    },
    'clean_restaurant_3': {
        'name': "Hygiene Parfaite",
        'description': "Nettoyer le restaurant 3 fois",
        'target': 3,
        'reward_money': 40,
        'reward_reputation': 5,
        'type': 'clean',
        'icon': 'clean'
    },
    
    # Missions de combat
    'attack_1': {
        'name': "Premier Sang",
        'description': "Attaquer un client ennemi",
        'target': 1,
        'reward_money': 10,
        'reward_reputation': 0,
        'type': 'attack',
        'icon': 'attack'
    },
    'attack_5': {
        'name': "Guerrier du Snack",
        'description': "Attaquer 5 clients",
        'target': 5,
        'reward_money': 35,
        'reward_reputation': 0,
        'type': 'attack',
        'icon': 'attack'
    },
    
    # Missions streak
    'streak_3': {
        'name': "Combo x3",
        'description': "Servir 3 clients sans erreur",
        'target': 3,
        'reward_money': 40,
        'reward_reputation': 3,
        'type': 'streak',
        'icon': 'streak'
    },
    'streak_5': {
        'name': "Combo x5",
        'description': "Servir 5 clients sans erreur",
        'target': 5,
        'reward_money': 80,
        'reward_reputation': 6,
        'type': 'streak',
        'icon': 'streak'
    },
}


class MissionManager:
    """Gère les missions d'un joueur"""
    
    MAX_ACTIVE_MISSIONS = 3
    
    def __init__(self, player):
        self.player = player
        self.active_missions = []
        self.completed_missions = []
        self.current_streak = 0  # Pour les missions streak
        
        # Générer les missions initiales
        self._generate_initial_missions()
    
    def _get_restaurant(self):
        """Restaurant du joueur (tacos ou kebab) pour filtrer les missions de service."""
        return getattr(self.player, 'owns_restaurant', getattr(self.player, 'home_zone', 'tacos'))

    def _mission_ok_for_player(self, mission_id):
        """True si la mission est réalisable par le joueur (ex: pas 'servir kebabs' pour joueur tacos)."""
        restaurant = self._get_restaurant()
        if mission_id.startswith('serve_tacos_'):
            return restaurant == 'tacos'
        if mission_id.startswith('serve_kebabs_'):
            return restaurant == 'kebab'
        return True

    def _generate_initial_missions(self):
        """Génère les missions de départ (uniquement réalisables pour ce joueur)."""
        restaurant = self._get_restaurant()
        # Mission de service selon le restaurant (tacos ou kebab, pas les deux)
        serve_mission = 'serve_tacos_5' if restaurant == 'tacos' else 'serve_kebabs_5'

        easy_missions = ['serve_clients_3', 'earn_money_100']
        medium_missions = [serve_mission, 'reach_reputation_60', 'clean_restaurant_1']

        selected = []
        easy = random.choice(easy_missions)
        selected.append(easy)

        random.shuffle(medium_missions)
        for m in medium_missions:
            if m not in selected and len(selected) < self.MAX_ACTIVE_MISSIONS:
                selected.append(m)

        for mission_id in selected:
            self._add_mission(mission_id)
    
    def _add_mission(self, mission_id):
        """Ajoute une mission active"""
        if mission_id not in MISSION_TEMPLATES:
            return
        
        template = MISSION_TEMPLATES[mission_id]
        mission = Mission(
            mission_id=mission_id,
            name=template['name'],
            description=template['description'],
            target=template['target'],
            reward_money=template['reward_money'],
            reward_reputation=template['reward_reputation'],
            mission_type=template['type'],
            icon=template.get('icon', 'default')
        )
        mission.start_time = time.time()
        self.active_missions.append(mission)
    
    def update(self, event_type, value=1):
        """Met à jour les missions selon un événement
        
        event_type peut être:
        - 'serve_tacos': service d'un tacos
        - 'serve_kebabs': service d'un kebab
        - 'serve_clients': service d'un client
        - 'earn_money': argent gagné (value = montant)
        - 'reach_reputation': réputation actuelle (value = réputation)
        - 'sabotage': sabotage effectué
        - 'clean': nettoyage effectué
        - 'attack': attaque effectuée
        - 'serve_success': service réussi (pour streak)
        - 'serve_fail': service raté (reset streak)
        """
        completed_any = False
        
        for mission in self.active_missions[:]:  # Copie pour pouvoir modifier pendant l'itération
            if mission.completed:
                continue
            
            # Gestion des streaks
            if event_type == 'serve_success':
                self.current_streak += 1
                if mission.mission_type == 'streak':
                    if self.current_streak >= mission.target:
                        mission.progress = mission.target
                        mission.completed = True
                        completed_any = True
            elif event_type == 'serve_fail':
                self.current_streak = 0
            
            # Mise à jour selon le type de mission
            if mission.mission_type == event_type:
                if event_type in ('earn_money', 'reach_reputation'):
                    # Pour ces types, on set directement la valeur
                    mission.progress = value
                    if value >= mission.target:
                        mission.completed = True
                        completed_any = True
                else:
                    # Pour les autres, on incrémente
                    if mission.update_progress(value):
                        completed_any = True
        
        return completed_any
    
    def claim_completed_missions(self):
        """Réclame toutes les missions complétées"""
        claimed_count = 0
        total_money = 0
        total_reputation = 0
        
        for mission in self.active_missions[:]:
            if mission.completed and not mission.claimed:
                if mission.claim_reward(self.player):
                    claimed_count += 1
                    total_money += mission.reward_money
                    total_reputation += mission.reward_reputation
                    
                    # Déplacer vers les missions complétées
                    self.completed_missions.append(mission)
                    self.active_missions.remove(mission)
                    
                    # Incrémenter le compteur de missions du joueur
                    if hasattr(self.player, 'missions_completed'):
                        self.player.missions_completed += 1
                    else:
                        self.player.missions_completed = 1
                    
                    # Générer une nouvelle mission
                    self._generate_new_mission()
        
        return claimed_count, total_money, total_reputation
    
    def _generate_new_mission(self):
        """Génère une nouvelle mission pour remplacer une complétée (réalisable pour ce joueur)."""
        if len(self.active_missions) >= self.MAX_ACTIVE_MISSIONS:
            return

        used_ids = {m.id for m in self.active_missions}
        used_ids.update({m.id for m in self.completed_missions})

        available = [
            mid for mid in MISSION_TEMPLATES.keys()
            if mid not in used_ids and self._mission_ok_for_player(mid)
        ]

        if not available:
            available = [
                mid for mid in MISSION_TEMPLATES.keys()
                if self._mission_ok_for_player(mid)
            ]

        if available:
            new_mission_id = random.choice(available)
            self._add_mission(new_mission_id)
    
    def get_active_missions(self):
        """Retourne les missions actives"""
        return self.active_missions
    
    def get_unclaimed_count(self):
        """Retourne le nombre de missions complétées non réclamées"""
        return sum(1 for m in self.active_missions if m.completed and not m.claimed)
    
    def has_pending_rewards(self):
        """Vérifie s'il y a des récompenses à réclamer"""
        return self.get_unclaimed_count() > 0
