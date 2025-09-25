from flask import Flask, render_template, jsonify, request, send_from_directory
import random, json, os
from threading import Lock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(__name__, static_folder="static", template_folder="templates")
LOCK = Lock()
FAV_FILE = os.path.join(BASE_DIR, "favorites.json")

if not os.path.exists(FAV_FILE):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

def load_json(fname):
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing data file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

LISTS = load_json("lists.json")
NAMES = load_json("names.json")

BACKGROUNDS = LISTS.get("backgrounds", [])
RACES = LISTS.get("races", [])
CLASSES = LISTS.get("classes", [])
ALIGNMENTS = LISTS.get("alignments", [])
PRONOUN_PRESETS = LISTS.get("pronouns", [{"label":"They/Them","value":"they/them"}])
LANGUAGES = LISTS.get("languages", [])
SKILLS = LISTS.get("skills", [])
EQUIPMENT_ITEMS = LISTS.get("equipment", [])

PERSONALITY_TRAITS = LISTS.get("personality_traits", [
    "Quick to smile","Stoic and watchful","Hot-headed","Curious about everything",
    "Slow to trust","Generous when able","Proud and formal","Kind but guarded"
])
IDEALS = LISTS.get("ideals", [
    "Honor","Freedom","Community","Knowledge","Power","Redemption","Mercy","Ambition"
])
BONDS = LISTS.get("bonds", [
    "A mentor I owe everything to","My family name","A debt I must repay",
    "My homeland","A lost lover","A sacred relic"
])
FLAWS = LISTS.get("flaws", [
    "I take unnecessary risks","I hold grudges","I lie to impress others",
    "I have a weakness for gambling","I am easily manipulated"
])

SUBCLASSES = LISTS.get("subclasses", {})
FIRST_NAMES = NAMES.get("first", [])
SURNAMES = NAMES.get("surname", [])

STANDARD_ARRAY = [15,14,13,12,10,8]

def roll_4d6_drop_lowest():
    scores=[]
    for _ in range(6):
        rolls=[random.randint(1,6) for _ in range(4)]
        rolls.sort()
        scores.append(sum(rolls[1:]))
    return scores

def modifiers_from_scores(scores):
    return [ (int(s)-10)//2 for s in scores ]

def random_height_weight(race):
    base_height=60
    base_weight=120
    race_mod = LISTS.get("race_height_weight_mods", {})
    dh,dw = race_mod.get(race,(0,0))
    inches = base_height + dh + random.randint(-6,8)
    pounds = base_weight + dw + random.randint(-20,60)
    return f"{inches//12}ft {inches%12}in", f"{pounds}lbs"

def pick_unique(lst,n):
    if not lst: return []
    return random.sample(lst, min(len(lst), n))

def random_age_for_race(race):
    ranges = LISTS.get("age_ranges", {})
    lo,hi = ranges.get(race,(16,120))
    return random.randint(lo,hi)

# --- CHANGED choose_equipment TO USE RANDOM RANGE ---
def choose_equipment(min_choices=5, max_choices=15):
    """
    Choose equipment items. Randomly pick between min_choices and max_choices items.
    Ensures at most one bundle (pack) per character.
    """
    num_choices = random.randint(min_choices, max_choices)

    if not EQUIPMENT_ITEMS:
        return []

    bundles = [it for it in EQUIPMENT_ITEMS if isinstance(it, dict) and it.get("type") == "bundle"]
    non_bundles = [it for it in EQUIPMENT_ITEMS if not (isinstance(it, dict) and it.get("type") == "bundle")]

    chosen = []
    remaining = num_choices

    include_bundle = bool(bundles) and (random.random() < 0.25)

    if include_bundle:
        item = random.choice(bundles)
        name = item.get("name")
        itype = item.get("type", "bundle")
        obj = {"name": name, "type": itype, "qty": 1}
        if item.get("notes"):
            obj["notes"] = item.get("notes")
        if item.get("contents"):
            obj["contents"] = item.get("contents")
        chosen.append(obj)
        remaining -= 1

    pool_non_bundle = non_bundles.copy() if non_bundles else EQUIPMENT_ITEMS.copy()

    for _ in range(remaining):
        if not pool_non_bundle:
            pool_non_bundle = EQUIPMENT_ITEMS.copy()
        item = random.choice(pool_non_bundle)
        name = item.get("name") if isinstance(item, dict) else str(item)
        itype = item.get("type","single") if isinstance(item, dict) else "single"
        obj = {"name": name, "type": itype, "qty": 1}
        if itype in ("stackable","ammo","consumable"):
            min_q = item.get("min_qty",1)
            max_q = item.get("max_qty", max(min_q,4))
            obj["qty"] = random.randint(min_q, max_q)
        if item.get("notes"):
            obj["notes"] = item.get("notes")
        if item.get("contents"):
            obj["contents"] = item.get("contents")

        if obj["qty"] == 1 and not obj.get("notes") and not obj.get("contents") and itype == "single":
            chosen.append(name)
        else:
            chosen.append(obj)

        if isinstance(item, dict) and not item.get("allow_duplicate"):
            try:
                pool_non_bundle.remove(item)
            except ValueError:
                pass

    return chosen
# --- END CHANGED FUNCTION ---

def split_money_into_coins(total_gp):
    conv = LISTS.get("currency_conversion", {"gp":1,"sp":0.1,"cp":0.01})
    invs = [1/v if v>0 else 1 for v in conv.values()]
    multiplier = max(1, int(round(max(invs))))
    total_small = int(round(total_gp * multiplier))
    unit_values = {cur:int(round(v*multiplier)) for cur,v in conv.items()}
    unit_values.setdefault("gp", multiplier)
    unit_values.setdefault("sp", int(round(0.1*multiplier)))
    unit_values.setdefault("cp", 1)

    max_gold = total_small // unit_values["gp"]
    gold_qty = random.randint(max(0, max_gold//2), max_gold) if max_gold>0 else 0
    rem = total_small - gold_qty * unit_values["gp"]

    max_silver = rem // unit_values["sp"] if unit_values["sp"]>0 else 0
    silver_qty = 0
    if max_silver > 0:
        silver_qty = random.randint(max(0, max_silver//3), max_silver)
    rem -= silver_qty * unit_values["sp"]

    copper_qty = rem // unit_values["cp"] if unit_values["cp"]>0 else 0

    caps = LISTS.get("coin_stack_caps", {"gp":100, "sp":50, "cp":200})
    return {
        "gp": gold_qty,
        "sp": silver_qty,
        "cp": copper_qty,
        "caps": caps
    }

def compute_money_from_coins(coins):
    conv = LISTS.get("currency_conversion", {"gp":1,"sp":0.1,"cp":0.01})
    total_gp = 0.0
    for cur in ("gp","sp","cp"):
        qty = int(coins.get(cur, 0))
        rate = conv.get(cur, 1)
        total_gp += qty * rate
    return round(total_gp, 2)

def split_into_stacks(coins):
    caps = LISTS.get("coin_stack_caps", {"gp":100,"sp":50,"cp":200})
    name_map = {}
    for it in EQUIPMENT_ITEMS:
        if isinstance(it, dict) and it.get("currency"):
            name_map[it.get("currency")] = it.get("name")
    stacks = []
    for cur in ("gp","sp","cp"):
        qty = int(coins.get(cur, 0))
        cap = max(1, int(caps.get(cur, 50 if cur=="sp" else 200)))
        while qty > 0:
            take = min(qty, cap)
            stacks.append({
                "name": name_map.get(cur, f"{cur.upper()} Piece (coin)"),
                "type": "stackable",
                "currency": cur,
                "qty": take,
                "value": 1
            })
            qty -= take
    return stacks

def build_character(payload):
    method = payload.get("method","4d6")
    custom_name = payload.get("name","").strip()
    chosen_pronouns = payload.get("pronouns","they/them")
    chosen_gender = payload.get("gender","").strip()

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
        ability_scores = roll_4d6_drop_lowest()

    ability_scores = [int(s) for s in ability_scores]
    mods = modifiers_from_scores(ability_scores)
    height, weight = random_height_weight(race)
    age = random_age_for_race(race)

    languages = ["Common"]
    race_lang_map = LISTS.get("race_languages", {})
    extra_langs = race_lang_map.get(race, [])
    for l in extra_langs:
        if l not in languages:
            languages.append(l)
    if random.random() < 0.25 and LANGUAGES:
        extra = random.choice([l for l in LANGUAGES if l not in languages])
        languages.append(extra)

    profs = pick_unique(SKILLS, 2)
    double_profs = []
    # --- updated to use random amount of equipment ---
    equip = choose_equipment(min_choices=5, max_choices=15)

    base_random_money = random.choice([0,5,10,15,25,50,75,100])
    if background in ("Noble","Guild Artisan"):
        base_random_money += random.choice([50,75,100])
    if background in ("Urchin","Hermit"):
        base_random_money = max(base_random_money - random.choice([5,10]), 0)
    money_gp_total = int(round(base_random_money))

    coins_totals = split_money_into_coins(money_gp_total)
    coins = {k: coins_totals[k] for k in ("gp","sp","cp")}
    money_from_coins = compute_money_from_coins(coins)
    coin_stacks = split_into_stacks(coins)

    name = custom_name or (f"{random.choice(FIRST_NAMES)} {random.choice(SURNAMES)}" if FIRST_NAMES and SURNAMES else "Unnamed")
    personality = random.choice(PERSONALITY_TRAITS) if PERSONALITY_TRAITS else ""
    ideal = random.choice(IDEALS) if IDEALS else ""
    bond = random.choice(BONDS) if BONDS else ""
    flaw = random.choice(FLAWS) if FLAWS else ""

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
        "coins": coins,
        "coin_stacks": coin_stacks,
        "money": f"{money_from_coins:.2f} gp",
        "money_gp_total": money_from_coins,
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
    return jsonify(LISTS)

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
    app.run(debug=True, use_reloader=False,)
