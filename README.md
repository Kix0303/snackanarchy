# SnackAnarchy

**SnackAnarchy** est un jeu de gestion de fast-food compétitif en écran partagé. Deux joueurs s'affrontent localement pour devenir le meilleur restaurateur de la rue !

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat&logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.5+-green?style=flat)

---

## Concept

Dans **SnackAnarchy**, chaque joueur gère son propre restaurant :
- **Joueur 1** : Restaurant **Tacos**
- **Joueur 2** : Restaurant **Kebab**

Le but ? **Gagner le plus d'argent** avant la fin du temps imparti en servant des clients... et en sabotant discrètement son adversaire.

### Fonctionnalités principales

- **Écran partagé** : Deux joueurs sur le même écran
- **Système de réputation** : Plus votre réputation est haute, plus les clients viennent chez vous
- **Mini-jeu de préparation** : Réussissez la séquence de touches pour servir vos clients
- **Sabotages** : Lancez des rumeurs, cassez l'équipement adverse, volez la broche...
- **Armes** : Ramassez couteaux et fourchettes pour "décourager" les clients de l'adversaire
- **Gestion de stock** : Surveillez vos ingrédients et réapprovisionnez-vous à temps
- **Touches personnalisables** : Configurez vos contrôles depuis le menu

---

## Captures d'écran

### Menu principal

![Menu principal](demo/demo1.png)

### Configuration des joueurs

![Configuration](demo/demo2.png)

### Gameplay - Les deux restaurants

![Gameplay restaurants](demo/demo3.png)

### Gameplay - La rue et les clients

![Gameplay rue](demo/demo4.png)

---

## Installation

### Téléchargement des releases

Rendez-vous sur la page **[Actions](https://github.com/Kix0303/snackanarchy/actions)** du dépôt pour télécharger les exécutables pré-compilés (artifacts).

| Plateforme | Fichier | Description |
|------------|---------|-------------|
| **Windows** | `SnackAnarchy-Setup.exe` | Installateur avec raccourcis Bureau et Menu Démarrer |
| **Windows** | `SnackAnarchy-Windows-Portable.zip` | Version portable (décompresser et lancer) |
| **macOS** | `SnackAnarchy.dmg` | Image disque à glisser dans Applications |
| **Linux** | `SnackAnarchy-Linux.tar.gz` | Archive à extraire |

### Instructions par plateforme

#### Windows

**Installateur :**
1. Lancer `SnackAnarchy-Setup.exe`
2. Choisir le dossier d'installation
3. Le jeu est accessible depuis le Bureau ou le Menu Démarrer

**Portable :**
1. Décompresser `SnackAnarchy-Windows-Portable.zip`
2. Lancer `SnackAnarchy.exe` depuis le dossier

#### macOS

1. Ouvrir `SnackAnarchy.dmg`
2. Glisser **SnackAnarchy.app** vers **Applications**
3. Si macOS affiche "application endommagée" :
   - **Option A** : Clic droit → **Ouvrir** → confirmer
   - **Option B** : Dans Terminal : `xattr -cr /Applications/SnackAnarchy.app`

> L'application n'est pas signée avec un certificat Apple Developer (signature ad-hoc), d'où l'avertissement.

#### Linux

1. Installer les dépendances système :
   ```bash
   sudo apt-get install libsdl2-2.0-0 libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 \
       libsdl2-ttf-2.0-0 libasound2 libportmidi0
   ```
2. Extraire l'archive :
   ```bash
   tar -xzvf SnackAnarchy-Linux.tar.gz
   ```
3. Lancer le jeu :
   ```bash
   ./SnackAnarchy
   ```

---

## Lancer depuis les sources

### Prérequis

- Python 3.11+
- pip

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/snackanarchy.git
cd snackanarchy

# Installer les dépendances
pip install -r requirements.txt

# Lancer le jeu
python main.py
```

### Dépendances

```
pygame>=2.5.0
opencv-python>=4.8.0
numpy>=1.24.0
```

---

## Contrôles

Les contrôles sont entièrement personnalisables depuis le menu **Touches**.

### Touches par défaut

| Action | Joueur 1 | Joueur 2 |
|--------|----------|----------|
| Haut | `W` / `Z` | `↑` |
| Bas | `S` / `Q` | `↓` |
| Gauche | `A` / `S` | `←` |
| Droite | `D` | `→` |
| Servir | `E` | `Entrée` |
| Attaque | `Q` / `M` | `L` / `R-CTRL` |
| Sabotage | `R` | `Retour` |
| Inventaire | `I` | `V` / `\` |
| Pause | `Échap` | `Échap` |

> Les touches entre parenthèses varient selon le clavier (AZERTY/QWERTY).

### Mini-jeu de préparation

Quand vous servez un client, un mini-jeu apparaît :
- Appuyez sur **A → S → D → F** dans l'ordre avant la fin du temps
- Réussite = client servi + argent + réputation
- Échec = le client reste (vous pouvez réessayer)

---

## Gameplay

### Objectif

À la fin du temps imparti (3, 5 ou 10 minutes selon le mode), le joueur avec le **plus d'argent** gagne.

### Servir les clients

1. Des clients apparaissent dans la rue et se dirigent vers un restaurant
2. Plus votre **réputation** est haute, plus ils viennent chez vous
3. Approchez-vous d'un client dans votre restaurant et appuyez sur **Servir**
4. Réussissez le mini-jeu (A-S-D-F) pour gagner de l'argent (+20€) et de la réputation (+2%)

### Réputation

- **Départ** : 50% pour chaque joueur
- **+2%** : Client servi avec succès
- **-1%** : Client parti (trop d'attente)
- **-5%** : Client tué dans votre propre restaurant
- Les sabotages peuvent faire baisser la réputation de l'adversaire

### Armes

Des armes (couteaux, fourchettes) apparaissent périodiquement sur la carte :
- Ramassez-les automatiquement en passant dessus
- Appuyez sur **Attaque** pour frapper un client à proximité
- **Tactique** : Tuez les clients dans le restaurant adverse pour faire baisser sa réputation !

### Sabotages

Utilisez votre argent pour saboter l'adversaire :

| Sabotage | Coût | Effet |
|----------|------|-------|
| Casse Friteuse | 50€ | Casse l'équipement adverse |
| Lancer Rumeur | 30€ | -15% réputation adverse |
| Falsifier Carte | 40€ | Perturbe les commandes |
| Contrôle Hygiène | 80€ | -5% réputation + inspection |
| Voler la Broche | 60€ | Vole la broche kebab (30s) |
| Empoisonner Stock | 70€ | -10% réputation + stock réduit |

### Gestion du stock

Surveillez vos ingrédients dans l'inventaire :
- **Tacos** : galette, viande, sauce fromagère, frites, sel
- **Kebab** : pain pita, viande kebab, salade, tomates, oignons, sauce blanche

Si un ingrédient manque, vous ne pouvez plus servir !

---

## Structure du projet

```
snackanarchy/
├── main.py                 # Point d'entrée
├── config.py               # Configuration globale
├── requirements.txt        # Dépendances Python
├── keybindings.json        # Configuration des touches
├── assets/                 # Ressources graphiques et audio
│   ├── *.png               # Sprites et images
│   ├── *.tmx               # Cartes Tiled
│   └── *.wav               # Effets sonores et musique
├── game/                   # Logique de jeu
│   ├── state.py            # État global du jeu
│   ├── player.py           # Classe Joueur
│   ├── client.py           # Classe Client
│   ├── inventory.py        # Inventaire et stock
│   ├── sabotage.py         # Système de sabotage
│   ├── minigames.py        # Mini-jeux
│   └── ...
├── rendering/              # Affichage
│   ├── split_screen.py     # Rendu écran partagé
│   ├── menu.py             # Menus du jeu
│   └── ...
└── input/                  # Gestion des entrées
    └── controls.py         # Contrôles et touches
```

---

## Compilation

Le projet utilise **GitHub Actions** pour compiler automatiquement les exécutables.

**Accéder aux builds** : [https://github.com/Kix0303/snackanarchy/actions](https://github.com/Kix0303/snackanarchy/actions)

Le workflow se déclenche :
- À chaque push sur `main`
- À chaque pull request
- Manuellement via **Actions → Build executables → Run workflow**

### Compiler localement

```bash
pip install pyinstaller

# Windows
pyinstaller main.py --name SnackAnarchy --onefile --noconsole --collect-all cv2

# macOS
pyinstaller main.py --name SnackAnarchy --windowed --collect-all cv2

# Linux
pyinstaller main.py --name SnackAnarchy --onefile --collect-all cv2

# Copier les assets
cp -r assets dist/assets
cp keybindings.json dist/
```

---

## Crédits

- **Moteur** : [Pygame](https://www.pygame.org/)
- **Vision** : [OpenCV](https://opencv.org/)
