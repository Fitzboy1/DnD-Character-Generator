from flask import Flask, render_template, jsonify, request, send_from_directory, abort
import random
import json
import os
from threading import Lock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(__name__, static_folder="static", template_folder="templates")
LOCK = Lock()
FAV_FILE = os.path.join(BASE_DIR, "favorites.json")

# Ensure favorites file exists
if not os.path.exists(FAV_FILE):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# Helper to load JSON dataset files
def load_json(fname):
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing data file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Load datasets at startup
try:
    LISTS = load_json("lists.json")
    NAMES = load_json("names.json")
except Exception as e:
    raise RuntimeError(f"Failed to load data files from data/: {e}")

# Expose some convenient references
BACKGROUNDS = LISTS.get("backgrounds", [])
RACES = LISTS.get("races", [])
CLASSES = LISTS.get("classes", [])
ALIGNMENTS = LISTS.get("alignments", [])
PRONOUN_PRESETS = LISTS.get("pronouns", [{"label": "They/Them", "value": "they/them"}])
LANGUAGES = LISTS.get("languages", [])
SKILLS = LISTS.get("skills", [])
EQUIPMENT = LISTS.get("equipment", [])
IDEALS = LISTS.get("ideals", [])
BONDS = LISTS.get("bonds", [])
FLAWS = LISTS.get("flaws", [])
PERSONALITY_TRAITS = LISTS.get("personality_traits", [])
SUBCLASSES = LISTS.get("subclasses", {})  # mapping class -> possible subclasses
FIRST_NAMES = NAMES.get("first", [])
SURNAMES = NAMES.get("surname", [])

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

def roll_4d6_drop_lowest():
    scores = []
    for _ in range(6):
        rolls = [random.randint(1,6) for _ in range(4)]
        rolls.sort()
        scores.append(sum(rolls[1:]))
    return scores

def modifiers_from_scores(scores):
    return [ (int(s) - 10) // 2 for s in scores ]

def random_height_weight(race):
    base_height = 60
    base_weight = 120
    race_mod = LISTS.get("race_height_weight_mods", {})
    dh, dw = race_mod.get(race, (0,0))
    inches = base_height + dh + random.randint(-6, 8)
    pounds = base_weight + dw + random.randint(-20, 60)
    feet = inches // 12
    rem_in = inches % 12
    return f"{feet}ft {rem_in}in", f"{pounds}lbs"

def pick_unique(lst, n):
    if not lst:
        return []
    return random.sample(lst, min(len(lst), n))

def random_age_for_race(race):
    ranges = LISTS.get("age_ranges", {})
    lo, hi = ranges.get(race, (16, 120))
    return random.randint(lo, hi)

def build_character(payload):
    method = payload.get("method", "4d6")
    custom_name = payload.get("name", "").strip()
    chosen_pronouns = payload.get("pronouns", "they/them")
    chosen_gender = payload.get("gender", "").strip()

    background = random.choice(BACKGROUNDS) if BACKGROUNDS else ""
    race = random.choice(RACES) if RACES else "Human"
    cls = random.choice(CLASSES) if CLASSES else "Fighter"
    alignment = random.choice(ALIGNMENTS) if ALIGNMENTS else "True Neutral"

    if method == "4d6":
        ability_scores = roll_4d6_drop_lowest()
    elif method == "standard":
        ability_scores = STANDARD_ARRAY.copy()
        random.shuffle(ability_scores)
    else:
        # unknown method fallback to 4d6
        ability_scores = roll_4d6_drop_lowest()

    ability_scores = [int(s) for s in ability_scores]
    mods = modifiers_from_scores(ability_scores)
    height, weight = random_height_weight(race)
    age = random_age_for_race(race)

    languages = ["Common"]
    # add some common race languages from data if defined
    race_lang_map = LISTS.get("race_languages", {})
    extra_langs = race_lang_map.get(race, [])
    for l in extra_langs:
        if l not in languages:
            languages.append(l)
    # occasional extra language
    if random.random() < 0.25 and LANGUAGES:
        extra = random.choice([l for l in LANGUAGES if l not in languages])
        languages.append(extra)

    profs = pick_unique(SKILLS, 2)
    double_profs = []
    equip = pick_unique(EQUIPMENT, 3)
    money = f"{random.choice([0, 5, 10, 15, 25, 50])} gp"
    name = custom_name or f"{random.choice(FIRST_NAMES)} {random.choice(SURNAMES)}" if FIRST_NAMES and SURNAMES else custom_name or "Unnamed"
    personality = random.choice(PERSONALITY_TRAITS) if PERSONALITY_TRAITS else ""
    ideal = random.choice(IDEALS) if IDEALS else ""
    bond = random.choice(BONDS) if BONDS else ""
    flaw = random.choice(FLAWS) if FLAWS else ""

    # pick subclass from mapping if available for class
    subclass = ""
    if SUBCLASSES and cls in SUBCLASSES:
        subs = SUBCLASSES.get(cls, [])
        if subs:
            subclass = random.choice(subs)

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
    try:
        result = build_character(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(result)

@app.route("/api/lists", methods=["GET"])
def get_lists():
    # Expose the lists (for frontend controls if needed)
    return jsonify(LISTS)

# Favorites API
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
