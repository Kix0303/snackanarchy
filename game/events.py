import random
import time

class Event:
    def __init__(self, name, description, duration, effect_func):
        self.name = name
        self.description = description
        self.start_time = time.time()
        self.duration = duration
        self.effect_func = effect_func
        self.active = True
        
    def update(self):
        if time.time() - self.start_time > self.duration:
            self.active = False

def police_raid(game_state):
    # Example: Reduce all players money if they have dirty ingredients?
    pass

def health_inspection(game_state):
    for player in game_state.players:
        risk = player.equipment["toilets"].get_inspection_risk()
        if random.random() < risk:
            player.add_money(-100) # Fine
            player.modify_reputation(-20)

class EventManager:
    def __init__(self, game_state):
        self.game_state = game_state
        self.active_events = []
        self.last_event_time = time.time()
        self.event_interval = 60 # Every minute
        
    def update(self):
        # Random spawn
        if time.time() - self.last_event_time > self.event_interval:
            if random.random() < 0.3: # 30% chance
                self.trigger_random_event()
            self.last_event_time = time.time()
            
        # Update active events
        for event in self.active_events:
            event.update()
        self.active_events = [e for e in self.active_events if e.active]
        
    def trigger_random_event(self):
        # For prototype just simple print or effect
        event = Event("Inspection", "Inspection sanitaire !", 5, health_inspection)
        event.effect_func(self.game_state) # Immediate effect for this type
        self.active_events.append(event)
