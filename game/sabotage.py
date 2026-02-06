import random
import time
from game.audio import play_sound

class Sabotage:
    def __init__(self, name, cost, sabotage_type, effect_func, cooldown=0, requires_proximity=False):
        self.name = name
        self.cost = cost
        self.sabotage_type = sabotage_type
        self.effect_func = effect_func
        self.cooldown = cooldown
        self.requires_proximity = requires_proximity
        self.last_used = 0
        
    def can_execute(self, executor_player, target_player):
        """Vérifie si le sabotage peut être exécuté"""
        # Vérifier le cooldown
        if time.time() - self.last_used < self.cooldown:
            return False, "En recharge"
            
        # Vérifier l'argent
        if executor_player.money < self.cost:
            return False, "Pas assez d'argent"
            
        # Vérifier la proximité si nécessaire
        if self.requires_proximity:
            if executor_player.current_zone != target_player.current_zone:
                return False, "Trop loin"
            distance = executor_player.get_distance_to(target_player)
            if distance > 150:  # ~2 tuiles
                return False, "Trop loin"
                
        return True, None
        
    def execute(self, executor_player, target_player):
        """Exécute le sabotage"""
        can_do, reason = self.can_execute(executor_player, target_player)
        if not can_do:
            return False, reason
            
        # Déduire le coût
        executor_player.money -= self.cost
        
        # Exécuter l'effet
        result = self.effect_func(executor_player, target_player)
        
        # Mettre à jour le cooldown
        self.last_used = time.time()
        
        play_sound('sabotage', 'sabotage')
        
        return True, result


# Sabotage Effects
def break_fryer(executor, target):
    target.equipment["fryer"].break_machine()
    play_sound('break', 'sabotage')
    return "Friteuse cassée!"

def spread_rumor(executor, target):
    target.modify_reputation(-15)
    return "Rumeur lancée! -15 réputation"

def falsify_menu(executor, target):
    target.equipment["menu"].break_machine()
    play_sound('break', 'sabotage')
    return "Menu falsifié!"

def call_inspection(executor, target):
    target.modify_reputation(-5)
    # Augmente le risque d'inspection
    target.equipment["toilets"].broken = True
    return "Inspection appelée!"

def steal_spit(executor, target):
    """Vole la broche à kebab du rival - nécessite d'être dans son restaurant"""
    if not hasattr(target, 'food_stock'):
        return "Impossible de voler"
        
    if not target.food_stock.is_spit_available():
        return "Broche déjà volée!"
        
    # Voler la broche pour 30 secondes
    target.food_stock.steal_spit(duration=30)
    
    # Casse temporairement la broche de l'adversaire
    target.equipment["spit"].break_machine()
    
    play_sound('steal_spit', 'sabotage')
    
    return "Broche volée! 30 secondes de chaos!"

def poison_food(executor, target):
    """Empoisonne le stock de nourriture"""
    if hasattr(target, 'food_stock'):
        # Réduit la qualité de tout le stock
        for ing_name in target.food_stock.ingredients:
            target.food_stock.ingredients[ing_name]['quantity'] = max(0, 
                target.food_stock.ingredients[ing_name]['quantity'] - 5)
    target.modify_reputation(-10)
    return "Nourriture empoisonnée! -10 réputation, stock réduit"


def hire_thief(executor, target):
    """Paye un voleur qui vole 100€ dans la caisse de l'adversaire. Coût 100€, -5 réputation pour l'utilisateur."""
    stolen = min(100, target.money)
    target.money = max(0, target.money - 100)
    executor.modify_reputation(-5)
    return f"Voleur envoyé! {stolen}€ volés, -5% réputation"


# List of Sabotages
SABOTAGES = {
    "break_fryer": Sabotage("Casse Friteuse", 50, "material", break_fryer, cooldown=60),
    "rumor": Sabotage("Lancer Rumeur", 30, "reputation", spread_rumor, cooldown=30),
    "fake_menu": Sabotage("Falsifier Carte", 40, "material", falsify_menu, cooldown=45),
    "inspection": Sabotage("Contrôle Hygiène", 80, "inspection", call_inspection, cooldown=90),
    "steal_spit": Sabotage("Voler la Broche", 60, "theft", steal_spit, cooldown=45, requires_proximity=True),
    "poison_food": Sabotage("Empoisonner Stock", 70, "sabotage", poison_food, cooldown=60),
    "thief": Sabotage("Payer un Voleur", 100, "theft", hire_thief, cooldown=60),
}


class SabotageManager:
    """Gestionnaire des sabotages en cours"""
    
    def __init__(self):
        self.active_sabotages = []
        self.sabotage_history = []
        
    def execute_sabotage(self, sabotage_name, executor, target):
        """Exécute un sabotage"""
        if sabotage_name not in SABOTAGES:
            return False, "Sabotage inconnu"
            
        sabotage = SABOTAGES[sabotage_name]
        success, message = sabotage.execute(executor, target)
        
        if success:
            self.sabotage_history.append({
                'name': sabotage_name,
                'executor': executor.id,
                'target': target.id,
                'time': time.time(),
                'message': message
            })
            
        return success, message
        
    def get_available_sabotages(self, player):
        """Retourne les sabotages disponibles pour un joueur"""
        available = []
        for name, sabotage in SABOTAGES.items():
            if player.money >= sabotage.cost:
                cooldown_remaining = max(0, sabotage.cooldown - (time.time() - sabotage.last_used))
                available.append({
                    'name': name,
                    'display_name': sabotage.name,
                    'cost': sabotage.cost,
                    'cooldown': cooldown_remaining,
                    'requires_proximity': sabotage.requires_proximity
                })
        return available
