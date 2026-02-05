# Diagramme de classes UML — SnackAnarchy

Documentation des classes du jeu avec schémas UML en ASCII.

---

## 1. Vue d'ensemble des packages

```
+------------------+  +------------------+  +------------------+  +------------------+
|      main        |  |      game       |  |    rendering     |  |      input       |
|  - Game          |  | - GameState     |  | - SplitScreen    |  | - KeyBindings    |
|                  |  | - Player        |  | - MenuRenderer   |  | - InputHandler   |
|                  |  | - Client        |  | - Camera         |  |                  |
|                  |  | - Zone/Map      |  | - InventoryMenu  |  |                  |
|                  |  | - Dishes        |  | - CarteMenu      |  |                  |
|                  |  | - Inventory     |  | - MissionDisplay |  |                  |
|                  |  | - Animation     |  | - etc.           |  |                  |
+------------------+  +------------------+  +------------------+  +------------------+
```

---

## 2. Package main

### Game

```
+------------------------------------------+
|                  Game                     |
+------------------------------------------+
| - screen: Surface                        |
| - clock: Clock                           |
| - running: bool                           |
| - current_state: str                      |
| - game_state: GameState | None           |
| - pause_start_time: float | None          |
| - total_pause_time: float                |
| - intro_cutscene: IntroCutscene | None   |
| - pending_player_configs: list | None    |
| - renderer: SplitScreenRenderer           |
| - menu_renderer: MenuRenderer            |
| - inventory_menu: InventoryMenu          |
| - carte_menu: CarteMenu                  |
| - keybind_menu: KeybindMenu              |
| - history_menu: HistoryMenu              |
| - tutorial_menu: TutorialMenu            |
| - mission_display: MissionDisplay        |
| - mission_notification: MissionNotification |
| - input_handler: InputHandler            |
| - key_bindings: KeyBindings             |
| - audio: AudioManager                    |
+------------------------------------------+
| + __init__()                             |
| + start_game(player_configs)           |
| + run()                                  |
| + _handle_events()                       |
| + _update()                              |
| + _draw()                                |
+------------------------------------------+
         | uses
         v
    GameState, SplitScreenRenderer, MenuRenderer,
    InventoryMenu, CarteMenu, KeybindMenu, HistoryMenu,
    TutorialMenu, MissionDisplay, IntroCutscene,
    InputHandler, KeyBindings, AudioManager
```

---

## 3. Package game — État et entités

### GameState

```
+------------------------------------------+
|               GameState                   |
+------------------------------------------+
| - world_map: WorldMap                    |
| - players: list[Player]                   |
| - player_configs: list                   |
| - clients: list[Client]                   |
| - last_spawn_time: float                 |
| - spawn_interval: float                  |
| - last_wander_spawn_time: float          |
| - wander_spawn_interval: float           |
| - wandering_clients_limit: int           |
| - event_manager: EventManager            |
| - weapon_spawner: WeaponSpawner         |
| - sabotage_manager: SabotageManager      |
| - animation_manager: AnimationManager    |
| - thief_animations: list                 |
| - audio: AudioManager                    |
| - start_time: float                      |
| - game_duration: float                   |
| - game_over: bool                        |
| - timer_warning_played: bool             |
+------------------------------------------+
| + __init__(player_configs)               |
| + update(events, input_action)            |
| + _spawn_initial_clients()               |
| + _get_restaurant_owner(zone_name)       |
| + handle_interaction(player_idx)         |
| + handle_attack(player_idx)              |
| + handle_sabotage(player_idx, name)      |
| + handle_sabotage_menu(player_idx)      |
| + handle_sweep(player_idx)              |
| + try_steal_spit(player_idx)             |
| + spawn_client(force_target_restaurant)  |
| + _spawn_wandering_client()              |
| + _recompute_queues()                    |
| + _get_queue_config(target_restaurant)   |
| + get_remaining_time(): int              |
| + draw_zone(surface, camera, zone_name)  |
| + get_winner(): int                      |
| + get_available_sabotages(player_idx)    |
| + get_player_stock_status(player_idx)    |
+------------------------------------------+
```

### Player (hérite de pygame.sprite.Sprite)

```
+------------------------------------------+
|     Player <<pygame.sprite.Sprite>>      |
+------------------------------------------+
| - id: int                                |
| - color: tuple                           |
| - username: str                          |
| - image_right, image_left, image: Surface|
| - mask: Mask                             |
| - rect: Rect                             |
| - speed: float                           |
| - vx, vy: float                         |
| - current_zone, home_zone: str           |
| - money: int                             |
| - reputation: int                        |
| - equipment: dict[str, Equipment]        |
| - current_client: Client | None         |
| - active_minigame: MiniGame | None       |
| - serve_animation: ServeAnimation | None |
| - inventory: PlayerInventory             |
| - food_stock: FoodStock                  |
| - walk_animation: WalkAnimation         |
| - attack_animation: AttackAnimation|None |
| - animation_manager: AnimationManager   |
| - facing: str                            |
| - mission_manager: MissionManager        |
| - sweep_cooldown, is_sweeping: float,bool|
| - clients_served, tacos_served, etc.     |
+------------------------------------------+
| + move(dx, dy)                           |
| + update(world_map, events)              |
| + draw(surface, camera, viewport_owner_id)|
| + check_collision_with(other)            |
| + get_distance_to(other)                 |
| + add_money(amount)                      |
| + modify_reputation(amount)              |
| + pickup_weapon(weapon)                  |
| + attack(target_pos)                    |
| + can_attack_client(client)             |
| + can_serve_dish(dish_name)              |
| + use_ingredients_for_dish(dish_name)    |
| + restock(ingredient_name)               |
| + can_sweep(), start_sweep()             |
| + can_steal_spit(other_player)           |
| + get_weapon_info()                      |
+------------------------------------------+
         | 1
         | has
         v *
    PlayerInventory, FoodStock, MissionManager,
    Equipment, MiniGame, ServeAnimation, AnimationManager
```

### Client (hérite de pygame.sprite.Sprite)

```
+------------------------------------------+
|    Client <<pygame.sprite.Sprite>>       |
+------------------------------------------+
| - image, base_image: Surface             |
| - mask: Mask                             |
| - rect: Rect                             |
| - zone, target_zone: str                  |
| - is_wanderer: bool                      |
| - speed: int                            |
| - dish: Dish                            |
| - state: str                            |
| - queue_tile_x, queue_tile_y: int | None |
| - outside_tile_x, outside_tile_y        |
| - is_first_in_queue: bool               |
| - spawn_time: float | None               |
| - patience: int                         |
| - death_animation: DeathAnimation | None |
| - flee_animation: FleeAnimation | None   |
| - fear_level: float                     |
+------------------------------------------+
| + update(world_map, game_state)          |
| + take_damage(damage, weapon_type)       |
| + scare(intensity)                       |
| + flee(direction)                       |
| + is_alive(): bool                      |
| + is_targetable(): bool                 |
| + draw(surface, camera)                 |
+------------------------------------------+
         | has 1
         v
       Dish
```

---

## 4. Package game — Plats et ingrédients

### Ingredient, Dish

```
+------------------------+       +------------------------+
|      Ingredient        |       |         Dish           |
+------------------------+       +------------------------+
| - name: str            |       | - name: str             |
| - type: str            |  *    | - base_ingredients: list|
| - is_dirty: bool       |------>| - added_ingredients:list|
| - effect: dict | None  |       +------------------------+
+------------------------+       | + add_ingredient(ing)   |
                                 | + is_valid(): bool     |
                                 | + get_quality_score() |
                                 +------------------------+
```

---

## 5. Package game — Inventaire et armes

### FoodStock, Weapon, PlayerInventory, WeaponSpawner

```
+------------------------+     +------------------------+
|      FoodStock         |     |        Weapon          |
+------------------------+     +------------------------+
| - restaurant_type: str |     | - weapon_type: str     |
| - ingredients: dict    |     | - x, y: int            |
| - has_spit: bool       |     | - zone: str            |
| - spit_stolen_until    |     | - picked_up: bool     |
| + use_ingredient(...)  |     | - damage, range        |
| + use_recipe(...)      |     | - rect: Rect           |
| + restock(...)         |     | + update(): bool       |
| + is_spit_available()  |     | + draw(surface, camera)|
| + steal_spit(duration)  |     +------------------------+
+------------------------+              ^
         ^                               |
         | 1                             | *
+------------------------+     +------------------------+
|   PlayerInventory      |     |    WeaponSpawner       |
+------------------------+     +------------------------+
| - player_id: int       |     | - weapons: list[Weapon]|
| - weapon: Weapon|None  |     | - spawn_interval      |
| - weapon_uses: int     |     | - last_spawn: float    |
| - max_weapon_uses: int |     | - spawn_points: dict   |
| + pickup_weapon(w)      |     | + update()             |
| + use_weapon()         |     | + spawn_weapon()      |
| + has_weapon(): bool   |     | + check_pickup(...)   |
| + get_weapon_info()    |     | + draw(...)            |
| + drop_weapon()        |     +------------------------+
+------------------------+
```

---

## 6. Package game — Carte et zones

### Zone et sous-classes, WorldMap, Map

```
+------------------------------------------+
|                 Zone                     |
+------------------------------------------+
| - name: str                              |
| - width, height: int                     |
| - bg_image_name: str | None              |
| - tiles: list[list]                     |
| - doors: list[tuple]                     |
| - walkable_area: list[Rect]              |
| - collision_rects: list[Rect]           |
| - use_pixel_collisions: bool             |
+------------------------------------------+
| + set_tile(x, y, tile_type)              |
| + add_door(x, y, target_zone, tx, ty)    |
| + set_walkable_rect(x, y, w, h)          |
| + set_collision_rects(rects)             |
| + is_walkable(x, y): bool                |
| + is_walkable_pixel(px, py, ...): bool   |
| + get_door_at(x, y)                      |
+------------------------------------------+
         ^
         | inherits
    +----+----+----+
    |         |    |
+---+---+  +--+--+  +--------+
| Tacos  |  |Kebab |  | Street |
|Restaurant| |Restaurant|  | (Zone)|
+--------+  +-------+  +--------+
```

```
+------------------------------------------+
|              WorldMap                    |
+------------------------------------------+
| - zones: dict[str, Zone]                 |
|   {"tacos", "kebab", "street"}           |
+------------------------------------------+
| + get_zone(name): Zone | None            |
| + draw_zone(zone, surface, camera)        |
+------------------------------------------+
         |
         | uses
         v
   Zone, TacosRestaurant, KebabRestaurant, Street
```

```
+------------------------------------------+
|                 Map                      |
+------------------------------------------+
| - world: WorldMap                        |
| - width, height: int                     |
| - tile_size: int                         |
+------------------------------------------+
| + draw(surface, camera, zone_name)       |
+------------------------------------------+
```

---

## 7. Package game — Équipement

### Equipment et sous-classes

```
+------------------------------------------+
|              Equipment                   |
+------------------------------------------+
| - name: str                              |
| - description: str                       |
| - broken: bool                           |
| - degraded: bool                         |
+------------------------------------------+
| + break_machine()                         |
| + repair()                               |
| + get_status(): str                      |
+------------------------------------------+
         ^
         | inherits
    +----+----+----+----+----+
    |    |    |    |    |
+---+  +--+  +-+  +--+  +-------+
|Fryer|  |Spit|  |Menu| |Register| |Toilets|
+-----+  +---+  +----+  +--------+  +-------+
| - cooking_time_multiplier | - get_quality_penalty() | - get_client_spawn_rate_penalty() | - get_money_loss_risk() | - get_inspection_risk()
| + get_multiplier()        |                       |                        |
+---------------------------+-----------------------+------------------------+
```

---

## 8. Package game — Animations

### Animation et sous-classes, AnimationManager

```
+------------------------------------------+
|              Animation                   |
+------------------------------------------+
| - duration: float                        |
| - loop: bool                             |
| - start_time: float                      |
| - completed: bool                        |
| - paused: bool                          |
+------------------------------------------+
| + update()                               |
| + pause(), resume(), reset()             |
+------------------------------------------+
         ^
         | inherits
    +----+----+----+----+----+----+----+----+----+----+
    |    |    |    |    |    |    |    |    |    |
SpriteAnim WalkAnim AttackAnim StealAnim DeathAnim FleeAnim PickupAnim FloatingText ServeAnim ThiefAnim
```

```
+------------------------------------------+
|           AnimationManager               |
+------------------------------------------+
| - animations: list[Animation]            |
| - floating_texts: list[FloatingText]    |
+------------------------------------------+
| + add_animation(animation)                |
| + add_floating_text(text, position, ...)|
| + update()                               |
| + draw(surface, camera)                  |
| + clear()                                |
+------------------------------------------+
```

---

## 9. Package game — Missions

### Mission, MissionManager

```
+------------------------------------------+
|               Mission                    |
+------------------------------------------+
| - id: str                                |
| - name: str                              |
| - description: str                       |
| - target: int                            |
| - progress: int                         |
| - reward_money, reward_reputation: int   |
| - mission_type: str                      |
| - completed: bool                        |
| - claimed: bool                          |
+------------------------------------------+
| + update_progress(amount)                |
| + get_progress_percent(): int            |
| + get_progress_text(): str               |
| + claim_reward(player)                   |
+------------------------------------------+
```

```
+------------------------------------------+
|           MissionManager                 |
+------------------------------------------+
| - player: Player                         |
| - active_missions: list[Mission]         |
| - completed_missions: list                |
| - current_streak: int                   |
+------------------------------------------+
| + update(mission_type, value)            |
| + claim_completed_missions()             |
| + _generate_initial_missions()            |
| + _mission_ok_for_player(mission_id)     |
+------------------------------------------+
         | uses
         v
     Mission, Player
```

---

## 10. Package game — Sabotages et événements

### Sabotage, SabotageManager

```
+------------------------------------------+
|              Sabotage                    |
+------------------------------------------+
| - name: str                              |
| - cost: int                              |
| - sabotage_type: str                     |
| - effect_func: Callable                  |
| - cooldown: float                        |
| - requires_proximity: bool               |
| - last_used: float                       |
+------------------------------------------+
| + can_execute(executor, target)          |
| + execute(executor, target)              |
+------------------------------------------+
```

```
+------------------------------------------+
|          SabotageManager                |
+------------------------------------------+
| - active_sabotages: list                 |
| - sabotage_history: list                 |
+------------------------------------------+
| + execute_sabotage(name, executor, target)|
| + get_available_sabotages(player)       |
+------------------------------------------+
```

### Event, EventManager

```
+------------------------+     +------------------------+
|        Event           |     |     EventManager        |
+------------------------+     +------------------------+
| - name: str             |     | - game_state: GameState |
| - description: str     |  *  | - active_events: list  |
| - start_time: float    |<----| - last_event_time      |
| - duration: float      |     | - event_interval       |
| - effect_func: Callable|     +------------------------+
| - active: bool         |     | + update()              |
+------------------------+     | + trigger_random_event()|
| + update()             |     +------------------------+
+------------------------+
```

---

## 11. Package game — Mini-jeu, historique, assets, audio

### MiniGame

```
+------------------------------------------+
|              MiniGame                    |
+------------------------------------------+
| - dish_name: str                         |
| - player_index: int                      |
| - active: bool                           |
| - start_time: float                      |
| - duration: float                       |
| - completed: bool                        |
| - success: bool                         |
| - required_keys: list                   |
| - current_step: int                     |
+------------------------------------------+
| + update(events)                         |
| + draw(surface, x, y)                    |
+------------------------------------------+
```

### GameHistory (Singleton)

```
+------------------------------------------+
|         GameHistory <<Singleton>>        |
+------------------------------------------+
| - history: list                          |
| - player_stats: dict                     |
| - _instance: ClassVar                   |
+------------------------------------------+
| + get(): GameHistory                     |
| + record_game(game_state)                |
| + get_recent_games(limit)                |
| + get_player_stats(name)                 |
| + get_leaderboard(sort_by)               |
| + clear_history()                        |
| - _load(), _save()                       |
+------------------------------------------+
```

### TMXCollisionLoader, Assets (Singleton)

```
+------------------------+     +------------------------------------------+
|  TMXCollisionLoader    |     |       Assets <<Singleton>>                |
+------------------------+     +------------------------------------------+
| (static)               |     | - images: dict                           |
| + load_collisions(...)  |     | - masks: dict                            |
+------------------------+     | - fonts: dict                            |
                                | - collision_maps: dict                  |
                                | - _instance: ClassVar                   |
                                +------------------------------------------+
                                | + get(): Assets                          |
                                | + load_images()                          |
                                | + get_image(name)                        |
                                | + get_mask(name)                         |
                                | + get_collisions(zone_name)              |
                                +------------------------------------------+
```

### AudioManager (Singleton)

```
+------------------------------------------+
|      AudioManager <<Singleton>>           |
+------------------------------------------+
| - enabled: bool                          |
| - sounds: dict                           |
| - channels: dict                         |
| - music_volume, sfx_volume: float        |
| - muted: bool                            |
+------------------------------------------+
| + get(): AudioManager                    |
| + play(sound_name, channel)              |
| + play_music(music_name)                 |
| + stop_music(), stop_all()               |
| + set_music_volume(v), set_sfx_volume(v) |
| + toggle_mute()                           |
| - _load_sounds(), _create_synthetic_sounds()|
| - _generate_sound(), _generate_chord()   |
+------------------------------------------+
```

---

## 12. Package input

### KeyBindings, InputHandler

```
+------------------------------------------+
|            KeyBindings                   |
+------------------------------------------+
| - bindings: dict                         |
| - config_path: str                       |
| - bundled_config_path: str               |
+------------------------------------------+
| + load()                                 |
| + save()                                 |
| + get_key(player, action)                |
| + set_key(player, action, key_code)      |
+------------------------------------------+
```

```
+------------------------------------------+
|           InputHandler                   |
+------------------------------------------+
| - last_action_time: dict                 |
| - action_cooldown: float                 |
| - key_bindings: KeyBindings             |
+------------------------------------------+
| + handle_input(players, events, blocked) |
| + check_inventory_key(event, player_idx) |
+------------------------------------------+
         | uses
         v
   KeyBindings, Player
```

---

## 13. Package rendering

### Camera

```
+------------------------------------------+
|               Camera                      |
+------------------------------------------+
| - camera_rect: Rect                      |
| - width, height: int                     |
| - x, y: int                              |
+------------------------------------------+
| + update(target, zone)                   |
+------------------------------------------+
```

### SplitScreenRenderer

```
+------------------------------------------+
|        SplitScreenRenderer               |
+------------------------------------------+
| - screen: Surface                        |
| - width, height: int                     |
| - surface1, surface2: Surface            |
| - camera1, camera2: Camera               |
| - mission_display: MissionDisplay        |
+------------------------------------------+
| + draw(game_state)                       |
| - _draw_hud(...)                         |
| - _draw_missions(...)                    |
+------------------------------------------+
```

### Menus (Inventory, Carte, Keybind, History, Tutorial)

```
+------------------------+     +------------------------+
|    InventoryMenu        |     |   PlayerInventoryMenu  |
+------------------------+     +------------------------+
| - screen: Surface      |  *  | - screen: Surface      |
| - player_menus: list   |---->| - player_idx: int      |
+------------------------+     | - visible: bool        |
| + visible (property)    |     | - current_tab: int     |
| + toggle(player_idx)   |     | + toggle()              |
| + close(player_idx)    |     | + draw(game_state)      |
| + handle_input(...)    |     | + handle_input(...)     |
| + draw(game_state)     |     +------------------------+
+------------------------+
```

```
+------------------------+     +------------------------+
|      CarteMenu          |     |   PlayerCarteMenu      |
+------------------------+     +------------------------+
| - screen: Surface      |  *  | - screen: Surface      |
| - player_menus: list   |---->| - player_idx: int      |
+------------------------+     | - visible: bool        |
| + visible (property)    |     | + toggle(), close()   |
| + toggle(player_idx)   |     | + draw(game_state)     |
| + draw(game_state)     |     | + handle_input(...)    |
+------------------------+     +------------------------+
```

```
+----------------------+  +----------------------+  +----------------------+
|    KeybindMenu       |  |    HistoryMenu      |  |   TutorialMenu       |
+----------------------+  +----------------------+  |   IntroCutscene      |
| - screen             |  | - screen            |  +----------------------+
| + draw()             |  | + draw()           |  | MissionDisplay        |
| + handle_input()     |  | + handle_input()   |  | MissionNotification   |
+----------------------+  +----------------------+  +----------------------+
```

### MenuRenderer

```
+------------------------------------------+
|           MenuRenderer                   |
+------------------------------------------+
| - screen: Surface                        |
| - menu_state: str                        |
| - selected_option: int                   |
| - player_configs: list                   |
| - video_capture, video_frame             |
| - particles: list                        |
+------------------------------------------+
| + draw_main_menu()                        |
| + draw_player_setup()                     |
| + draw_pause_menu()                       |
| + handle_input(events)                   |
+------------------------------------------+
```

---

## 14. Diagramme de relations global (résumé)

```
                    +------+
                    | Game |
                    +--+---+
                       |
     +-----------------+-----------------+
     |                 |                 |
     v                 v                 v
+---------+      +-----------+      +------------+
|GameState|      | Renderers |      | InputHandler|
+----+----+      +------------+      +------------+
     |                 |
     | 1               |
     |    +------------+------------+
     |    |            |            |
     v    v            v            v
+----+  +-----+   SplitScreen  MenuRenderer  InventoryMenu
|WorldMap  |Player|   Camera    CarteMenu   KeybindMenu
+----+  +--+--+   MissionDisplay  etc.
     |     |
     |     | 1
     v     v
+--------+ +-------------+
| Zone   | |PlayerInventory|
| Tacos  | |FoodStock     |
| Kebab  | |MissionManager|
| Street | |AnimationMgr  |
+--------+ +-------------+
     |
     | *
     v
+--------+     +--------+
| Client |---->| Dish   |
+--------+     +--------+
     |
     v
+---------+   +----------+   +-----------+
| MiniGame|   | Weapon   |   | Sabotage  |
+---------+   +----------+   +-----------+
                  ^
                  |
            WeaponSpawner
```

---

## 15. Légende

| Symbole / convention     | Signification                    |
|--------------------------|----------------------------------|
| `Class <<stereotype>>`  | Classe avec stéréotype (ex: Singleton) |
| `|` entre sections        | Séparateur attributs / méthodes  |
| `^` avec `inherits`     | Héritage (enfant → parent)      |
| `*` à côté d’un type    | Liste ou multiplicité « plusieurs » |
| `| None`                 | Type optionnel                  |
| `--->`                   | Association / utilisation       |

---

*Généré pour le projet SnackAnarchy — jeu de gestion de fast-food en multijoueur local.*
