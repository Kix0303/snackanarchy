import random

class Ingredient:
    def __init__(self, name, type, is_dirty=False, effect=None):
        self.name = name
        self.type = type # base, dirty
        self.is_dirty = is_dirty
        self.effect = effect # Dictionary of impacts e.g., {'reputation': -10}

class Dish:
    def __init__(self, name, base_ingredients):
        self.name = name
        self.base_ingredients = base_ingredients
        self.added_ingredients = []
        
    def add_ingredient(self, ingredient):
        self.added_ingredients.append(ingredient)
        
    def is_valid(self):
        # Check if all base ingredients are present
        base_names = [i.name for i in self.base_ingredients]
        added_names = [i.name for i in self.added_ingredients]
        return all(name in added_names for name in base_names)
        
    def get_quality_score(self):
        score = 100
        for ing in self.added_ingredients:
            if ing.is_dirty:
                score -= 20
        return max(0, score)

# Ingrédients de base par type de plat (pour créer des instances fraîches)
def _tacos_base_ingredients():
    return [
        Ingredient("Galette de blé", "base"),
        Ingredient("Viande", "base"),
        Ingredient("Sauce fromagère", "base"),
        Ingredient("Frites", "base"),
        Ingredient("Sel", "base")
    ]

def _kebab_base_ingredients():
    return [
        Ingredient("Pain pita", "base"),
        Ingredient("Viande kebab", "base"),
        Ingredient("Salade", "base"),
        Ingredient("Tomates", "base"),
        Ingredient("Oignons", "base")
    ]

# Plats prédéfinis — chaque appel crée une nouvelle instance (pas de partage entre clients)
def create_tacos_xxl():
    return Dish("Tacos XXL", _tacos_base_ingredients())

def create_tacos_m():
    return Dish("Tacos M", _tacos_base_ingredients())

def create_burritos():
    return Dish("Burritos", _tacos_base_ingredients())

def create_nachos():
    return Dish("Nachos", _tacos_base_ingredients())

def create_tacos_s():
    return Dish("Tacos S", _tacos_base_ingredients())

def create_tacos_l():
    return Dish("Tacos L", _tacos_base_ingredients())

def create_kebab():
    return Dish("Kebab", _kebab_base_ingredients())

def create_kebab_wrap():
    return Dish("Kebab Wrap", _kebab_base_ingredients())

def create_assiettes():
    return Dish("Assiettes", _kebab_base_ingredients())

# Créateurs par restaurant pour répartition variée (chaque client a un plat différent)
TACOS_DISH_CREATORS = [create_tacos_xxl, create_tacos_m, create_burritos, create_nachos, create_tacos_s, create_tacos_l]
KEBAB_DISH_CREATORS = [create_kebab, create_kebab_wrap, create_assiettes]

def create_dish_for_restaurant(restaurant):
    """Retourne une nouvelle instance de plat pour ce restaurant (toujours une instance fraîche)."""
    if restaurant == "tacos":
        return random.choice(TACOS_DISH_CREATORS)()
    if restaurant == "kebab":
        return random.choice(KEBAB_DISH_CREATORS)()
    # rue / indécis
    return random.choice(TACOS_DISH_CREATORS + KEBAB_DISH_CREATORS)()

# Dirty Ingredients
DIRTY_INGREDIENTS = [
    Ingredient("Sauce périmée", "dirty", True, {'symptoms': 0.8, 'reputation': -10}),
    Ingredient("Trop de fromage", "dirty", True, {'eating_time': 1.5}),
    Ingredient("Frites brûlées", "dirty", True, {'reputation': -5}),
    Ingredient("Hygiène douteuse", "dirty", True, {'inspection_risk': 0.5}),
    Ingredient("Viande trop cuite", "dirty", True, {'quality': -20}),
    Ingredient("Sauce coupée à l'eau", "dirty", True, {'quality': -10, 'money': 2}), # Saves money?
    Ingredient("Salade flétrie", "dirty", True, {'quality': -5}),
]
