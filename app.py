from flask import Flask, render_template, jsonify, request, send_from_directory
import random
import json
import os
from threading import Lock

app = Flask(__name__, static_folder="static", template_folder="templates")
LOCK = Lock()
FAV_FILE = "favorites.json"

# Ensure favorites file exists
if not os.path.exists(FAV_FILE):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# Data sets
BACKGROUNDS = [
    "Acolyte", "Sage", "Criminal", "Soldier", "Entertainer",
    "Hermit", "Guild Artisan", "Folk Hero", "Noble", "Urchin",
    "Investigator", "Archivist", "Shipwright", "Cartographer"
]

RACES = [
    "Human", "High Elf", "Wood Elf", "Drow", "Halfling", "Lightfoot Halfling",
    "Stout Halfling", "Half-Elf", "Half-Orc", "Tiefling", "Dragonborn",
    "Gnome", "Forest Gnome", "Rock Gnome", "Aasimar", "Goliath", "Kenku", "Tabaxi"
]

CLASSES = [
    "Fighter", "Rogue", "Wizard", "Sorcerer", "Cleric", "Barbarian",
    "Ranger", "Paladin", "Warlock", "Bard", "Monk", "Druid"
]

ALIGNMENTS = [
    "Lawful Good", "Neutral Good", "Chaotic Good",
    "Lawful Neutral", "True Neutral", "Chaotic Neutral",
    "Lawful Evil", "Neutral Evil", "Chaotic Evil"
]

PRONOUN_PRESETS = [
    {"label": "They/Them", "value": "they/them"},
    {"label": "She/Her", "value": "she/her"},
    {"label": "He/Him", "value": "he/him"},
    {"label": "Custom", "value": "custom"}
]

FIRST_NAMES = [
    "Ash", "Rowan", "Kai", "Zara", "Mira", "Ira", "Sol", "Ren", "Luca", "Nia",
    "Asha", "Diego", "Omar", "Min", "Priya", "Kwame", "Aiko", "Sofia", "Mateo", "Lian",
    "Amara", "Chike", "Yara", "Noor", "Hana", "Eiji", "Marisol"
]

SURNAMES = [
    "Thorne", "Brightwood", "Maris", "Gale", "Ironheart", "Voss", "Kell",
    "N'dour", "Takeda", "Singh", "Garcia", "Okoye", "Hossain", "Ivanov", "Mbatha"
]

LANGUAGES = [
    "Common", "Elvish", "Dwarvish", "Halfling", "Infernal", "Abyssal", "Gnomish", "Goblin",
    "Orcish", "Sylvan", "Primordial", "Draconic", "Celestial", "Undercommon", "Thieves' Cant"
]

SKILLS = ["Athletics", "Acrobatics", "Sleight of Hand", "Stealth", "Arcana", "History", "Investigation", "Nature", "Religion", "Animal Handling", "Insight", "Medicine", "Perception", "Survival", "Persuasion", "Deception", "Intimidation"]

EQUIPMENT = [
    "Explorer's Pack", "Dungeoneer's Pack", "Light Crossbow", "Longsword", "Shortsword",
    "Shield", "Spellbook", "Holy Symbol", "Thieves' Tools", "Crowbar", "Rope (50 ft)", "Traveler's Clothes"
]

IDEALS = [
    "Greater good", "Personal freedom", "Greed", "Balance", "Knowledge", "Power", "Honor"
]

BONDS = [
    "My family", "A mentor", "A lost love", "My sworn oath", "My home village", "A debt", "An old patron"
]

FLAWS = [
    "I judge too quickly", "I have a weakness for vices", "I hide secrets", "I act rashly", "I am distrustful"
]

PERSONALITY_TRAITS = [
    "Brave", "Cautious", "Curious", "Stoic", "Charismatic", "Reserved", "Hot-headed", "Playful", "Methodical"
]

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

def roll_4d6_drop_lowest():
    scores = []
    for _ in range(6):
        rolls = [random.randint(1,6) for _ in range(4)]
        rolls.sort()
        scores.append(sum(rolls[1:]))
    return scores

def point_buy():
    costs = {9:1,10:2,11:3,12:4,13:5,14:7,15:9}
    scores = [8]*6
    points = 27
    while points > 0:
        idx = scores.index(min(scores))
        target = scores[idx] + 1
        if target > 15:
            break
        cost = costs.get(target, 999)
        if cost <= points:
            scores[idx] = target
            points -= cost
        else:
            break
    random.shuffle(scores)
    return scores

def modifiers_from_scores(scores):
    return [ (int(s) - 10) // 2 for s in scores ]

def random_height_weight(race):
    base_height = 60
    base_weight = 120
    race_mod = {
        "Halfling": (-12, -30),
        "Lightfoot Halfling": (-12, -30),
        "Stout Halfling": (-12, -30),
        "High Elf": (0, -5),
        "Wood Elf": (-2, -10),
        "Drow": (-3, -15),
        "Half-Elf": (-1, -10),
        "Half-Orc": (4, 20),
        "Dragonborn": (6, 30),
        "Tiefling": (0, -5),
        "Human": (0,0),
        "Gnome": (-10, -25),
        "Aasimar": (2, 5),
        "Goliath": (10, 50),
        "Kenku": (-8, -20),
        "Tabaxi": (-4, -5)
    }
    dh, dw = race_mod.get(race, (0,0))
    inches = base_height + dh + random.randint(-6, 8)
    pounds = base_weight + dw + random.randint(-20, 60)
    feet = inches // 12
    rem_in = inches % 12
    return f"{feet}ft {rem_in}in", f"{pounds}lbs"

def pick_unique(lst, n):
    return random.sample(lst, min(len(lst), n))

def random_age_for_race(race):
    ranges = {
        "Human": (16, 80),
        "High Elf": (100, 750),
        "Wood Elf": (100, 700),
        "Drow": (90, 600),
        "Halfling": (20, 150),
        "Lightfoot Halfling": (20, 150),
        "Stout Halfling": (20, 150),
        "Half-Elf": (20, 180),
        "Half-Orc": (14, 80),
        "Tiefling": (16, 120),
        "Dragonborn": (15, 80),
        "Gnome": (40, 500),
        "Forest Gnome": (40, 500),
        "Rock Gnome": (40, 500),
        "Aasimar": (18, 300),
        "Goliath": (12, 90),
        "Kenku": (10, 60),
        "Tabaxi": (8, 80)
    }
    lo, hi = ranges.get(race, (16, 120))
    return random.randint(lo, hi)

def build_character(payload):
    method = payload.get("method", "4d6")
    custom_name = payload.get("name", "").strip()
    chosen_pronouns = payload.get("pronouns", "they/them")
    chosen_gender = payload.get("gender", "").strip()

    background = random.choice(BACKGROUNDS)
    race = random.choice(RACES)
    cls = random.choice(CLASSES)
    alignment = random.choice(ALIGNMENTS)

    if method == "4d6":
        ability_scores = roll_4d6_drop_lowest()
    elif method == "standard":
        ability_scores = STANDARD_ARRAY.copy()
        random.shuffle(ability_scores)
    elif method == "pointbuy":
        ability_scores = point_buy()
    else:
        ability_scores = roll_4d6_drop_lowest()

    # ensure ints
    ability_scores = [int(s) for s in ability_scores]
    mods = modifiers_from_scores(ability_scores)
    height, weight = random_height_weight(race)
    age = random_age_for_race(race)

    languages = ["Common"]
    if "Elf" in race:
        languages.append("Elvish")
    if "Dwarf" in race:
        languages.append("Dwarvish")
    if race == "Tiefling":
        languages.append("Infernal")
    if race == "Dragonborn":
        languages.append("Draconic")
    if race == "Half-Orc":
        languages.append("Orcish")
    if random.random() < 0.25:
        extra = random.choice([l for l in LANGUAGES if l not in languages])
        languages.append(extra)

    profs = pick_unique(SKILLS, 2)
    double_profs = []
    equip = pick_unique(EQUIPMENT, 3)
    money = f"{random.choice([0, 5, 10, 15, 25, 50])} gp"
    name = custom_name or f"{random.choice(FIRST_NAMES)} {random.choice(SURNAMES)}"
    personality = random.choice(PERSONALITY_TRAITS)
    ideal = random.choice(IDEALS)
    bond = random.choice(BONDS)
    flaw = random.choice(FLAWS)

    subclass = ""
    if cls == "Barbarian":
        subclass = "Path of the Totem Warrior"
    if cls == "Sorcerer":
        subclass = random.choice(["Wild Magic", "Draconic Bloodline"])
    if cls == "Wizard":
        subclass = random.choice(["Evocation", "Divination", "Abjuration"])
    if cls == "Fighter":
        subclass = random.choice(["Champion", "Battle Master", "Eldritch Knight"])
    if cls == "Rogue":
        subclass = random.choice(["Thief", "Assassin", "Arcane Trickster"])
    if cls == "Cleric":
        subclass = random.choice(["Life Domain", "Light Domain", "War Domain"])
    if subclass == "" and cls == "Paladin":
        subclass = random.choice(["Oath of Devotion", "Oath of Vengeance", "Oath of Ancients"])

    result = {
        "name": name,
        "pronouns": chosen_pronouns,
        "gender": chosen_gender,
        "age": age,
        "background": background,
        "personality_trait": personality,
        "ideal": ideal,
        "bond": bond,
        "flaw": flaw,
        "alignment": alignment,
        "race": race,
        "height": height,
        "weight": weight,
        "class": cls,
        "subclass": subclass,
        "ability_scores": ability_scores,
        "ability_average": sum(ability_scores)/len(ability_scores),
        "modifiers": mods,
        "money": money,
        "languages": languages,
        "proficiencies": profs,
        "double_proficiencies": double_profs,
        "equipment": equip,
        "stat_method": method
    }
    return result

@app.route("/")
def index():
    return render_template("index.html", pronouns=PRONOUN_PRESETS)

@app.route("/api/generate", methods=["POST"])
def generate():
    payload = request.json or {}
    result = build_character(payload)
    return jsonify(result)

@app.route("/api/favorites", methods=["GET"])
def list_favorites():
    with LOCK:
        with open(FAV_FILE, "r", encoding="utf-8") as f:
            favs = json.load(f)
    return jsonify(favs)

@app.route("/api/favorites", methods=["POST"])
def add_favorite():
    payload = request.json or {}
    char = payload.get("character")
    if not char:
        return jsonify({"error": "No character provided"}), 400
    with LOCK:
        with open(FAV_FILE, "r+", encoding="utf-8") as f:
            try:
                favs = json.load(f)
            except Exception:
                favs = []
            char_id = max([c.get("id", 0) for c in favs], default=0) + 1
            char["id"] = char_id
            favs.append(char)
            f.seek(0)
            json.dump(favs, f, ensure_ascii=False, indent=2)
            f.truncate()
    return jsonify({"ok": True, "id": char_id})

@app.route("/api/favorites/<int:fid>", methods=["DELETE"])
def delete_favorite(fid):
    with LOCK:
        with open(FAV_FILE, "r+", encoding="utf-8") as f:
            favs = json.load(f)
            new = [c for c in favs if c.get("id") != fid]
            f.seek(0)
            json.dump(new, f, ensure_ascii=False, indent=2)
            f.truncate()
    return jsonify({"ok": True})

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(debug=True)