import random

class Sabotage:
    def __init__(self, name, cost, type, effect_func):
        self.name = name
        self.cost = cost
        self.type = type
        self.effect_func = effect_func
        
    def execute(self, target_player):
        self.effect_func(target_player)

# Sabotage Effects
def break_fryer(player):
    player.equipment["fryer"].break_machine()

def spread_rumor(player):
    player.modify_reputation(-15)

def falsify_menu(player):
    player.equipment["menu"].break_machine()

def call_inspection(player):
    # This would trigger an event, for now just high risk state
    player.reputation -= 5 # Immediate suspicion penalty
    # In a full event system, this adds an Inspection Event to the queue targeting this player

# List of Sabotages
SABOTAGES = {
    "break_fryer": Sabotage("Casse Friteuse", 50, "material", break_fryer),
    "rumor": Sabotage("Lancer Rumeur", 30, "reputation", spread_rumor),
    "fake_menu": Sabotage("Falsifier Carte", 40, "material", falsify_menu),
    "inspection": Sabotage("Contrôle Hygiène", 80, "inspection", call_inspection)
}
