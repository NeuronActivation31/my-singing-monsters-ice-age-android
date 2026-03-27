import pygame
import math
import random
import struct
import wave
import os
import io
import json
import time
import ctypes
import urllib.request
import threading
import subprocess
import tempfile
import shutil
import sys

# ============ UPDATE SYSTEM ============
GAME_VERSION = "1.1"
# Change this URL to point to your version.json file (hosted online)
# Examples:
#   GitHub raw:   "https://raw.githubusercontent.com/USER/REPO/main/version.json"
#   Dropbox:      "https://dl.dropboxusercontent.com/s/xxx/version.json"
#   Your server:  "https://yoursite.com/game/version.json"
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/NeuronActivation31/my-singing-monsters/master/version.json"
update_available = False
update_info = None
update_checking = False
update_downloading = False
update_progress = 0
update_error = None
update_download_url = None

# Prevent multiple instances
mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "MySingingMonstersIceAgeMutex")
if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    ctypes.windll.user32.MessageBoxW(0, "Game is already running!", "My Singing Monsters", 0)
    exit()

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
fullscreen = False
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Singing Monsters - Ice Age")
game_surface = pygame.Surface((WIDTH, HEIGHT))

# Colors
SKY_TOP = (135, 206, 250)
SKY_BOTTOM = (176, 224, 230)
WATER = (64, 164, 223)
WATER_DARK = (40, 120, 180)
GRASS = (80, 180, 60)
GRASS_DARK = (50, 140, 40)
DIRT = (139, 90, 43)
SUN = (255, 223, 0)
CLOUD = (255, 255, 255)
TREE_GREEN = (34, 139, 34)
TREE_TRUNK = (101, 67, 33)

# Monster colors
MONSTER_BODY = (147, 112, 219)
MONSTER_BODY_DARK = (120, 80, 180)
MONSTER_EYE = (255, 255, 255)
MONSTER_PUPIL = (30, 30, 30)
MONSTER_MOUTH = (220, 80, 80)
MONSTER_FEET = (100, 70, 150)

# UI colors
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SHADOW = (50, 50, 50)

# Menu colors (Ice Age theme)
MENU_BG_TOP = (10, 20, 50)
MENU_BG_BOTTOM = (30, 50, 90)
ICE_LIGHT = (180, 220, 255)
ICE_BLUE = (100, 180, 255)
ICE_DARK = (50, 120, 200)
FROST_WHITE = (220, 240, 255)
SNOW = (240, 248, 255)
BUTTON_NORMAL = (40, 80, 140)
BUTTON_HOVER = (60, 120, 200)
BUTTON_PRESS = (80, 160, 240)
TEXT_GLOW = (150, 200, 255)
AURORA_1 = (50, 200, 150)
AURORA_2 = (100, 150, 255)
AURORA_3 = (180, 100, 255)

# Generate a simple sound
def generate_sound(frequency, duration=0.3):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            value = int(16000 * (
                0.5 * math.sin(2 * math.pi * frequency * t) +
                0.3 * math.sin(2 * math.pi * frequency * 1.5 * t) +
                0.2 * math.sin(2 * math.pi * frequency * 2 * t)
            ) * max(0, 1 - t / duration))
            wav_file.writeframes(struct.pack('<h', max(-32768, min(32767, value))))
    buf.seek(0)
    return pygame.mixer.Sound(buf)

# Generate click sound for buttons
def generate_click():
    sample_rate = 44100
    duration = 0.15
    n_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 800 - (t / duration) * 400
            value = int(12000 * math.sin(2 * math.pi * freq * t) * (1 - t / duration))
            wav_file.writeframes(struct.pack('<h', max(-32768, min(32767, value))))
    buf.seek(0)
    return pygame.mixer.Sound(buf)

sounds = [
    generate_sound(300, 0.4),
    generate_sound(400, 0.3),
    generate_sound(250, 0.5),
    generate_sound(350, 0.35),
]
click_sound = generate_click()

# Fonts
font_title = pygame.font.SysFont("Arial", 64, bold=True)
font_large = pygame.font.SysFont("Arial", 48, bold=True)
font_medium = pygame.font.SysFont("Arial", 36, bold=True)
font_small = pygame.font.SysFont("Arial", 24)
font_tiny = pygame.font.SysFont("Arial", 18)

# Game state
coins = 0
score = 0
clock = pygame.time.Clock()
volume = 0.7
last_save_time = time.time()
SAVE_FILE = os.path.join(os.path.expanduser("~"), "Documents", "My Singing Monsters", "save.json")

def save_game():
    global last_save_time
    # Save bred monsters (skip the original 4)
    baby_monsters = []
    for i in range(4, len(monsters)):
        m = monsters[i]
        baby_monsters.append({
            "x": m.x,
            "y": m.y,
            "color": m.color,
            "color_dark": m.color_dark,
            "sound_index": m.sound_index,
            "name": m.name,
            "size": m.size
        })
    data = {
        "coins": coins,
        "score": score,
        "volume": volume,
        "language": current_lang,
        "fullscreen": fullscreen,
        "upgrades": upgrades,
        "baby_monsters": baby_monsters,
    }
    try:
        os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
        last_save_time = time.time()
    except Exception as e:
        print(f"Save error: {e}")

def load_game():
    global coins, score, volume, current_lang, fullscreen, upgrades, monsters
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            coins = data.get("coins", 0)
            score = data.get("score", 0)
            volume = data.get("volume", 0.7)
            current_lang = data.get("language", "en")
            fullscreen = data.get("fullscreen", False)
            saved_upgrades = data.get("upgrades", {})
            for key in upgrades:
                if key in saved_upgrades:
                    upgrades[key] = saved_upgrades[key]
            # Load baby monsters
            saved_babies = data.get("baby_monsters", [])
            for baby_data in saved_babies:
                baby = Monster(
                    baby_data["x"],
                    baby_data["y"],
                    tuple(baby_data["color"]),
                    tuple(baby_data["color_dark"]),
                    baby_data["sound_index"],
                    baby_data["name"]
                )
                baby.size = baby_data.get("size", 0.6)
                monsters.append(baby)
            return True
    except Exception as e:
        print(f"Load error: {e}")
    return False

def check_for_updates():
    global update_available, update_info, update_checking, update_error, update_download_url
    if not UPDATE_CHECK_URL:
        update_error = "no_url"
        update_checking = False
        return
    try:
        update_checking = True
        update_error = None
        req = urllib.request.Request(UPDATE_CHECK_URL, headers={"User-Agent": f"MySingingMonsters/{GAME_VERSION}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        remote_version = data.get("version", "0")
        if remote_version > GAME_VERSION:
            update_available = True
            update_info = data
            update_download_url = data.get("download_url", "")
        else:
            update_available = False
    except Exception as e:
        update_error = str(e)
        print(f"Update check failed: {e}")
    finally:
        update_checking = False

def download_update():
    global update_downloading, update_progress, update_error
    if not update_download_url:
        update_error = "no_download_url"
        return
    try:
        update_downloading = True
        update_progress = 0
        update_error = None
        # Determine what to download and where to save
        game_dir = os.path.dirname(os.path.abspath(__file__))
        is_exe = getattr(sys, 'frozen', False)
        if is_exe:
            # Running as .exe - download new exe
            target_file = os.path.join(game_dir, "My Singing Monsters_new.exe")
            restart_file = os.path.join(game_dir, "My Singing Monsters.exe")
        else:
            # Running as .py - download new game.py
            target_file = os.path.join(game_dir, "game_new.py")
            restart_file = os.path.join(game_dir, "game.py")
        # Download with progress
        req = urllib.request.Request(update_download_url, headers={"User-Agent": f"MySingingMonsters/{GAME_VERSION}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(target_file, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        update_progress = downloaded / total_size
        # Create updater script to replace file after game exits
        updater_script = os.path.join(tempfile.gettempdir(), "msm_updater.bat")
        with open(updater_script, "w") as f:
            f.write("@echo off\n")
            f.write("timeout /t 2 /nobreak >nul\n")
            f.write(f'copy /Y "{target_file}" "{restart_file}"\n')
            f.write(f'del "{target_file}"\n')
            f.write(f'start "" "{restart_file}"\n')
            f.write("del \"%~f0\"\n")
        # Launch updater and quit
        subprocess.Popen(["cmd", "/c", updater_script], creationflags=subprocess.CREATE_NO_WINDOW)
        pygame.quit()
        os._exit(0)
    except Exception as e:
        update_error = str(e)
        print(f"Update download failed: {e}")
    finally:
        update_downloading = False

def start_update_check():
    if not UPDATE_CHECK_URL or update_checking:
        return
    t = threading.Thread(target=check_for_updates, daemon=True)
    t.start()

def start_update_download():
    if update_downloading:
        return
    t = threading.Thread(target=download_update, daemon=True)
    t.start()

# Languages
current_lang = "en"

# Upgrades
upgrades = {
    "orange_top_hat": False,
    "dockyard": False,
    "breeding_structure": False,
}

# Breeding system
breeding_selected = [None, None]  # Two selected monster indices
breeding_result = None  # Result monster data after breeding
breeding_timer = 0  # Countdown for breeding animation
breeding_babies = []  # List of baby monsters spawned on island
breeding_cost = 75  # Cost to breed

# Monster color combinations for breeding results
breeding_combinations = {
    ("purple", "orange"): ((200, 130, 220), (160, 100, 180), "violet"),
    ("purple", "green"): ((100, 160, 200), (70, 120, 160), "teal"),
    ("purple", "pink"): ((180, 100, 180), (140, 70, 140), "magenta"),
    ("orange", "green"): ((150, 180, 80), (120, 140, 60), "lime"),
    ("orange", "pink"): ((255, 135, 130), (200, 100, 100), "coral"),
    ("green", "pink"): ((130, 155, 160), (100, 120, 130), "mint"),
}

translations = {
    "en": {
        "title_line1": "MY SINGING",
        "title_line2": "MONSTERS",
        "subtitle": "~ Ice Age ~",
        "play": "Play",
        "settings": "Settings",
        "credits": "Credits",
        "quit": "Quit",
        "back": "Back",
        "volume": "Volume",
        "vol_hint": "Click the volume slider to test sound!",
        "score": "Score",
        "menu": "Menu",
        "instruction": "Click the monsters to make music!",
        "languages": "Languages",
        "fullscreen": "Fullscreen",
        "shop": "Shop",
        "top_hat": "Top Hat",
        "top_hat_desc": "Give the orange blob a fancy top hat!",
        "dockyard": "Dockyard",
        "dockyard_desc": "Build a dockyard on your island!",
        "bought": "Owned",
        "buy": "Buy",
        "not_enough": "Not enough coins!",
        "check_updates": "Check for Updates",
        "update_available": "Update Available!",
        "update_version": "Version {ver} is ready!",
        "update_download": "Download Update",
        "update_checking": "Checking for updates...",
        "update_downloading": "Downloading update... {pct}%",
        "update_latest": "You have the latest version!",
        "update_error": "Could not check for updates",
        "update_no_url": "Update URL not configured",
        "credits_lines": [
            ("Game Design & Programming", "You & opencode"),
            ("Art", "Pygame shapes"),
            ("Music & Sounds", "Generated with Python"),
            ("Engine", "Pygame 2.6"),
            ("Language", "Python 3.11"),
            ("Inspired by", "My Singing Monsters"),
        ],
    },
    "bs": {
        "breeding": "Razmnozavanje",
        "breeding_structure": "Struktura razmnozavanja",
        "breeding_structure_desc": "Razmnozavaj cudovista da napravis nova!",
        "breed": "Razmnozi",
        "breeding_select": "Odaberite dva cudovista!",
        "breeding_baby": "Rodilo se novo cudoviste!",
        "breeding_busy": "Razmnozavanje u toku...",
        "breeding_cost": "Cijena: 75 novcica",
        "breeding_select_first": "Roditelj 1",
        "breeding_select_second": "Roditelj 2",
        "title_line1": "MOJE PJEUVAJUCE",
        "title_line2": "CUDOVISTA",
        "subtitle": "~ Ledeno Doba ~",
        "play": "Igraj",
        "settings": "Podesavanja",
        "credits": "Zasluge",
        "quit": "Izadji",
        "back": "Nazad",
        "volume": "Jacina zvuka",
        "vol_hint": "Klizac jacine zvuka za testiranje!",
        "score": "Rezultat",
        "menu": "Meni",
        "instruction": "Kliknite cudovista da pravite muziku!",
        "languages": "Jezici",
        "dockyard": "Pristanište",
        "dockyard_desc": "Izgradi pristanište na svom ostrvu!",
        "check_updates": "Provjeri azuriranja",
        "update_available": "Azuriranje dostupno!",
        "update_version": "Verzija {ver} je spremna!",
        "update_download": "Preuzmi azuriranje",
        "update_checking": "Provjerava azuriranja...",
        "update_downloading": "Preuzima azuriranje... {pct}%",
        "update_latest": "Imate najnoviju verziju!",
        "update_error": "Nije moguce provjeriti azuriranja",
        "update_no_url": "URL azuriranja nije konfigurisan",
        "credits_lines": [
            ("Dizajn i programiranje", "Vi i opencode"),
            ("Umjetnost", "Pygame oblici"),
            ("Muzika i zvukovi", "Generisano Pythonom"),
            ("Motor", "Pygame 2.6"),
            ("Jezik", "Python 3.11"),
            ("Inspirisano", "My Singing Monsters"),
        ],
    },
    "sv": {
        "breeding": "Avel",
        "breeding_structure": "Avelstruktur",
        "breeding_structure_desc": "Avel monster for att skapa nya!",
        "breed": "Avel",
        "breeding_select": "Valja tva monster!",
        "breeding_baby": "Ett nytt monster fodd!",
        "breeding_busy": "Avel pa gar...",
        "breeding_cost": "Kostnad: 75 mynt",
        "breeding_select_first": "Foralder 1",
        "breeding_select_second": "Foralder 2",
        "title_line1": "MINA SJUNGANDE",
        "title_line2": "MONSTER",
        "subtitle": "~ Istid ~",
        "play": "Spela",
        "settings": "Installningar",
        "credits": "Credits",
        "quit": "Avsluta",
        "back": "Tillbaka",
        "volume": "Volym",
        "vol_hint": "Klicka pa volymreglaget for att testa ljudet!",
        "score": "Poang",
        "menu": "Meny",
        "instruction": "Klicka pa monster for att gora musik!",
        "languages": "Sprak",
        "dockyard": "Varv",
        "dockyard_desc": "Bygg ett varv pa din o!",
        "check_updates": "Sok efter uppdateringar",
        "update_available": "Uppdatering tillganglig!",
        "update_version": "Version {ver} ar klar!",
        "update_download": "Ladda ner uppdatering",
        "update_checking": "Soker efter uppdateringar...",
        "update_downloading": "Laddar ner uppdatering... {pct}%",
        "update_latest": "Du har den senaste versionen!",
        "update_error": "Kunde inte soka efter uppdateringar",
        "update_no_url": "Uppdaterings-URL inte konfigurerad",
        "credits_lines": [
            ("Speldesign & programmering", "Du & opencode"),
            ("Konst", "Pygame-former"),
            ("Musik & ljud", "Genererat med Python"),
            ("Motor", "Pygame 2.6"),
            ("Sprak", "Python 3.11"),
            ("Inspirerat av", "My Singing Monsters"),
        ],
    },
    "pt": {
        "breeding": "Criacao",
        "breeding_structure": "Estrutura de criacao",
        "breeding_structure_desc": "Crie monstros para criar novos!",
        "breed": "Criar",
        "breeding_select": "Selecione dois monstros!",
        "breeding_baby": "Um novo monstro nasceu!",
        "breeding_busy": "Criacao em andamento...",
        "breeding_cost": "Custo: 75 moedas",
        "breeding_select_first": "Pai 1",
        "breeding_select_second": "Pai 2",
        "title_line1": "MEUS MONSTROS",
        "title_line2": "CANTORES",
        "subtitle": "~ Era do Gelo ~",
        "play": "Jogar",
        "settings": "Configuracoes",
        "credits": "Creditos",
        "quit": "Sair",
        "back": "Voltar",
        "volume": "Volume",
        "vol_hint": "Clique no controle deslizante para testar o som!",
        "score": "Pontuacao",
        "menu": "Menu",
        "instruction": "Clique nos monstros para fazer musica!",
        "languages": "Idiomas",
        "dockyard": "Estaleiro",
        "dockyard_desc": "Construa um estaleiro na sua ilha!",
        "check_updates": "Verificar atualizacoes",
        "update_available": "Atualizacao disponivel!",
        "update_version": "Versao {ver} esta pronta!",
        "update_download": "Baixar atualizacao",
        "update_checking": "Verificando atualizacoes...",
        "update_downloading": "Baixando atualizacao... {pct}%",
        "update_latest": "Voce tem a versao mais recente!",
        "update_error": "Nao foi possivel verificar atualizacoes",
        "update_no_url": "URL de atualizacao nao configurada",
        "credits_lines": [
            ("Design e programacao", "Voce e opencode"),
            ("Arte", "Formas Pygame"),
            ("Musica e sons", "Gerado com Python"),
            ("Motor", "Pygame 2.6"),
            ("Linguagem", "Python 3.11"),
            ("Inspirado em", "My Singing Monsters"),
        ],
    },
    "ja": {
        "breeding": "Shushoku",
        "breeding_structure": "Shushoku shisetsu",
        "breeding_structure_desc": "Monsutaa o shushoku shite atarashii!",
        "breed": "Shushoku",
        "breeding_select": "Futari no monsutaa o sentaku!",
        "breeding_baby": "Atarashii monsutaa ga umaremashita!",
        "breeding_busy": "Shushoku chu...",
        "breeding_cost": "Hiyo: 75 koin",
        "breeding_select_first": "Oya 1",
        "breeding_select_second": "Oya 2",
        "title_line1": "MY SINGING",
        "title_line2": "MONSTERS",
        "subtitle": "~ Hyoga Jidai ~",
        "play": "Purei",
        "settings": "Settei",
        "credits": "Kurejitto",
        "quit": "Shuryo",
        "back": "Modoru",
        "volume": "Ongaku",
        "vol_hint": "Barisuraidaa o kurikku shite saundo o tamesu!",
        "score": "Sukoa",
        "menu": "Menyuu",
        "instruction": "Monsutaa o kurikku shite ongaku o tsukuru!",
        "languages": "Gengo",
        "dockyard": "Dokku",
        "dockyard_desc": "Shima ni dokku o tsukuru!",
        "check_updates": "Koushin wo kensaku",
        "update_available": "Koushin ga kanou desu!",
        "update_version": "Ban {ver} ga junbi dekimasu!",
        "update_download": "Koushin wo dounrui",
        "update_checking": "Koushin wo kensaku chu...",
        "update_downloading": "Koushin wo dounrui chu... {pct}%",
        "update_latest": "Saishin ban wo motte imasu!",
        "update_error": "Koushin wo kensaku dekimasen",
        "update_no_url": "Koushin URL ga settei sarete imasen",
        "credits_lines": [
            ("Geemu dezain puroguramingu", "Anata & opencode"),
            ("Aato", "Pygame katachi"),
            ("Ongaku to saundo", "Python de seisei"),
            ("Enjin", "Pygame 2.6"),
            ("Gengo", "Python 3.11"),
            ("Kangaerareta", "My Singing Monsters"),
        ],
    },
    "bg": {
        "breeding": "Razhdatane",
        "breeding_structure": "Struktura za razhdatane",
        "breeding_structure_desc": "Razhdai chudovishta za da suzdadesh novi!",
        "breed": "Razhdai",
        "breeding_select": "Izberete dve chudovishta!",
        "breeding_baby": "Novo chudovishte se rodi!",
        "breeding_busy": "Razhdatane v protses...",
        "breeding_cost": "Tsena: 75 moneti",
        "breeding_select_first": "Roditel 1",
        "breeding_select_second": "Roditel 2",
        "title_line1": "MOITE PEUESHTI",
        "title_line2": "CHUDOVISHTA",
        "subtitle": "~ Ledena Epoha ~",
        "play": "Igrai",
        "settings": "Nastroyki",
        "credits": "Zaslugi",
        "quit": "Izhod",
        "back": "Nazad",
        "volume": "Silenost",
        "vol_hint": "Kliknete pluzgacha za zvuk!",
        "score": "Rezultat",
        "menu": "Menyu",
        "instruction": "Kliknete chudovishtata za muzika!",
        "languages": "Ezitsi",
        "dockyard": "Pristanishte",
        "dockyard_desc": "Postroyte pristanishte na ostrova si!",
        "check_updates": "Proveri za obnovyavaniya",
        "update_available": "Obnovyavane na raspolozhenie!",
        "update_version": "Versiya {ver} e gotova!",
        "update_download": "Iztegli obnovyavane",
        "update_checking": "Proveryava za obnovyavaniya...",
        "update_downloading": "Izteglya obnovyavane... {pct}%",
        "update_latest": "Imate poslednata versiya!",
        "update_error": "Ne mozhe da se proveri za obnovyavaniya",
        "update_no_url": "URL za obnovyavane ne e konfiguriran",
        "credits_lines": [
            ("Dizayn i programirane", "Vi i opencode"),
            ("Izkustvo", "Pygame figuri"),
            ("Muzika i zvutsi", "Generirani s Python"),
            ("Dvigatel", "Pygame 2.6"),
            ("Ezik", "Python 3.11"),
            ("Vdahnoveni ot", "My Singing Monsters"),
        ],
    },
    "de": {
        "breeding": "Zucht",
        "breeding_structure": "Zuchtgebaude",
        "breeding_structure_desc": "Zuchte Monster um neue zu erschaffen!",
        "breed": "Zuchten",
        "breeding_select": "Wahle zwei Monster!",
        "breeding_baby": "Ein neues Monster wurde geboren!",
        "breeding_busy": "Zucht lauft...",
        "breeding_cost": "Kosten: 75 Munzen",
        "breeding_select_first": "Elternteil 1",
        "breeding_select_second": "Elternteil 2",
        "title_line1": "MEINE SINGENDEN",
        "title_line2": "MONSTER",
        "subtitle": "~ Eiszeit ~",
        "play": "Spielen",
        "settings": "Einstellungen",
        "credits": "Credits",
        "quit": "Beenden",
        "back": "Zuruck",
        "volume": "Lautstarke",
        "vol_hint": "Klicke den Lautstarkeregler zum Testen!",
        "score": "Punkte",
        "menu": "Menu",
        "instruction": "Klicke die Monster um Musik zu machen!",
        "languages": "Sprachen",
        "dockyard": "Werft",
        "dockyard_desc": "Baue eine Werft auf deiner Insel!",
        "check_updates": "Nach Updates suchen",
        "update_available": "Update verfugbar!",
        "update_version": "Version {ver} ist bereit!",
        "update_download": "Update herunterladen",
        "update_checking": "Suche nach Updates...",
        "update_downloading": "Lade Update herunter... {pct}%",
        "update_latest": "Du hast die neueste Version!",
        "update_error": "Konnte nicht nach Updates suchen",
        "update_no_url": "Update-URL nicht konfiguriert",
        "credits_lines": [
            ("Spieldesign & Programmierung", "Du & opencode"),
            ("Kunst", "Pygame-Formen"),
            ("Musik & Sounds", "Mit Python generiert"),
            ("Engine", "Pygame 2.6"),
            ("Sprache", "Python 3.11"),
            ("Inspiriert von", "My Singing Monsters"),
        ],
    },
    "hr": {
        "breeding": "Razmnozavanje",
        "breeding_structure": "Struktura razmnozavanja",
        "breeding_structure_desc": "Razmnožavaj cudovišta da stvoriš nova!",
        "breed": "Razmnozi",
        "breeding_select": "Odaberite dva cudovišta!",
        "breeding_baby": "Novo cudovište se rodilo!",
        "breeding_busy": "Razmnozavanje u tijeku...",
        "breeding_cost": "Cijena: 75 novcica",
        "breeding_select_first": "Roditelj 1",
        "breeding_select_second": "Roditelj 2",
        "title_line1": "MOJI PJEUVAJUCI",
        "title_line2": "CUDOVISTA",
        "subtitle": "~ Ledeno Doba ~",
        "play": "Igraj",
        "settings": "Postavke",
        "credits": "Zasluge",
        "quit": "Izlaz",
        "back": "Natrag",
        "volume": "Glasnoca",
        "vol_hint": "Kliknite klizac za zvuk!",
        "score": "Rezultat",
        "menu": "Izbornik",
        "instruction": "Kliknite cudovista za glazbu!",
        "languages": "Jezici",
        "fullscreen": "Cijeli zaslon",
        "dockyard": "Brodogradilište",
        "dockyard_desc": "Izgradi brodogradilište na svom otoku!",
        "check_updates": "Provjeri azuriranja",
        "update_available": "Azuriranje dostupno!",
        "update_version": "Verzija {ver} je spremna!",
        "update_download": "Preuzmi azuriranje",
        "update_checking": "Provjerava azuriranja...",
        "update_downloading": "Preuzima azuriranje... {pct}%",
        "update_latest": "Imate najnoviju verziju!",
        "update_error": "Nije moguce provjeriti azuriranja",
        "update_no_url": "URL azuriranja nije konfiguriran",
        "credits_lines": [
            ("Dizajn i programiranje", "Vi i opencode"),
            ("Umjetnost", "Pygame oblici"),
            ("Glazba i zvukovi", "Generirano Pythonom"),
            ("Motor", "Pygame 2.6"),
            ("Jezik", "Python 3.11"),
            ("Inspirirano", "My Singing Monsters"),
        ],
    },
    "ro": {
        "breeding": "Reproducere",
        "breeding_structure": "Structura de reproducere",
        "breeding_structure_desc": "Reproduceti monstri pentru a crea noi!",
        "breed": "Reproduce",
        "breeding_select": "Selectati doi monstri!",
        "breeding_baby": "Un nou monstru s-a nascut!",
        "breeding_busy": "Reproducere in curs...",
        "breeding_cost": "Cost: 75 monede",
        "breeding_select_first": "Parinte 1",
        "breeding_select_second": "Parinte 2",
        "title_line1": "MONSTRII MEI",
        "title_line2": "CANTARETI",
        "subtitle": "~ Era Glaciara ~",
        "play": "Joaca",
        "settings": "Setari",
        "credits": "Credite",
        "quit": "Iesire",
        "back": "Inapoi",
        "volume": "Volum",
        "vol_hint": "Faceti clic pe cursor pentru a testa sunetul!",
        "score": "Scor",
        "menu": "Meniu",
        "instruction": "Faceti clic pe monstri pentru a face muzica!",
        "languages": "Limbi",
        "fullscreen": "Ecran complet",
        "dockyard": "Santier naval",
        "dockyard_desc": "Construieste un santier naval pe insula ta!",
        "check_updates": "Verifica actualizarile",
        "update_available": "Actualizare disponibila!",
        "update_version": "Versiunea {ver} este gata!",
        "update_download": "Descarca actualizarea",
        "update_checking": "Se verifica actualizarile...",
        "update_downloading": "Se descarca actualizarea... {pct}%",
        "update_latest": "Aveti cea mai recenta versiune!",
        "update_error": "Nu s-au putut verifica actualizarile",
        "update_no_url": "URL-ul de actualizare nu este configurat",
        "credits_lines": [
            ("Design si programare", "Dvs. si opencode"),
            ("Arta", "Forme Pygame"),
            ("Muzica si sunete", "Generate cu Python"),
            ("Motor", "Pygame 2.6"),
            ("Limba", "Python 3.11"),
            ("Inspirat de", "My Singing Monsters"),
        ],
    },
    "es": {
        "breeding": "Criar",
        "breeding_structure": "Estructura de cria",
        "breeding_structure_desc": "Cria monstruos para crear nuevos!",
        "breed": "Criar",
        "breeding_select": "Selecciona dos monstruos!",
        "breeding_baby": "Un nuevo monstruo nacio!",
        "breeding_busy": "Cria en progreso...",
        "breeding_cost": "Costo: 75 monedas",
        "breeding_select_first": "Padre 1",
        "breeding_select_second": "Padre 2",
        "title_line1": "MIS MONSTRUOS",
        "title_line2": "CANTANTES",
        "subtitle": "~ Edad de Hielo ~",
        "play": "Jugar",
        "settings": "Ajustes",
        "credits": "Creditos",
        "quit": "Salir",
        "back": "Volver",
        "volume": "Volumen",
        "vol_hint": "Haz clic en el control para probar el sonido!",
        "score": "Puntuacion",
        "menu": "Menu",
        "instruction": "Haz clic en los monstruos para hacer musica!",
        "languages": "Idiomas",
        "fullscreen": "Pantalla completa",
        "dockyard": "Astillero",
        "dockyard_desc": "¡Construye un astillero en tu isla!",
        "check_updates": "Buscar actualizaciones",
        "update_available": "¡Actualizacion disponible!",
        "update_version": "¡La version {ver} esta lista!",
        "update_download": "Descargar actualizacion",
        "update_checking": "Buscando actualizaciones...",
        "update_downloading": "Descargando actualizacion... {pct}%",
        "update_latest": "¡Tienes la ultima version!",
        "update_error": "No se pudieron buscar actualizaciones",
        "update_no_url": "URL de actualizacion no configurada",
        "credits_lines": [
            ("Diseno y programacion", "Tu y opencode"),
            ("Arte", "Formas Pygame"),
            ("Musica y sonidos", "Generado con Python"),
            ("Motor", "Pygame 2.6"),
            ("Lenguaje", "Python 3.11"),
            ("Inspirado en", "My Singing Monsters"),
        ],
    },
    "udm": {
        "breeding": "Vyltem",
        "breeding_structure": "Vyltem korpus",
        "breeding_structure_desc": "Monsterjos vyltem gur!",
        "breed": "Vyltem",
        "breeding_select": "Kyk monsterjos kyshken!",
        "breeding_baby": "Novyi monster borez!",
        "breeding_busy": "Vyltem ike...",
        "breeding_cost": "Tsyn: 75 monet",
        "breeding_select_first": "Vyltem 1",
        "breeding_select_second": "Vyltem 2",
        "title_line1": "MY SINGING",
        "title_line2": "MONSTERS",
        "subtitle": "~ Yul Dyr ~",
        "play": "Badya",
        "settings": "Otkatnom",
        "credits": "Credits",
        "quit": "Ketshy",
        "back": "Tol",
        "volume": "Kuch",
        "vol_hint": "Slydy vylym tshy kyshken bur!",
        "score": "Es",
        "menu": "Menyu",
        "instruction": "Monsterjos tshy kyshken gur!",
        "languages": "Kyl",
        "fullscreen": "Punas ekran",
        "dockyard": "Dockyard",
        "dockyard_desc": "Dockyard ostryg shoryos!",
        "check_updates": "Obnovlenie kysky",
        "update_available": "Obnovlenie val!",
        "update_version": "Versia {ver} gotov!",
        "update_download": "Obnovlenie skachivat",
        "update_checking": "Obnovlenie kysky...",
        "update_downloading": "Obnovlenie skachivat... {pct}%",
        "update_latest": "Sochni versia val!",
        "update_error": "Obnovlenie kysky nemona",
        "update_no_url": "Obnovlenie URL konfiguratsia uon",
        "credits_lines": [
            ("Dizayn da programirovanie", "Ty da opencode"),
            ("Iskusstvo", "Pygame formaos"),
            ("Myzyk da shoryos", "Python-yz"),
            ("Dvigatel", "Pygame 2.6"),
            ("Kyl", "Python 3.11"),
            ("Istshetko", "My Singing Monsters"),
        ],
    },
}

def t(key):
    return translations[current_lang].get(key, translations["en"].get(key, key))

# Flag drawing functions (small 30x20 flags)
def draw_flag(surface, x, y, code):
    w, h = 30, 20
    flag_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (0, 0, 0), flag_rect, 1)

    if code == "en":  # UK simplified
        pygame.draw.rect(surface, (0, 36, 125), flag_rect)
        pygame.draw.line(surface, WHITE, (x, y), (x + w, y + h), 3)
        pygame.draw.line(surface, WHITE, (x + w, y), (x, y + h), 3)
        pygame.draw.line(surface, (206, 17, 38), (x, y), (x + w, y + h), 1)
        pygame.draw.line(surface, (206, 17, 38), (x + w, y), (x, y + h), 1)
        pygame.draw.rect(surface, WHITE, (x + w//2 - 2, y, 4, h))
        pygame.draw.rect(surface, WHITE, (x, y + h//2 - 2, w, 4))
        pygame.draw.rect(surface, (206, 17, 38), (x + w//2 - 1, y, 2, h))
        pygame.draw.rect(surface, (206, 17, 38), (x, y + h//2 - 1, w, 2))
    elif code == "bs":  # Bosnia - blue with yellow right triangle
        pygame.draw.rect(surface, (0, 114, 198), flag_rect)
        # Yellow triangle: top-left corner to middle-right to bottom-left
        pygame.draw.polygon(surface, (255, 205, 0), [(x, y), (x + w * 5 // 10, y + h), (x, y + h)])
    elif code == "sv":  # Sweden - blue with yellow cross
        pygame.draw.rect(surface, (0, 106, 167), flag_rect)
        pygame.draw.rect(surface, (254, 204, 0), (x + 8, y, 5, h))
        pygame.draw.rect(surface, (254, 204, 0), (x, y + 7, w, 5))
    elif code == "pt":  # Brazil - green with yellow diamond
        pygame.draw.rect(surface, (0, 156, 59), flag_rect)
        pygame.draw.polygon(surface, (255, 223, 0), [(x + w//2, y + 2), (x + w - 3, y + h//2), (x + w//2, y + h - 2), (x + 3, y + h//2)])
        pygame.draw.circle(surface, (0, 39, 118), (x + w//2, y + h//2), 5)
        pygame.draw.line(surface, WHITE, (x + w//2 - 4, y + h//2), (x + w//2 + 4, y + h//2), 1)
    elif code == "ja":  # Japan - white with red circle
        pygame.draw.rect(surface, WHITE, flag_rect)
        pygame.draw.circle(surface, (188, 0, 45), (x + w//2, y + h//2), 7)
    elif code == "bg":  # Bulgaria - white, green, red
        pygame.draw.rect(surface, WHITE, (x, y, w, h//3))
        pygame.draw.rect(surface, (0, 150, 110), (x, y + h//3, w, h//3))
        pygame.draw.rect(surface, (214, 38, 18), (x, y + 2*h//3, w, h//3 + 1))
    elif code == "de":  # Germany - black, red, gold
        pygame.draw.rect(surface, (0, 0, 0), (x, y, w, h//3))
        pygame.draw.rect(surface, (221, 0, 0), (x, y + h//3, w, h//3))
        pygame.draw.rect(surface, (255, 206, 0), (x, y + 2*h//3, w, h//3 + 1))
    elif code == "hr":  # Croatia - red, white, blue with checkerboard
        pygame.draw.rect(surface, (255, 0, 0), (x, y, w, h//3))
        pygame.draw.rect(surface, WHITE, (x, y + h//3, w, h//3))
        pygame.draw.rect(surface, (0, 0, 147), (x, y + 2*h//3, w, h//3 + 1))
        # Mini checkerboard in center
        for cx in range(3):
            for cy in range(3):
                if (cx + cy) % 2 == 0:
                    pygame.draw.rect(surface, (255, 0, 0), (x + 11 + cx*3, y + 6 + cy*3, 3, 3))
                else:
                    pygame.draw.rect(surface, WHITE, (x + 11 + cx*3, y + 6 + cy*3, 3, 3))
    elif code == "ro":  # Romania - blue, yellow, red vertical
        pygame.draw.rect(surface, (0, 43, 127), (x, y, w//3, h))
        pygame.draw.rect(surface, (252, 209, 22), (x + w//3, y, w//3, h))
        pygame.draw.rect(surface, (206, 17, 38), (x + 2*w//3, y, w//3 + 1, h))
    elif code == "es":  # Spain - red, yellow, red
        pygame.draw.rect(surface, (198, 11, 30), (x, y, w, h//4))
        pygame.draw.rect(surface, (255, 196, 0), (x, y + h//4, w, h//2))
        pygame.draw.rect(surface, (198, 11, 30), (x, y + 3*h//4, w, h//4 + 1))
    elif code == "udm":  # Udmurt - red, black, white horizontal
        pygame.draw.rect(surface, (200, 30, 30), (x, y, w, h//3))
        pygame.draw.rect(surface, (0, 0, 0), (x, y + h//3, w, h//3))
        pygame.draw.rect(surface, WHITE, (x, y + 2*h//3, w, h//3 + 1))
        # Red circle symbol
        pygame.draw.circle(surface, (200, 30, 30), (x + w//2, y + h//2), 4)

# States
STATE_MENU = "menu"
STATE_PLAY = "play"
STATE_SETTINGS = "settings"
STATE_CREDITS = "credits"
STATE_LANGUAGES = "languages"
STATE_SHOP = "shop"
STATE_BREEDING = "breeding"
STATE_UPDATES = "updates"
current_state = STATE_MENU

# Fade transition
fade_alpha = 255
fade_speed = 5
fade_target = 0

# Menu particles (snowflake effect)
class Snowflake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(-20, -5)
        self.speed = random.uniform(1, 3)
        self.size = random.randint(2, 8)
        self.life = 1.0
        self.color_choice = random.choice([ICE_LIGHT, FROST_WHITE, SNOW, (200, 230, 255)])
        self.wobble = random.uniform(-1.5, 1.5)
        self.wobble_speed = random.uniform(0.02, 0.06)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-2, 2)

    def update(self):
        self.y += self.speed
        self.x += math.sin(self.y * self.wobble_speed) * self.wobble
        self.rotation += self.rot_speed
        if self.y > HEIGHT + 10:
            self.reset()

    def draw(self, surface):
        alpha = int(200 * self.life)
        color = (*self.color_choice[:3], alpha)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        # Draw snowflake as a 6-pointed star
        cx, cy = self.size, self.size
        for i in range(6):
            angle = math.radians(self.rotation + i * 60)
            ex = cx + math.cos(angle) * self.size
            ey = cy + math.sin(angle) * self.size
            pygame.draw.line(s, color, (cx, cy), (ex, ey), 1)
        pygame.draw.circle(s, color, (cx, cy), max(1, self.size // 3))
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

snowflakes = [Snowflake() for _ in range(100)]

# Menu floating monsters (decorative)
class MenuMonster:
    def __init__(self, x, y, color, color_dark, scale=0.6):
        self.x = x
        self.y = y
        self.base_y = y
        self.color = color
        self.color_dark = color_dark
        self.scale = scale
        self.bounce = random.uniform(0, 6.28)

    def update(self):
        self.bounce += 0.03
        self.y = self.base_y + math.sin(self.bounce) * 8

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        s = self.scale
        # Simple monster silhouette
        pygame.draw.ellipse(surface, self.color, (x - 30*s, y - 25*s, 60*s, 50*s))
        pygame.draw.ellipse(surface, self.color_dark, (x - 30*s, y - 25*s, 60*s, 50*s), 2)
        # Eyes
        pygame.draw.circle(surface, WHITE, (int(x - 10*s), int(y - 8*s)), int(8*s))
        pygame.draw.circle(surface, WHITE, (int(x + 10*s), int(y - 8*s)), int(8*s))
        pygame.draw.circle(surface, BLACK, (int(x - 8*s), int(y - 6*s)), int(4*s))
        pygame.draw.circle(surface, BLACK, (int(x + 12*s), int(y - 6*s)), int(4*s))
        # Horns
        pygame.draw.polygon(surface, self.color_dark, [
            (x - 18*s, y - 25*s), (x - 25*s, y - 45*s), (x - 10*s, y - 28*s)
        ])
        pygame.draw.polygon(surface, self.color_dark, [
            (x + 18*s, y - 25*s), (x + 25*s, y - 45*s), (x + 10*s, y - 28*s)
        ])

menu_monsters = [
    MenuMonster(120, 520, (147, 112, 219), (120, 80, 180), 0.7),
    MenuMonster(680, 510, (255, 165, 0), (200, 130, 0), 0.65),
    MenuMonster(250, 540, (50, 205, 50), (30, 160, 30), 0.55),
    MenuMonster(550, 530, (255, 105, 180), (200, 70, 140), 0.6),
]

# Button class
class Button:
    def __init__(self, x, y, w, h, text, font=font_medium):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.hovered = False
        self.pressed = False
        self.scale = 1.0

    def update(self, mouse_pos, mouse_pressed):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.pressed = self.hovered and mouse_pressed
        target = 1.05 if self.hovered else 1.0
        self.scale += (target - self.scale) * 0.2

    def draw(self, surface):
        # Scale animation
        w = int(self.rect.width * self.scale)
        h = int(self.rect.height * self.scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        scaled_rect = pygame.Rect(x, y, w, h)

        # Glow effect
        if self.hovered:
            glow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*TEXT_GLOW, 60), (0, 0, w + 20, h + 20), border_radius=18)
            surface.blit(glow, (x - 10, y - 10))

        # Button background
        color = BUTTON_PRESS if self.pressed else (BUTTON_HOVER if self.hovered else BUTTON_NORMAL)
        pygame.draw.rect(surface, color, scaled_rect, border_radius=15)
        pygame.draw.rect(surface, GOLD if self.hovered else (180, 140, 255), scaled_rect, 3, border_radius=15)

        # Text
        text_surf = self.font.render(self.text, True, GOLD if self.hovered else WHITE)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.hovered

# Create menu buttons
btn_play = Button(WIDTH//2 - 120, 280, 240, 55, t("play"))
btn_settings = Button(WIDTH//2 - 120, 355, 240, 55, t("settings"))
btn_credits = Button(WIDTH//2 - 120, 430, 240, 55, t("credits"))
btn_quit = Button(WIDTH//2 - 120, 505, 240, 55, t("quit"))

btn_back = Button(30, 30, 120, 45, t("back"), font_small)
btn_languages = Button(650, 30, 120, 45, t("languages"), font_small)
btn_fullscreen = Button(WIDTH//2 - 120, 380, 240, 55, t("fullscreen"))
btn_updates = Button(WIDTH//2 - 120, 455, 240, 55, t("check_updates"), font_small)
btn_update_download = Button(WIDTH//2 - 130, 380, 260, 55, t("update_download"), font_small)

# Language selection buttons
lang_codes = ["en", "bs", "sv", "pt", "ja", "bg", "de", "hr", "ro", "es", "udm"]
lang_names = ["English", "Bosnian", "Svenska", "Portugues", "Nihongo", "Bulgarski", "Deutsch", "Hrvatski", "Romana", "Espanol", "Udmurt"]
lang_buttons = []
for i, (code, name) in enumerate(zip(lang_codes, lang_names)):
    row = i // 2
    col = i % 2
    x = WIDTH//2 - 150 + col * 200
    y = 140 + row * 55
    lang_buttons.append((code, Button(x, y, 150, 44, name, font_tiny)))

# Settings sliders
vol_slider_rect = pygame.Rect(WIDTH//2 - 150, 250, 300, 20)
vol_handle_x = WIDTH//2 - 150 + int(volume * 300)
dragging_volume = False

# Lava ground for menu
def draw_menu_background(surface):
    # Gradient background
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(MENU_BG_TOP[0] + (MENU_BG_BOTTOM[0] - MENU_BG_TOP[0]) * ratio)
        g = int(MENU_BG_TOP[1] + (MENU_BG_BOTTOM[1] - MENU_BG_TOP[1]) * ratio)
        b = int(MENU_BG_TOP[2] + (MENU_BG_BOTTOM[2] - MENU_BG_TOP[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

    # Frozen ground at bottom
    ice_surf = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
    for x in range(0, WIDTH, 4):
        wave_h = math.sin((x + pygame.time.get_ticks() * 0.001) * 0.03) * 10
        h = int(100 + wave_h)
        color_lerp = random.choice([0.3, 0.5, 0.7, 1.0])
        r = int(ICE_DARK[0] * color_lerp + ICE_LIGHT[0] * (1 - color_lerp))
        g = int(ICE_DARK[1] * color_lerp + ICE_LIGHT[1] * (1 - color_lerp))
        b = int(ICE_DARK[2] * color_lerp + ICE_LIGHT[2] * (1 - color_lerp))
        pygame.draw.rect(ice_surf, (r, g, b, 220), (x, HEIGHT - h, 5, h))
    surface.blit(ice_surf, (0, 0))

    # Ice blocks
    for i in range(7):
        x = 50 + i * 120
        y = HEIGHT - 50 + math.sin(i * 1.2) * 8
        points = [
            (x - 25, y + 15),
            (x - 18, y - 15),
            (x - 5, y - 25),
            (x + 8, y - 20),
            (x + 22, y - 8),
            (x + 25, y + 15),
        ]
        pygame.draw.polygon(surface, (120, 180, 230), points)
        pygame.draw.polygon(surface, ICE_LIGHT, points, 2)
        # Ice shine
        pygame.draw.line(surface, (200, 240, 255), (x - 10, y - 10), (x - 5, y - 20), 2)

def draw_menu(surface):
    draw_menu_background(surface)

    # Snowflakes
    for p in snowflakes:
        p.update()
        p.draw(surface)

    # Decorative monsters
    for m in menu_monsters:
        m.update()
        m.draw(surface)

    # Title with glow effect
    time = pygame.time.get_ticks() * 0.001
    glow_intensity = int(100 + math.sin(time * 2) * 50)

    # Title glow
    glow_surf = font_title.render(t("title_line1"), True, ICE_LIGHT)
    glow_surf.set_alpha(glow_intensity)
    for offset in [(3, 3), (-3, -3), (3, -3), (-3, 3), (0, 4), (0, -4), (4, 0), (-4, 0)]:
        surface.blit(glow_surf, (WIDTH//2 - glow_surf.get_width()//2 + offset[0], 80 + offset[1]))

    # Title text
    title = font_title.render(t("title_line1"), True, FROST_WHITE)
    surface.blit(title, (WIDTH//2 - title.get_width()//2, 75))
    title2 = font_title.render(t("title_line2"), True, FROST_WHITE)
    surface.blit(title2, (WIDTH//2 - title2.get_width()//2, 140))

    # Subtitle
    subtitle = font_small.render(t("subtitle"), True, ICE_BLUE)
    surface.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 210))

    # Version
    version = font_tiny.render(f"v{GAME_VERSION}", True, (100, 150, 200))
    surface.blit(version, (WIDTH - 50, HEIGHT - 25))

def draw_settings(surface):
    draw_menu_background(surface)
    for p in snowflakes[:40]:
        p.update()
        p.draw(surface)

    # Title
    title = font_large.render(t("settings").upper(), True, FROST_WHITE)
    surface.blit(title, (WIDTH//2 - title.get_width()//2, 100))

    # Volume section
    vol_label = font_medium.render(t("volume"), True, WHITE)
    surface.blit(vol_label, (WIDTH//2 - vol_label.get_width()//2, 200))

    # Slider track
    pygame.draw.rect(surface, (30, 50, 80), vol_slider_rect, border_radius=10)
    pygame.draw.rect(surface, ICE_BLUE, vol_slider_rect, 2, border_radius=10)

    # Filled portion
    filled_rect = pygame.Rect(vol_slider_rect.x, vol_slider_rect.y, vol_handle_x - vol_slider_rect.x, 20)
    pygame.draw.rect(surface, ICE_LIGHT, filled_rect, border_radius=10)

    # Handle
    pygame.draw.circle(surface, FROST_WHITE, (vol_handle_x, vol_slider_rect.centery), 14)
    pygame.draw.circle(surface, ICE_BLUE, (vol_handle_x, vol_slider_rect.centery), 14, 2)

    # Volume percentage
    vol_pct = font_small.render(f"{int(volume * 100)}%", True, WHITE)
    surface.blit(vol_pct, (WIDTH//2 - vol_pct.get_width()//2, 290))

    # Sound test button
    test_label = font_small.render(t("vol_hint"), True, (150, 200, 240))
    surface.blit(test_label, (WIDTH//2 - test_label.get_width()//2, 340))

    # Fullscreen button
    btn_fullscreen.text = t("fullscreen") + (" ON" if fullscreen else " OFF")
    btn_fullscreen.draw(surface)

    # Update check button
    btn_updates.draw(surface)
    # Show update notification dot if update available
    if update_available:
        pygame.draw.circle(surface, (255, 80, 80), (btn_updates.rect.right - 10, btn_updates.rect.top + 10), 6)

    # Back button
    btn_back.draw(surface)

def draw_credits(surface):
    draw_menu_background(surface)
    for p in snowflakes[:40]:
        p.update()
        p.draw(surface)

    # Title
    title = font_large.render(t("credits").upper(), True, FROST_WHITE)
    surface.blit(title, (WIDTH//2 - title.get_width()//2, 100))

    credits_lines = t("credits_lines")

    y = 180
    for label, value in credits_lines:
        label_surf = font_tiny.render(label, True, (150, 200, 240))
        value_surf = font_small.render(value, True, WHITE)
        surface.blit(label_surf, (WIDTH//2 - 150, y))
        surface.blit(value_surf, (WIDTH//2 + 20, y))
        y += 45

    # Back button
    btn_back.draw(surface)

# Cloud positions
clouds = [
    {"x": 100, "y": 60, "speed": 0.3, "size": 1.0},
    {"x": 400, "y": 40, "speed": 0.2, "size": 0.8},
    {"x": 650, "y": 80, "speed": 0.25, "size": 1.2},
]

# Monster class
class Monster:
    def __init__(self, x, y, color, color_dark, sound_index, name=""):
        self.x = x
        self.y = y
        self.base_y = y
        self.color = color
        self.color_dark = color_dark
        self.sound_index = sound_index
        self.name = name
        self.bounce = 0
        self.bounce_speed = 0
        self.is_bouncing = False
        self.size = 1.0
        self.click_cooldown = 0

    def update(self):
        self.bounce += 0.05
        idle_offset = math.sin(self.bounce) * 3
        self.y = self.base_y + idle_offset

        if self.is_bouncing:
            self.bounce_speed += 0.5
            self.y -= self.bounce_speed
            if self.bounce_speed > 15:
                self.is_bouncing = False
                self.bounce_speed = 0

        if self.click_cooldown > 0:
            self.click_cooldown -= 1

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        s = self.size

        # Shadow
        pygame.draw.ellipse(surface, (0, 0, 0, 50), (x - 30*s, y + 35*s, 60*s, 15*s))

        # Feet
        pygame.draw.ellipse(surface, MONSTER_FEET, (x - 25*s, y + 20*s, 18*s, 12*s))
        pygame.draw.ellipse(surface, MONSTER_FEET, (x + 7*s, y + 20*s, 18*s, 12*s))

        # Body
        pygame.draw.ellipse(surface, self.color, (x - 35*s, y - 30*s, 70*s, 60*s))
        pygame.draw.ellipse(surface, self.color_dark, (x - 35*s, y - 30*s, 70*s, 60*s), 3)

        # Belly
        pygame.draw.ellipse(surface, (200, 180, 255), (x - 18*s, y - 5*s, 36*s, 30*s))

        # Eyes
        pygame.draw.ellipse(surface, MONSTER_EYE, (x - 22*s, y - 22*s, 20*s, 22*s))
        pygame.draw.circle(surface, MONSTER_PUPIL, (int(x - 12*s), int(y - 12*s)), int(6*s))
        pygame.draw.circle(surface, WHITE, (int(x - 9*s), int(y - 15*s)), int(2*s))

        pygame.draw.ellipse(surface, MONSTER_EYE, (x + 2*s, y - 22*s, 20*s, 22*s))
        pygame.draw.circle(surface, MONSTER_PUPIL, (int(x + 12*s), int(y - 12*s)), int(6*s))
        pygame.draw.circle(surface, WHITE, (int(x + 15*s), int(y - 15*s)), int(2*s))

        # Mouth (open when clicked, smile otherwise)
        if self.is_bouncing or self.click_cooldown > 10:
            # Open mouth (oval)
            pygame.draw.ellipse(surface, MONSTER_MOUTH, (x - 14*s, y + 0*s, 28*s, 20*s))
            pygame.draw.ellipse(surface, (80, 20, 20), (x - 10*s, y + 4*s, 20*s, 12*s))
            # Tongue
            pygame.draw.ellipse(surface, (255, 120, 120), (x - 6*s, y + 10*s, 12*s, 8*s))
        else:
            # Smile
            pygame.draw.arc(surface, MONSTER_MOUTH, (x - 12*s, y + 2*s, 24*s, 14*s), 3.14, 6.28, 3)

        # Horns
        pygame.draw.polygon(surface, self.color_dark, [
            (x - 20*s, y - 30*s), (x - 28*s, y - 50*s), (x - 12*s, y - 35*s),
        ])
        pygame.draw.polygon(surface, self.color_dark, [
            (x + 20*s, y - 30*s), (x + 28*s, y - 50*s), (x + 12*s, y - 35*s),
        ])
        pygame.draw.circle(surface, (255, 180, 255), (int(x - 28*s), int(y - 50*s)), int(5*s))
        pygame.draw.circle(surface, (255, 180, 255), (int(x + 28*s), int(y - 50*s)), int(5*s))

        # Top hat for orange blob
        if self.name == "orange" and upgrades.get("orange_top_hat", False):
            # Hat brim
            pygame.draw.ellipse(surface, (30, 30, 30), (x - 22*s, y - 52*s, 44*s, 10*s))
            # Hat body
            pygame.draw.rect(surface, (30, 30, 30), (x - 15*s, y - 85*s, 30*s, 35*s))
            pygame.draw.rect(surface, (50, 50, 50), (x - 15*s, y - 85*s, 30*s, 35*s), 2)
            # Hat band
            pygame.draw.rect(surface, (180, 50, 50), (x - 15*s, y - 58*s, 30*s, 6*s))
            # Hat top
            pygame.draw.ellipse(surface, (30, 30, 30), (x - 15*s, y - 88*s, 30*s, 8*s))

    def is_clicked(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return math.sqrt(dx*dx + dy*dy) < 40 * self.size

    def on_click(self):
        if self.click_cooldown <= 0:
            self.is_bouncing = True
            self.bounce_speed = -5
            sounds[self.sound_index].set_volume(volume)
            sounds[self.sound_index].play()
            self.click_cooldown = 20
            return True
        return False

# Create monsters
monsters = [
    Monster(200, 380, (147, 112, 219), (120, 80, 180), 0, "purple"),
    Monster(400, 400, (255, 165, 0), (200, 130, 0), 1, "orange"),
    Monster(580, 370, (50, 205, 50), (30, 160, 30), 2, "green"),
    Monster(350, 450, (255, 105, 180), (200, 70, 140), 3, "pink"),
]

def draw_sky(surface):
    for y in range(0, 250):
        ratio = y / 250
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * ratio)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * ratio)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

def draw_sun(surface):
    pygame.draw.circle(surface, SUN, (680, 80), 50)
    for i in range(12):
        angle = i * 30 * math.pi / 180
        x1 = 680 + math.cos(angle) * 55
        y1 = 80 + math.sin(angle) * 55
        x2 = 680 + math.cos(angle) * 75
        y2 = 80 + math.sin(angle) * 75
        pygame.draw.line(surface, SUN, (x1, y1), (x2, y2), 4)

def draw_cloud(surface, x, y, size=1.0):
    s = size
    pygame.draw.circle(surface, CLOUD, (int(x), int(y)), int(25*s))
    pygame.draw.circle(surface, CLOUD, (int(x - 20*s), int(y + 5*s)), int(20*s))
    pygame.draw.circle(surface, CLOUD, (int(x + 20*s), int(y + 5*s)), int(20*s))
    pygame.draw.circle(surface, CLOUD, (int(x - 10*s), int(y - 10*s)), int(18*s))
    pygame.draw.circle(surface, CLOUD, (int(x + 10*s), int(y - 10*s)), int(18*s))

def draw_island(surface):
    for y in range(250, HEIGHT):
        ratio = (y - 250) / (HEIGHT - 250)
        r = int(WATER[0] + (WATER_DARK[0] - WATER[0]) * ratio)
        g = int(WATER[1] + (WATER_DARK[1] - WATER[1]) * ratio)
        b = int(WATER[2] + (WATER_DARK[2] - WATER[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

    for i in range(5):
        y = 280 + i * 50
        for x in range(0, WIDTH, 40):
            offset = math.sin((x + pygame.time.get_ticks() * 0.001) * 0.05) * 5
            pygame.draw.arc(surface, (100, 200, 255), (x, y + offset, 40, 15), 3.14, 6.28, 2)

    pygame.draw.ellipse(surface, DIRT, (50, 300, 700, 250))
    pygame.draw.ellipse(surface, GRASS, (60, 290, 680, 180))
    pygame.draw.ellipse(surface, GRASS_DARK, (60, 290, 680, 180), 3)

    # Draw house in the middle back
    draw_house(surface, 400, 310)

    # Draw dockyard if purchased
    if upgrades.get("dockyard", False):
        draw_dockyard(surface, 100, 380)

    # Draw breeding structure if purchased
    if upgrades.get("breeding_structure", False):
        draw_breeding_structure(surface, 620, 350)

def draw_house(surface, x, y):
    # House base
    pygame.draw.rect(surface, (180, 120, 80), (x - 45, y - 30, 90, 55))
    pygame.draw.rect(surface, (140, 90, 60), (x - 45, y - 30, 90, 55), 3)

    # Roof
    pygame.draw.polygon(surface, (160, 50, 30), [
        (x - 55, y - 30), (x, y - 75), (x + 55, y - 30)
    ])
    pygame.draw.polygon(surface, (120, 35, 20), [
        (x - 55, y - 30), (x, y - 75), (x + 55, y - 30)
    ], 3)

    # Door
    pygame.draw.rect(surface, (100, 60, 30), (x - 10, y, 20, 25))
    pygame.draw.rect(surface, (70, 40, 20), (x - 10, y, 20, 25), 2)
    pygame.draw.circle(surface, (255, 215, 0), (x + 6, y + 13), 3)

    # Windows
    pygame.draw.rect(surface, (150, 200, 255), (x - 35, y - 18, 18, 18))
    pygame.draw.rect(surface, (100, 50, 20), (x - 35, y - 18, 18, 18), 2)
    pygame.draw.line(surface, (100, 50, 20), (x - 26, y - 18), (x - 26, y), 2)
    pygame.draw.line(surface, (100, 50, 20), (x - 35, y - 9), (x - 17, y - 9), 2)

    pygame.draw.rect(surface, (150, 200, 255), (x + 17, y - 18, 18, 18))
    pygame.draw.rect(surface, (100, 50, 20), (x + 17, y - 18, 18, 18), 2)
    pygame.draw.line(surface, (100, 50, 20), (x + 26, y - 18), (x + 26, y), 2)
    pygame.draw.line(surface, (100, 50, 20), (x + 17, y - 9), (x + 35, y - 9), 2)

    # Chimney
    pygame.draw.rect(surface, (120, 60, 40), (x + 25, y - 70, 15, 25))
    pygame.draw.rect(surface, (80, 40, 25), (x + 25, y - 70, 15, 25), 2)

    # Shop sign
    sign_bg = pygame.Surface((60, 18), pygame.SRCALPHA)
    pygame.draw.rect(sign_bg, (50, 30, 10, 200), (0, 0, 60, 18), border_radius=5)
    surface.blit(sign_bg, (x - 30, y - 55))
    shop_text = font_tiny.render(t("shop"), True, GOLD)
    surface.blit(shop_text, (x - shop_text.get_width()//2, y - 54))

def draw_dockyard(surface, x, y):
    # Wooden posts
    for i in range(4):
        px = x - 30 + i * 25
        pygame.draw.rect(surface, (120, 80, 40), (px, y - 5, 8, 50))
        pygame.draw.rect(surface, (90, 60, 30), (px, y - 5, 8, 50), 2)

    # Dock platform
    pygame.draw.rect(surface, (160, 110, 60), (x - 35, y, 95, 15))
    pygame.draw.rect(surface, (120, 80, 40), (x - 35, y, 95, 15), 2)

    # Planks
    for i in range(5):
        px = x - 33 + i * 20
        pygame.draw.line(surface, (100, 70, 35), (px, y + 2), (px, y + 13), 1)

    # Small boat
    boat_x = x - 10
    boat_y = y + 30
    # Hull
    pygame.draw.polygon(surface, (140, 90, 50), [
        (boat_x - 20, boat_y), (boat_x - 15, boat_y + 15),
        (boat_x + 25, boat_y + 15), (boat_x + 30, boat_y)
    ])
    pygame.draw.polygon(surface, (100, 65, 35), [
        (boat_x - 20, boat_y), (boat_x - 15, boat_y + 15),
        (boat_x + 25, boat_y + 15), (boat_x + 30, boat_y)
    ], 2)
    # Mast
    pygame.draw.line(surface, (100, 70, 35), (boat_x + 5, boat_y), (boat_x + 5, boat_y - 30), 2)
    # Sail
    pygame.draw.polygon(surface, WHITE, [
        (boat_x + 5, boat_y - 28), (boat_x + 20, boat_y - 15), (boat_x + 5, boat_y - 8)
    ])
    pygame.draw.polygon(surface, (200, 200, 200), [
        (boat_x + 5, boat_y - 28), (boat_x + 20, boat_y - 15), (boat_x + 5, boat_y - 8)
    ], 1)

    # Barrel on dock
    pygame.draw.ellipse(surface, (150, 100, 50), (x + 40, y - 15, 15, 12))
    pygame.draw.rect(surface, (140, 90, 45), (x + 41, y - 12, 13, 10))
    pygame.draw.rect(surface, (100, 70, 30), (x + 40, y - 10, 15, 2))
    pygame.draw.rect(surface, (100, 70, 30), (x + 40, y - 5, 15, 2))

def draw_breeding_structure(surface, x, y):
    # Stone base
    pygame.draw.rect(surface, (120, 120, 130), (x - 35, y - 10, 70, 30))
    pygame.draw.rect(surface, (90, 90, 100), (x - 35, y - 10, 70, 30), 3)

    # Heart-shaped structure
    heart_color = (220, 100, 120)
    heart_dark = (180, 70, 90)

    # Left bump
    pygame.draw.circle(surface, heart_color, (x - 12, y - 35), 18)
    pygame.draw.circle(surface, heart_dark, (x - 12, y - 35), 18, 2)

    # Right bump
    pygame.draw.circle(surface, heart_color, (x + 12, y - 35), 18)
    pygame.draw.circle(surface, heart_dark, (x + 12, y - 35), 18, 2)

    # Bottom point
    pygame.draw.polygon(surface, heart_color, [
        (x - 28, y - 28), (x + 28, y - 28), (x, y - 5)
    ])
    pygame.draw.polygon(surface, heart_dark, [
        (x - 28, y - 28), (x + 28, y - 28), (x, y - 5)
    ], 2)

    # Inner heart glow
    pygame.draw.circle(surface, (255, 180, 200), (x - 8, y - 38), 6)
    pygame.draw.circle(surface, (255, 180, 200), (x + 8, y - 38), 6)

    # Sparkle effect
    time = pygame.time.get_ticks() * 0.001
    sparkle_alpha = int(150 + math.sin(time * 3) * 100)
    sparkle = pygame.Surface((20, 20), pygame.SRCALPHA)
    pygame.draw.circle(sparkle, (255, 255, 255, sparkle_alpha), (10, 10), 4)
    surface.blit(sparkle, (x - 10, y - 55))

    # Sign
    sign_bg = pygame.Surface((70, 18), pygame.SRCALPHA)
    pygame.draw.rect(sign_bg, (50, 30, 10, 200), (0, 0, 70, 18), border_radius=5)
    surface.blit(sign_bg, (x - 35, y - 75))
    breed_text = font_tiny.render(t("breeding"), True, (255, 150, 180))
    surface.blit(breed_text, (x - breed_text.get_width()//2, y - 74))

def draw_tree(surface, x, y):
    pygame.draw.rect(surface, TREE_TRUNK, (x - 8, y - 40, 16, 50))
    pygame.draw.circle(surface, TREE_GREEN, (x, y - 55), 30)
    pygame.draw.circle(surface, (50, 160, 50), (x - 15, y - 45), 22)
    pygame.draw.circle(surface, (50, 160, 50), (x + 15, y - 45), 22)
    pygame.draw.circle(surface, (40, 150, 40), (x, y - 70), 20)

def draw_game_ui(surface, coins, score):
    # Top bar
    bar = pygame.Surface((WIDTH, 50), pygame.SRCALPHA)
    pygame.draw.rect(bar, (0, 0, 0, 150), (0, 0, WIDTH, 50))
    surface.blit(bar, (0, 0))

    # Coin display
    pygame.draw.circle(surface, GOLD, (40, 25), 15)
    pygame.draw.circle(surface, (200, 170, 0), (40, 25), 15, 2)
    coins_text = font_medium.render(str(coins), True, WHITE)
    surface.blit(coins_text, (60, 8))

    # Score
    score_text = font_small.render(f"{t('score')}: {score}", True, WHITE)
    surface.blit(score_text, (WIDTH - 150, 15))

    # Menu button
    menu_btn = pygame.Rect(WIDTH//2 - 50, 8, 100, 34)
    pygame.draw.rect(surface, BUTTON_NORMAL, menu_btn, border_radius=10)
    pygame.draw.rect(surface, (180, 140, 255), menu_btn, 2, border_radius=10)
    menu_text = font_small.render(t("menu"), True, WHITE)
    surface.blit(menu_text, (menu_btn.centerx - menu_text.get_width()//2, menu_btn.centery - menu_text.get_height()//2))

    # Instructions
    inst_bg = pygame.Surface((340, 30), pygame.SRCALPHA)
    pygame.draw.rect(inst_bg, (0, 0, 0, 100), (0, 0, 340, 30), border_radius=10)
    surface.blit(inst_bg, (WIDTH//2 - 170, HEIGHT - 40))
    inst = font_small.render(t("instruction"), True, WHITE)
    surface.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT - 37))

particles = []

def add_particle(x, y, text, color=GOLD):
    particles.append({"x": x, "y": y, "text": text, "color": color, "life": 60})

def update_particles(surface):
    for p in particles[:]:
        p["y"] -= 1
        p["life"] -= 1
        alpha = int(255 * (p["life"] / 60))
        text_surf = font_small.render(p["text"], True, p["color"])
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (p["x"], p["y"]))
        if p["life"] <= 0:
            particles.remove(p)

# Menu click sound
def play_click():
    click_sound.set_volume(volume)
    click_sound.play()

def toggle_fullscreen():
    global fullscreen, screen
    fullscreen = not fullscreen
    if fullscreen:
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    btn_fullscreen.text = t("fullscreen") + (" ON" if fullscreen else " OFF")

def draw_shop(surface):
    draw_sky(surface)
    draw_sun(surface)
    draw_island(surface)

    # Dark overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT))
    surface.blit(overlay, (0, 0))

    # Shop panel (taller for more upgrades)
    panel = pygame.Surface((500, 450), pygame.SRCALPHA)
    pygame.draw.rect(panel, (40, 60, 100, 240), (0, 0, 500, 450), border_radius=20)
    pygame.draw.rect(panel, ICE_BLUE, (0, 0, 500, 450), 3, border_radius=20)
    surface.blit(panel, (150, 75))

    # Title
    title = font_large.render(t("shop").upper(), True, GOLD)
    surface.blit(title, (WIDTH//2 - title.get_width()//2, 90))

    # Coin display
    pygame.draw.circle(surface, GOLD, (200, 140), 12)
    pygame.draw.circle(surface, (200, 170, 0), (200, 140), 12, 2)
    coin_text = font_small.render(str(coins), True, WHITE)
    surface.blit(coin_text, (218, 130))

    # --- Top hat upgrade ---
    upgrade_y = 170
    pygame.draw.rect(surface, (50, 70, 110), (200, upgrade_y, 400, 70), border_radius=10)
    pygame.draw.rect(surface, (80, 100, 150), (200, upgrade_y, 400, 70), 2, border_radius=10)

    hat_name = font_small.render(t("top_hat"), True, WHITE)
    surface.blit(hat_name, (215, upgrade_y + 8))
    hat_desc = font_tiny.render(t("top_hat_desc"), True, (180, 200, 220))
    surface.blit(hat_desc, (215, upgrade_y + 32))

    if upgrades.get("orange_top_hat", False):
        owned_text = font_small.render(t("bought"), True, (100, 255, 100))
        surface.blit(owned_text, (530, upgrade_y + 22))
    else:
        price_text = font_small.render("50", True, GOLD)
        surface.blit(price_text, (540, upgrade_y + 22))
        pygame.draw.circle(surface, GOLD, (525, upgrade_y + 32), 8)

    # --- Dockyard upgrade ---
    upgrade_y2 = 260
    pygame.draw.rect(surface, (50, 70, 110), (200, upgrade_y2, 400, 70), border_radius=10)
    pygame.draw.rect(surface, (80, 100, 150), (200, upgrade_y2, 400, 70), 2, border_radius=10)

    dock_name = font_small.render(t("dockyard"), True, WHITE)
    surface.blit(dock_name, (215, upgrade_y2 + 8))
    dock_desc = font_tiny.render(t("dockyard_desc"), True, (180, 200, 220))
    surface.blit(dock_desc, (215, upgrade_y2 + 32))

    if upgrades.get("dockyard", False):
        owned_text = font_small.render(t("bought"), True, (100, 255, 100))
        surface.blit(owned_text, (530, upgrade_y2 + 22))
    else:
        price_text = font_small.render("100", True, GOLD)
        surface.blit(price_text, (540, upgrade_y2 + 22))
        pygame.draw.circle(surface, GOLD, (522, upgrade_y2 + 32), 8)

    # --- Breeding Structure upgrade ---
    upgrade_y3 = 350
    pygame.draw.rect(surface, (50, 70, 110), (200, upgrade_y3, 400, 70), border_radius=10)
    pygame.draw.rect(surface, (80, 100, 150), (200, upgrade_y3, 400, 70), 2, border_radius=10)

    breed_name = font_small.render(t("breeding_structure"), True, WHITE)
    surface.blit(breed_name, (215, upgrade_y3 + 8))
    breed_desc = font_tiny.render(t("breeding_structure_desc"), True, (180, 200, 220))
    surface.blit(breed_desc, (215, upgrade_y3 + 32))

    if upgrades.get("breeding_structure", False):
        owned_text = font_small.render(t("bought"), True, (100, 255, 100))
        surface.blit(owned_text, (530, upgrade_y3 + 22))
    else:
        price_text = font_small.render("200", True, GOLD)
        surface.blit(price_text, (540, upgrade_y3 + 22))
        pygame.draw.circle(surface, GOLD, (522, upgrade_y3 + 32), 8)

    # Back button
    btn_back.draw(surface)

def draw_languages(surface):
    draw_menu_background(surface)
    for p in snowflakes[:40]:
        p.update()
        p.draw(surface)

    # Title
    title = font_large.render(t("languages").upper(), True, FROST_WHITE)
    surface.blit(title, (WIDTH//2 - title.get_width()//2, 80))

    # Draw language buttons with flags
    for code, btn in lang_buttons:
        # Highlight current language
        if code == current_lang:
            pygame.draw.rect(surface, ICE_BLUE, btn.rect.inflate(10, 10), border_radius=18)
        btn.update(mouse_pos, mouse_pressed)
        btn.draw(surface)
        # Draw flag to the left of the button
        draw_flag(surface, btn.rect.x - 35, btn.rect.y + 15, code)

    # Back button
    btn_back.draw(surface)

# Load saved game
load_game()

# Apply fullscreen if saved
if fullscreen:
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)

# Update button texts based on loaded language
btn_play.text = t("play")
btn_settings.text = t("settings")
btn_credits.text = t("credits")
btn_quit.text = t("quit")
btn_back.text = t("back")
btn_languages.text = t("languages")
btn_fullscreen.text = t("fullscreen") + (" ON" if fullscreen else " OFF")
btn_updates.text = t("check_updates")
btn_update_download.text = t("update_download")

# Check for updates in background on startup
if UPDATE_CHECK_URL:
    start_update_check()

# Main game loop
running = True
mouse_pressed = False

while running:
    raw_mouse_pos = pygame.mouse.get_pos()
    # Scale mouse position to game coordinates in fullscreen
    if fullscreen:
        sw, sh = screen.get_size()
        mouse_pos = (int(raw_mouse_pos[0] * WIDTH / sw), int(raw_mouse_pos[1] * HEIGHT / sh))
    else:
        mouse_pos = raw_mouse_pos
    mouse_pressed_this_frame = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pressed = True
            mouse_pressed_this_frame = True
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_pressed = False
            dragging_volume = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                play_click()
                toggle_fullscreen()

    # === MENU STATE ===
    if current_state == STATE_MENU:
        btn_play.update(mouse_pos, mouse_pressed)
        btn_settings.update(mouse_pos, mouse_pressed)
        btn_credits.update(mouse_pos, mouse_pressed)
        btn_quit.update(mouse_pos, mouse_pressed)
        btn_languages.update(mouse_pos, mouse_pressed)

        if mouse_pressed_this_frame:
            if btn_play.hovered:
                play_click()
                current_state = STATE_PLAY
                fade_alpha = 255
            elif btn_settings.hovered:
                play_click()
                current_state = STATE_SETTINGS
            elif btn_credits.hovered:
                play_click()
                current_state = STATE_CREDITS
            elif btn_languages.hovered:
                play_click()
                current_state = STATE_LANGUAGES
            elif btn_quit.hovered:
                play_click()
                save_game()
                running = False

        draw_menu(game_surface)
        btn_play.draw(game_surface)
        btn_settings.draw(game_surface)
        btn_credits.draw(game_surface)
        btn_quit.draw(game_surface)
        btn_languages.draw(game_surface)

    # === SETTINGS STATE ===
    elif current_state == STATE_SETTINGS:
        btn_back.update(mouse_pos, mouse_pressed)
        btn_fullscreen.update(mouse_pos, mouse_pressed)
        btn_updates.update(mouse_pos, mouse_pressed)

        # Volume slider
        if mouse_pressed:
            if vol_slider_rect.collidepoint(mouse_pos) or dragging_volume:
                dragging_volume = True
                vol_handle_x = max(vol_slider_rect.x, min(mouse_pos[0], vol_slider_rect.right))
                volume = (vol_handle_x - vol_slider_rect.x) / vol_slider_rect.width

        if mouse_pressed_this_frame:
            if btn_back.hovered:
                play_click()
                current_state = STATE_MENU
            elif btn_fullscreen.hovered:
                play_click()
                toggle_fullscreen()
            elif btn_updates.hovered:
                play_click()
                update_checking = True
                update_error = None
                start_update_check()
                current_state = STATE_UPDATES

        draw_settings(game_surface)

    # === CREDITS STATE ===
    elif current_state == STATE_CREDITS:
        btn_back.update(mouse_pos, mouse_pressed)

        if mouse_pressed_this_frame:
            if btn_back.hovered:
                play_click()
                current_state = STATE_MENU

        draw_credits(game_surface)

    # === LANGUAGES STATE ===
    elif current_state == STATE_LANGUAGES:
        btn_back.update(mouse_pos, mouse_pressed)

        if mouse_pressed_this_frame:
            if btn_back.hovered:
                play_click()
                current_state = STATE_MENU
            else:
                for code, btn in lang_buttons:
                    if btn.hovered:
                        play_click()
                        current_lang = code
                        # Update button texts
                        btn_play.text = t("play")
                        btn_settings.text = t("settings")
                        btn_credits.text = t("credits")
                        btn_quit.text = t("quit")
                        btn_back.text = t("back")
                        btn_languages.text = t("languages")
                        btn_fullscreen.text = t("fullscreen") + (" ON" if fullscreen else " OFF")

        draw_languages(game_surface)

    # === SHOP STATE ===
    elif current_state == STATE_SHOP:
        btn_back.update(mouse_pos, mouse_pressed)

        if mouse_pressed_this_frame:
            if btn_back.hovered:
                play_click()
                current_state = STATE_PLAY
            # Check if clicking on top hat upgrade (y: 170-240)
            elif 200 <= mouse_pos[0] <= 600 and 170 <= mouse_pos[1] <= 240:
                if not upgrades.get("orange_top_hat", False):
                    if coins >= 50:
                        play_click()
                        coins -= 50
                        upgrades["orange_top_hat"] = True
                    else:
                        play_click()
            # Check if clicking on dockyard upgrade (y: 260-330)
            elif 200 <= mouse_pos[0] <= 600 and 260 <= mouse_pos[1] <= 330:
                if not upgrades.get("dockyard", False):
                    if coins >= 100:
                        play_click()
                        coins -= 100
                        upgrades["dockyard"] = True
                    else:
                        play_click()
            # Check if clicking on breeding structure upgrade (y: 350-420)
            elif 200 <= mouse_pos[0] <= 600 and 350 <= mouse_pos[1] <= 420:
                if not upgrades.get("breeding_structure", False):
                    if coins >= 200:
                        play_click()
                        coins -= 200
                        upgrades["breeding_structure"] = True
                    else:
                        play_click()

        draw_shop(game_surface)

    # === PLAY STATE ===
    elif current_state == STATE_PLAY:
        if mouse_pressed_this_frame:
            pos = mouse_pos

            # Check menu button
            menu_btn = pygame.Rect(WIDTH//2 - 50, 8, 100, 34)
            if menu_btn.collidepoint(pos):
                play_click()
                current_state = STATE_MENU
                continue

            # Check house click (shop)
            house_rect = pygame.Rect(355, 280, 90, 55)
            if house_rect.collidepoint(pos):
                play_click()
                current_state = STATE_SHOP
                continue

            # Check breeding structure click
            if upgrades.get("breeding_structure", False):
                breed_rect = pygame.Rect(585, 280, 70, 70)
                if breed_rect.collidepoint(pos):
                    play_click()
                    breeding_selected = [None, None]
                    current_state = STATE_BREEDING
                    continue

            for monster in monsters:
                if monster.is_clicked(pos):
                    if monster.on_click():
                        coins += 10
                        score += 100
                        add_particle(pos[0], pos[1], "+10")

        # Update
        for cloud in clouds:
            cloud["x"] += cloud["speed"]
            if cloud["x"] > WIDTH + 50:
                cloud["x"] = -50

        for monster in monsters:
            monster.update()

        # Draw
        draw_sky(game_surface)
        draw_sun(game_surface)

        for cloud in clouds:
            draw_cloud(game_surface, cloud["x"], cloud["y"], cloud["size"])

        draw_island(game_surface)
        draw_tree(game_surface, 130, 350)
        draw_tree(game_surface, 670, 340)

        for monster in sorted(monsters, key=lambda m: m.y):
            monster.draw(game_surface)

        update_particles(game_surface)
        draw_game_ui(game_surface, coins, score)

    # === BREEDING STATE ===
    elif current_state == STATE_BREEDING:
        btn_back.update(mouse_pos, mouse_pressed)

        if mouse_pressed_this_frame:
            if btn_back.hovered:
                play_click()
                current_state = STATE_PLAY
                breeding_selected = [None, None]
            else:
                # Check if clicking on a monster to select
                for i, monster in enumerate(monsters):
                    if monster.is_clicked(mouse_pos):
                        play_click()
                        if breeding_selected[0] is None:
                            breeding_selected[0] = i
                        elif breeding_selected[1] is None and breeding_selected[0] != i:
                            breeding_selected[1] = i
                            # Start breeding
                            if coins >= breeding_cost:
                                coins -= breeding_cost
                                breeding_timer = 180  # 3 seconds at 60 FPS
                                # Determine result based on parent colors
                                parent1_name = monsters[breeding_selected[0]].name
                                parent2_name = monsters[breeding_selected[1]].name
                                # Sort names to match combination key
                                key = tuple(sorted([parent1_name, parent2_name]))
                                if key in breeding_combinations:
                                    color, color_dark, baby_name = breeding_combinations[key]
                                    breeding_result = (color, color_dark, baby_name)
                                else:
                                    # Fallback: blend colors
                                    c1 = monsters[breeding_selected[0]].color
                                    c2 = monsters[breeding_selected[1]].color
                                    color = ((c1[0] + c2[0]) // 2, (c1[1] + c2[1]) // 2, (c1[2] + c2[2]) // 2)
                                    color_dark = (int(color[0] * 0.8), int(color[1] * 0.8), int(color[2] * 0.8))
                                    breeding_result = (color, color_dark, "baby")
                        break

        # Update breeding timer
        if breeding_timer > 0:
            breeding_timer -= 1
            if breeding_timer == 0 and breeding_result:
                # Spawn baby monster
                color, color_dark, baby_name = breeding_result
                # Find empty spot on island
                baby_x = random.randint(150, 650)
                baby_y = random.randint(380, 450)
                baby_monster = Monster(baby_x, baby_y, color, color_dark, random.randint(0, 3), baby_name)
                baby_monster.size = 0.6  # Babies start smaller
                monsters.append(baby_monster)
                breeding_babies.append(len(monsters) - 1)
                breeding_selected = [None, None]
                breeding_result = None
                add_particle(WIDTH // 2, HEIGHT // 2, t("breeding_baby"), (255, 200, 220))

        # Draw breeding UI
        draw_sky(game_surface)
        draw_sun(game_surface)
        for cloud in clouds:
            draw_cloud(game_surface, cloud["x"], cloud["y"], cloud["size"])
        draw_island(game_surface)
        draw_tree(game_surface, 130, 350)
        draw_tree(game_surface, 670, 340)

        for monster in sorted(monsters, key=lambda m: m.y):
            monster.draw(game_surface)

        # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT))
        game_surface.blit(overlay, (0, 0))

        # Breeding panel
        panel = pygame.Surface((500, 400), pygame.SRCALPHA)
        pygame.draw.rect(panel, (40, 60, 100, 240), (0, 0, 500, 400), border_radius=20)
        pygame.draw.rect(panel, (220, 100, 150), (0, 0, 500, 400), 3, border_radius=20)
        game_surface.blit(panel, (150, 100))

        # Title
        title = font_large.render(t("breeding").upper(), True, (255, 180, 200))
        game_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        # Cost display
        cost_text = font_small.render(t("breeding_cost"), True, WHITE)
        game_surface.blit(cost_text, (WIDTH // 2 - cost_text.get_width() // 2, 170))

        # Coin display
        pygame.draw.circle(game_surface, GOLD, (200, 200), 12)
        pygame.draw.circle(game_surface, (200, 170, 0), (200, 200), 12, 2)
        coin_text = font_small.render(str(coins), True, WHITE)
        game_surface.blit(coin_text, (218, 190))

        # Parent slots
        slot_y = 230
        for i in range(2):
            slot_x = 250 + i * 150
            # Slot background
            slot_color = (220, 100, 150) if breeding_selected[i] is not None else (60, 80, 120)
            pygame.draw.rect(game_surface, slot_color, (slot_x - 50, slot_y, 100, 100), border_radius=15)
            pygame.draw.rect(game_surface, (180, 140, 255), (slot_x - 50, slot_y, 100, 100), 2, border_radius=15)

            if breeding_selected[i] is not None:
                # Draw mini monster preview
                monster = monsters[breeding_selected[i]]
                pygame.draw.ellipse(game_surface, monster.color, (slot_x - 25, slot_y + 20, 50, 40))
                pygame.draw.ellipse(game_surface, monster.color_dark, (slot_x - 25, slot_y + 20, 50, 40), 2)
                pygame.draw.circle(game_surface, WHITE, (slot_x - 8, slot_y + 30), 6)
                pygame.draw.circle(game_surface, WHITE, (slot_x + 8, slot_y + 30), 6)
                pygame.draw.circle(game_surface, BLACK, (slot_x - 6, slot_y + 32), 3)
                pygame.draw.circle(game_surface, BLACK, (slot_x + 10, slot_y + 32), 3)
            else:
                # Empty slot
                label = t(f"breeding_select_{'first' if i == 0 else 'second'}")
                label_text = font_tiny.render(label, True, (150, 200, 240))
                game_surface.blit(label_text, (slot_x - label_text.get_width() // 2, slot_y + 40))

        # Breeding progress
        if breeding_timer > 0:
            progress_text = font_medium.render(t("breeding_busy"), True, (255, 200, 220))
            game_surface.blit(progress_text, (WIDTH // 2 - progress_text.get_width() // 2, 360))
            # Progress bar
            bar_width = 300
            bar_height = 20
            bar_x = WIDTH // 2 - bar_width // 2
            bar_y = 400
            pygame.draw.rect(game_surface, (40, 60, 100), (bar_x, bar_y, bar_width, bar_height), border_radius=10)
            progress = 1 - (breeding_timer / 180)
            fill_width = int(bar_width * progress)
            pygame.draw.rect(game_surface, (220, 100, 150), (bar_x, bar_y, fill_width, bar_height), border_radius=10)
            pygame.draw.rect(game_surface, (180, 140, 255), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=10)
        elif breeding_selected[0] is not None and breeding_selected[1] is not None:
            # Both selected, ready to breed
            ready_text = font_medium.render(t("breeding_select"), True, (100, 255, 150))
            game_surface.blit(ready_text, (WIDTH // 2 - ready_text.get_width() // 2, 360))
        else:
            # Instructions
            instruct_text = font_small.render(t("breeding_select"), True, (180, 200, 220))
            game_surface.blit(instruct_text, (WIDTH // 2 - instruct_text.get_width() // 2, 360))

        btn_back.draw(game_surface)
        update_particles(game_surface)

    # === UPDATES STATE ===
    elif current_state == STATE_UPDATES:
        btn_back.update(mouse_pos, mouse_pressed)
        if update_available:
            btn_update_download.update(mouse_pos, mouse_pressed)

        if mouse_pressed_this_frame:
            if btn_back.hovered:
                play_click()
                current_state = STATE_SETTINGS
            elif update_available and btn_update_download.hovered and not update_downloading:
                play_click()
                start_update_download()

        # Draw update screen
        draw_menu_background(game_surface)
        for p in snowflakes[:40]:
            p.update()
            p.draw(game_surface)

        title = font_large.render(t("check_updates").upper(), True, FROST_WHITE)
        game_surface.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        if update_checking:
            status_text = font_medium.render(t("update_checking"), True, ICE_LIGHT)
            game_surface.blit(status_text, (WIDTH//2 - status_text.get_width()//2, 250))
        elif update_downloading:
            pct = int(update_progress * 100)
            status_text = font_medium.render(t("update_downloading").format(pct=pct), True, ICE_LIGHT)
            game_surface.blit(status_text, (WIDTH//2 - status_text.get_width()//2, 250))
            # Progress bar
            bar_width = 400
            bar_height = 25
            bar_x = WIDTH//2 - bar_width//2
            bar_y = 310
            pygame.draw.rect(game_surface, (30, 50, 80), (bar_x, bar_y, bar_width, bar_height), border_radius=12)
            fill_w = int(bar_width * update_progress)
            pygame.draw.rect(game_surface, ICE_LIGHT, (bar_x, bar_y, fill_w, bar_height), border_radius=12)
            pygame.draw.rect(game_surface, ICE_BLUE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=12)
        elif update_available:
            avail_text = font_large.render(t("update_available"), True, (100, 255, 150))
            game_surface.blit(avail_text, (WIDTH//2 - avail_text.get_width()//2, 200))
            if update_info:
                ver_text = font_medium.render(t("update_version").format(ver=update_info.get("version", "?")), True, WHITE)
                game_surface.blit(ver_text, (WIDTH//2 - ver_text.get_width()//2, 260))
                if update_info.get("notes"):
                    notes_text = font_tiny.render(update_info["notes"], True, (180, 200, 220))
                    game_surface.blit(notes_text, (WIDTH//2 - notes_text.get_width()//2, 310))
            btn_update_download.draw(game_surface)
        elif update_error:
            if update_error == "no_url":
                err_text = font_small.render(t("update_no_url"), True, (255, 150, 150))
            else:
                err_text = font_small.render(t("update_error"), True, (255, 150, 150))
            game_surface.blit(err_text, (WIDTH//2 - err_text.get_width()//2, 250))
        else:
            latest_text = font_medium.render(t("update_latest"), True, (100, 255, 100))
            game_surface.blit(latest_text, (WIDTH//2 - latest_text.get_width()//2, 250))

        # Version info
        ver_info = font_tiny.render(f"v{GAME_VERSION}", True, (100, 150, 200))
        game_surface.blit(ver_info, (WIDTH//2 - ver_info.get_width()//2, 480))

        btn_back.draw(game_surface)

    # Fade transition
    if fade_alpha > 0:
        fade_surface = pygame.Surface((WIDTH, HEIGHT))
        fade_surface.fill(BLACK)
        fade_surface.set_alpha(fade_alpha)
        game_surface.blit(fade_surface, (0, 0))
        fade_alpha -= fade_speed

    # Scale game to screen (fullscreen or windowed)
    if fullscreen:
        sw, sh = screen.get_size()
        scaled = pygame.transform.scale(game_surface, (sw, sh))
        screen.blit(scaled, (0, 0))
    else:
        screen.blit(game_surface, (0, 0))

    pygame.display.flip()
    # Auto-save every 10 minutes
    if time.time() - last_save_time > 600:
        save_game()

    clock.tick(60)

pygame.quit()
