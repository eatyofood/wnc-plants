#!/usr/bin/env python3
"""Local flashcards for Western North Carolina plants and North Carolina birds."""

from __future__ import annotations

import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "data"))
from bird_path import BIRD_ORDER, BIRD_TITLES  # noqa: E402
from learn_path import GROUP_SIZE, GROUP_TITLES, LEARN_ORDER  # noqa: E402
from seed_birds import BIRDS as SEED_BIRDS  # noqa: E402

DATA_PATH = ROOT / "data" / "plants.json"
BIRDS_PATH = ROOT / "data" / "birds.json"
PROGRESS_PATH = ROOT / "data" / "progress.json"

app = Flask(__name__, static_folder="static", template_folder="templates")

# Each topic has its own unlocked-group count. Name-from-picture can be on
# group 7 while Uses is still on group 1. Topic ids are shared by both decks.
TOPICS = (
    ("name", "Name from the picture"),
    ("uses", "Uses"),
    ("lookalikes", "Look-alikes"),
    ("identify", "How to identify it"),
)
BIRD_TOPICS = (
    ("call", "Name from the call"),
    ("name", "Name from the picture"),
    ("uses", "Voice and diet"),
    ("lookalikes", "Look-alikes"),
    ("identify", "How to identify it"),
)
TOPIC_IDS = {key for key, _label in TOPICS}
TOPIC_FIELD = {"uses": "uses", "lookalikes": "lookalikes", "identify": "id_tips"}
PLANT_PROMPTS = {
    "name": "What plant is this?",
    "uses": "Which use fits this plant?",
    "lookalikes": "Which look-alike note fits this plant?",
    "identify": "Which clue identifies this plant?",
}
BIRD_PROMPTS = {
    "call": "Which bird made this call?",
    "name": "What bird is this?",
    "uses": "Which voice or diet note fits this bird?",
    "lookalikes": "Which look-alike note fits this bird?",
    "identify": "Which clue identifies this bird?",
}

BLANK = "_________"
_NAME_QUALIFIERS = {
    "eastern", "western", "northern", "southern", "american", "chinese",
    "japanese", "english", "oriental", "common", "wild", "flowering",
    "large", "large-flowered", "scarlet", "smooth", "highbush", "sweet",
    "yellow", "red", "white", "black", "downy", "hollow", "hollow-stem",
    "virginia", "carolina", "mountain", "striped", "shortleaf", "coral",
    "pignut", "shagbark", "cucumber", "cinnamon", "table", "rosebay",
    "catawba", "flame", "pink", "purple", "blue", "brown", "gold", "orange",
    "green",
}
_TOKEN_SKIP = _NAME_QUALIFIERS | {
    "the", "and", "for", "with", "from", "into", "over", "under", "its",
    "tree", "plant", "plants", "flower", "flowers", "vine", "stem",
    "leaf", "leaves", "wood", "grass", "weed", "bush",
}
_BIRD_TOKEN_SKIP = _TOKEN_SKIP | {
    "house", "song", "gray", "grey", "great", "belted", "crested",
    "collared", "headed", "throated", "rumped", "bellied", "tailed",
    "eyed", "crowned", "breasted", "horned", "winged", "european",
    "eurasian", "rock", "ruby", "dark", "cattle", "canada", "double",
    "pileated", "hairy", "mourning", "tufted", "chipping", "indigo",
    "hooded", "belted",
}
_GIVEAWAY_WORDS = (
    "oak", "maple", "pine", "birch", "hickory", "dogwood", "hemlock",
    "beech", "walnut", "locust", "poplar", "magnolia", "holly", "ash",
    "fir", "spruce", "cherry", "chestnut", "sycamore", "buckeye",
    "persimmon", "laurel", "sumac", "azalea", "rhododendron", "redbud",
    "pawpaw", "sassafras", "sourwood", "tulip", "trillium", "honeysuckle",
    "bittersweet", "privet", "kudzu", "wisteria", "blueberry", "elderberry",
    "serviceberry", "silverbell", "bloodroot", "mayapple", "spicebush",
    "pokeweed", "jewelweed", "witch", "hazel", "fern",
)
_BIRD_GIVEAWAYS = (
    "mockingbird", "chickadee", "hummingbird", "woodpecker", "nuthatch",
    "kingfisher", "yellowthroat", "goldfinch", "meadowlark", "cormorant",
    "gnatcatcher", "sapsucker", "blackbird", "bluebird", "catbird",
    "redstart", "ovenbird", "killdeer", "bobwhite", "thrasher", "waxwing",
    "kingbird", "cardinal", "starling", "sparrow", "grackle", "titmouse",
    "towhee", "flicker", "vulture", "kestrel", "warbler", "bunting",
    "tanager", "pelican", "mallard", "heron", "egret", "turkey", "grouse",
    "pigeon", "finch", "junco", "creeper", "osprey", "eagle", "thrush",
    "phoebe", "vireo", "swallow", "martin", "swift", "goose", "raven",
    "crow", "robin", "wren", "hawk", "dove", "duck", "swan", "gull",
    "tern", "owl", "jay", "willet",
)


class Deck:
    def __init__(self, key, noun, order, titles, prompts, topic_labels, giveaways, token_skip):
        self.key = key
        self.noun = noun
        self.order = list(order)
        self.titles = titles
        self.prompts = prompts
        self.topic_labels = topic_labels
        self.giveaways = giveaways
        self.token_skip = token_skip
        self.rows: list[dict] = []
        self.by_id: dict[str, dict] = {}
        self.group_count = 0
        self.id_to_group: dict[str, int] = {}

    def bind(self, rows: list[dict]) -> None:
        self.rows = rows
        self.by_id = {row["id"]: row for row in rows}
        self.group_count = (len(self.order) + GROUP_SIZE - 1) // GROUP_SIZE
        self.id_to_group = {
            pid: (index // GROUP_SIZE) + 1 for index, pid in enumerate(self.order)
        }

    def clamp(self, n) -> int:
        try:
            n = int(n)
        except (TypeError, ValueError):
            n = 1
        return max(1, min(self.group_count, n))


PLANT_DECK = Deck(
    "plants", "plants", LEARN_ORDER, GROUP_TITLES, PLANT_PROMPTS, TOPICS,
    _GIVEAWAY_WORDS, _TOKEN_SKIP,
)
BIRD_DECK = Deck(
    "birds", "birds", BIRD_ORDER, BIRD_TITLES, BIRD_PROMPTS, BIRD_TOPICS,
    _BIRD_GIVEAWAYS, _BIRD_TOKEN_SKIP,
)
DECKS = {"plants": PLANT_DECK, "birds": BIRD_DECK}

_PLANTS_MTIME: float | None = None
_BIRDS_MTIME: float | None = None


def load_json_list(path: Path) -> list[dict] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, list) or not data:
        return None
    if not all(isinstance(row, dict) and row.get("id") for row in data):
        return None
    return data


def ids_match(rows: list[dict], order: list[str]) -> bool:
    found = [row["id"] for row in rows]
    return len(found) == len(set(found)) and set(found) == set(order)


def reload_catalogs() -> None:
    """Pick up plants.json and birds.json when a photo save changes them."""
    global _PLANTS_MTIME, _BIRDS_MTIME
    if not DATA_PATH.exists():
        raise SystemExit("Missing data/plants.json. Run:  python3 download_images.py")
    plant_mtime = DATA_PATH.stat().st_mtime
    if _PLANTS_MTIME != plant_mtime:
        plants = load_json_list(DATA_PATH)
        if plants and ids_match(plants, LEARN_ORDER):
            PLANT_DECK.bind(plants)
            _PLANTS_MTIME = plant_mtime
    if BIRDS_PATH.exists():
        bird_mtime = BIRDS_PATH.stat().st_mtime
        if _BIRDS_MTIME != bird_mtime:
            birds = load_json_list(BIRDS_PATH)
            if birds and ids_match(birds, BIRD_ORDER):
                BIRD_DECK.bind(birds)
                _BIRDS_MTIME = bird_mtime
    if not BIRD_DECK.rows:
        BIRD_DECK.bind([dict(bird) for bird in SEED_BIRDS])


def ensure_catalogs() -> None:
    reload_catalogs()
    if not PLANT_DECK.rows or not ids_match(PLANT_DECK.rows, LEARN_ORDER):
        raise SystemExit("learn_path does not match data/plants.json")
    if len(LEARN_ORDER) != len(set(LEARN_ORDER)):
        raise SystemExit("learn_path has duplicate ids")
    if not BIRD_DECK.rows or not ids_match(BIRD_DECK.rows, BIRD_ORDER):
        raise SystemExit("bird_path does not match the bird deck")
    if len(BIRD_ORDER) != len(set(BIRD_ORDER)):
        raise SystemExit("bird_path has duplicate ids")


ensure_catalogs()


@app.before_request
def _refresh_catalog() -> None:
    reload_catalogs()


def clamp_group(n) -> int:
    return PLANT_DECK.clamp(n)


def empty_bird_box() -> dict:
    return {
        "unlocked_groups": 1,
        "topics": {key: 1 for key, _label in BIRD_TOPICS},
        "records": {},
    }


def empty_state() -> dict:
    return {
        "unlocked_groups": 1,
        "topics": {key: 1 for key, _label in TOPICS},
        "plants": {},
        "birds": empty_bird_box(),
    }


def normalize_plant_state(raw) -> tuple[dict, bool]:
    """Return plant progress. Name progress stays on unlocked_groups."""
    changed = False
    if not isinstance(raw, dict):
        base = empty_state()
        base.pop("birds", None)
        return base, True
    plants = raw.get("plants")
    if isinstance(raw, dict) and "unlocked_groups" in raw and isinstance(plants, dict):
        pass
    elif isinstance(raw, dict) and any(
        isinstance(v, dict) and "box" in v for v in raw.values()
    ):
        plants = {
            k: v
            for k, v in raw.items()
            if k != "_meta" and isinstance(v, dict) and "box" in v
        }
        raw = {"unlocked_groups": 1, "plants": plants}
        changed = True
    else:
        plants = {}
        changed = True
    if not isinstance(plants, dict):
        plants = {}
        changed = True
    topics_in = raw.get("topics") if isinstance(raw, dict) else None
    if not isinstance(topics_in, dict):
        topics_in = {}
        changed = True
    if "name" in topics_in:
        name_n = topics_in["name"]
        if "unlocked_groups" in raw and clamp_group(raw.get("unlocked_groups")) != clamp_group(name_n):
            name_n = raw.get("unlocked_groups")
            changed = True
    else:
        name_n = raw.get("unlocked_groups", 1) if isinstance(raw, dict) else 1
        changed = True
    topics = {}
    for key, _label in TOPICS:
        if key == "name":
            topics[key] = clamp_group(name_n)
        elif key not in topics_in:
            topics[key] = 1
            changed = True
        else:
            topics[key] = clamp_group(topics_in[key])
            if topics[key] != topics_in[key]:
                changed = True
    if not isinstance(raw, dict) or raw.get("unlocked_groups") != topics["name"]:
        changed = True
    return {
        "unlocked_groups": topics["name"],
        "topics": topics,
        "plants": plants,
    }, changed


def normalize_bird_box(raw) -> tuple[dict, bool]:
    """Bird groups live here so plant unlocked_groups is never rewritten."""
    changed = False
    if not isinstance(raw, dict):
        return empty_bird_box(), True
    records = raw.get("records")
    if not isinstance(records, dict):
        records = {}
        changed = True
    topics_in = raw.get("topics")
    if not isinstance(topics_in, dict):
        topics_in = {}
        changed = True
    topics = {}
    for key, _label in BIRD_TOPICS:
        if key not in topics_in:
            topics[key] = 1
            changed = True
        else:
            topics[key] = BIRD_DECK.clamp(topics_in[key])
            if topics[key] != topics_in[key]:
                changed = True
    if "unlocked_groups" in raw:
        name_n = BIRD_DECK.clamp(raw.get("unlocked_groups"))
        if topics["name"] != name_n:
            topics["name"] = name_n
            changed = True
    if raw.get("unlocked_groups") != topics["name"]:
        changed = True
    return {
        "unlocked_groups": topics["name"],
        "topics": topics,
        "records": records,
    }, changed


QUIZ_LOG_LIMIT = 4000


def clean_quiz_log(raw) -> tuple[list, bool]:
    """Keep quiz history without touching plant or bird mastery."""
    if not isinstance(raw, dict) or "quiz_log" not in raw:
        return [], False
    log = raw.get("quiz_log")
    if not isinstance(log, list):
        return [], True
    allowed = {
        "plants": {key for key, _label in TOPICS},
        "birds": {key for key, _label in BIRD_TOPICS},
    }
    clean = []
    changed = False
    for item in log:
        if not isinstance(item, dict):
            changed = True
            continue
        subject = item.get("subject")
        topic = item.get("topic")
        pid = item.get("id")
        correct = item.get("correct")
        when = item.get("t")
        if (
            subject not in allowed
            or topic not in allowed[subject]
            or not isinstance(pid, str)
            or not pid
            or not isinstance(correct, bool)
            or not isinstance(when, str)
            or not when
        ):
            changed = True
            continue
        clean.append(
            {
                "t": when,
                "subject": subject,
                "topic": topic,
                "id": pid,
                "correct": correct,
            }
        )
    if len(clean) > QUIZ_LOG_LIMIT:
        clean = clean[-QUIZ_LOG_LIMIT:]
        changed = True
    if len(clean) != len(log):
        changed = True
    return clean, changed


def normalize_state(raw) -> tuple[dict, bool]:
    plants, plant_changed = normalize_plant_state(raw)
    birds_raw = raw.get("birds") if isinstance(raw, dict) else None
    birds, bird_changed = normalize_bird_box(birds_raw)
    plants["birds"] = birds
    quiz_log, log_changed = clean_quiz_log(raw if isinstance(raw, dict) else None)
    plants["quiz_log"] = quiz_log
    return plants, plant_changed or bird_changed or log_changed


def load_state() -> dict:
    if not PROGRESS_PATH.exists():
        state = empty_state()
        save_state(state)
        return state
    try:
        raw = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        state = empty_state()
        save_state(state)
        return state
    state, changed = normalize_state(raw)
    if changed:
        save_state(state)
    return state


def save_state(state: dict) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def request_subject(body: dict | None = None) -> str:
    raw = ""
    if isinstance(body, dict) and body.get("subject"):
        raw = str(body.get("subject"))
    elif request.args.get("subject"):
        raw = str(request.args.get("subject"))
    raw = raw.strip()
    return raw if raw in DECKS else "plants"


def current_deck(body: dict | None = None) -> Deck:
    return DECKS[request_subject(body)]


def deck_topic_ids(deck: Deck) -> set[str]:
    return {key for key, _label in deck.topic_labels}


def request_topic(body: dict | None = None) -> str:
    raw = ""
    if isinstance(body, dict) and body.get("topic"):
        raw = str(body.get("topic"))
    elif request.args.get("topic"):
        raw = str(request.args.get("topic"))
    raw = raw.strip()
    return raw if raw in deck_topic_ids(current_deck(body)) else "name"


def group_ids(deck: Deck, n: int) -> list[str]:
    start = (n - 1) * GROUP_SIZE
    return deck.order[start : start + GROUP_SIZE]


def unlocked_ids(deck: Deck, through: int) -> list[str]:
    return deck.order[: through * GROUP_SIZE]


def topic_map(state: dict, deck: Deck) -> dict:
    if deck.key == "birds":
        return state["birds"]["topics"]
    return state["topics"]


def record_store(state: dict, deck: Deck) -> dict:
    if deck.key == "birds":
        return state["birds"]["records"]
    return state["plants"]


def parse_path_filter(deck: Deck) -> tuple[int, int | None, str]:
    """Return (through_group, single_group_or_None, topic)."""
    state = load_state()
    topic = request_topic()
    cap = int(topic_map(state, deck)[topic])
    through = cap
    raw_through = request.args.get("through")
    if raw_through == "all":
        through = deck.group_count
    elif raw_through:
        try:
            through = max(1, min(deck.group_count, int(raw_through)))
        except ValueError:
            pass
    through = min(through, cap)
    single = None
    if request.args.get("group"):
        try:
            group = int(request.args.get("group"))
            if 1 <= group <= cap:
                single = group
        except ValueError:
            pass
    return through, single, topic


def filtered_cards(deck: Deck | None = None) -> list[dict]:
    deck = deck or current_deck()
    through, single, _topic = parse_path_filter(deck)
    if single:
        allowed = set(group_ids(deck, single))
    else:
        allowed = set(unlocked_ids(deck, through))
    category = request.args.get("category") or "all"
    origin = request.args.get("origin") or "all"
    query = (request.args.get("q") or "").strip().lower()
    rows = []
    for pid in deck.order:
        if pid not in allowed:
            continue
        card = deck.by_id[pid]
        if category != "all" and card.get("category") != category:
            continue
        card_origin = card.get("origin")
        if origin == "nonnative":
            if card_origin not in {"introduced", "invasive"}:
                continue
        elif origin != "all" and card_origin != origin:
            continue
        hay = " ".join(
            [
                card.get("common_name", ""),
                card.get("scientific_name", ""),
                card.get("family", ""),
                " ".join(card.get("also_known_as") or []),
                card.get("habitat", ""),
            ]
        ).lower()
        if query and query not in hay:
            continue
        rows.append(card_payload(card, deck))
    return rows


@app.route("/")
def home():
    return render_template(
        "index.html",
        plant_count=len(PLANT_DECK.rows),
        group_count=PLANT_DECK.group_count,
        group_size=GROUP_SIZE,
    )


@app.route("/images/<path:name>")
def images(name: str):
    return send_from_directory(ROOT / "images", name)


@app.route("/sounds/<path:name>")
def sounds(name: str):
    return send_from_directory(ROOT / "sounds", name)


@app.route("/api/plants")
def api_plants():
    return jsonify(filtered_cards(current_deck()))


@app.route("/api/plant/<pid>")
def api_plant(pid: str):
    deck = current_deck()
    card = deck.by_id.get(pid)
    if not card:
        return jsonify({"error": "not found"}), 404
    return jsonify(card_payload(card, deck, full=True))


@app.route("/api/quiz")
def api_quiz():
    deck = current_deck()
    topic = request_topic()
    pool = [card for card in filtered_cards(deck) if card.get("image")]
    if topic == "call":
        audible = [card for card in pool if card.get("audio")]
        if not audible:
            return jsonify({"error": "No saved calls in this group yet."}), 400
        target = random.choice(audible)
        seen = {target["id"]}
        distractors = []
        others = [card for card in pool if card["id"] not in seen]
        random.shuffle(others)
        rest = [card for card in deck.rows if card.get("image") and card["id"] not in seen]
        random.shuffle(rest)
        for card in others + rest:
            if card["id"] in seen:
                continue
            distractors.append(card)
            seen.add(card["id"])
            if len(distractors) >= 3:
                break
        picks = [target] + distractors
        if len(picks) < 2:
            return jsonify({"error": "Need at least 2 birds with photos to quiz."}), 400
    elif len(pool) < 2:
        return jsonify({"error": f"Need at least 2 unlocked {deck.noun} to quiz."}), 400
    else:
        target = random.choice(pool)
        distractors = [card for card in pool if card["id"] != target["id"]]
        random.shuffle(distractors)
        n_choices = min(4, len(pool))
        if topic == "name":
            picks = [target] + distractors[: n_choices - 1]
        else:
            picks = [target]
            used = {choice_text(target, topic, target, deck)}
            for other in distractors:
                text = choice_text(other, topic, target, deck)
                if not text or text in used:
                    continue
                picks.append(other)
                used.add(text)
                if len(picks) >= n_choices:
                    break
            if len(picks) < 2:
                return jsonify({"error": f"Need at least 2 unlocked {deck.noun} to quiz."}), 400
    random.shuffle(picks)
    field = TOPIC_FIELD.get(topic)
    if topic == "call":
        detail = target.get("id_tips") or ""
    elif topic == "name":
        detail = target["id_tips"]
    else:
        detail = target.get(field) or ""
    return jsonify(
        {
            "subject": deck.key,
            "topic": topic,
            "prompt": deck.prompts[topic],
            "show_name": topic not in {"name", "call"},
            "hide_photo": topic == "call",
            "common_name": target["common_name"] if topic not in {"name", "call"} else "",
            "scientific_name": target["scientific_name"] if topic not in {"name", "call"} else "",
            "id": target["id"],
            "image": target.get("image"),
            "image_credit": target.get("image_credit", ""),
            "audio": target.get("audio") or "",
            "audio_credit": target.get("audio_credit") or "",
            "photos": target.get("photos") or [],
            "choices": [choice_payload(card, topic, target, deck) for card in picks],
            "answer": {
                "id": target["id"],
                "common_name": target["common_name"],
                "scientific_name": target["scientific_name"],
                "origin": target["origin"],
                "detail": detail,
                "id_tips": target["id_tips"],
            },
        }
    )


@app.route("/api/path")
def api_path_get():
    deck = current_deck()
    return jsonify(path_payload(deck, request_topic()))


@app.route("/api/path", methods=["POST"])
def api_path_post():
    body = request.get_json(force=True, silent=True) or {}
    action = body.get("action") or ""
    deck = current_deck(body)
    topic = request_topic(body)
    state = load_state()
    topics = topic_map(state, deck)
    unlocked = int(topics[topic])
    if action == "add":
        topics[topic] = min(deck.group_count, unlocked + 1)
    elif action == "reset":
        topics[topic] = 1
    elif action == "set":
        try:
            n = int(body.get("unlocked_groups"))
        except (TypeError, ValueError):
            return jsonify({"error": "bad request"}), 400
        topics[topic] = deck.clamp(n)
    else:
        return jsonify({"error": "bad request"}), 400
    if deck.key == "birds":
        state["birds"]["unlocked_groups"] = int(state["birds"]["topics"]["name"])
    else:
        state["unlocked_groups"] = int(state["topics"]["name"])
    save_state(state)
    return jsonify(path_payload(deck, topic))


@app.route("/api/progress")
def api_progress_get():
    state = load_state()
    deck = current_deck()
    return jsonify(record_store(state, deck))


def bump_record(rec: dict, result: str) -> dict:
    rec["seen"] = rec.get("seen", 0) + 1
    rec[result] = rec.get(result, 0) + 1
    rec["last"] = datetime.now(timezone.utc).isoformat()
    box = int(rec.get("box", 1))
    rec["box"] = min(5, box + 1) if result == "know" else 1
    return rec


@app.route("/api/progress", methods=["POST"])
def api_progress_post():
    body = request.get_json(force=True, silent=True) or {}
    pid = body.get("id")
    result = body.get("result")  # know | learning
    deck = current_deck(body)
    topic = request_topic(body)
    if pid not in deck.by_id or result not in {"know", "learning"}:
        return jsonify({"error": "bad request"}), 400
    state = load_state()
    store = record_store(state, deck)
    rec = store.get(pid) or {"box": 1, "seen": 0, "know": 0, "learning": 0}
    if topic == "name":
        rec = bump_record(rec, result)
    else:
        topics = rec.get("topics")
        if not isinstance(topics, dict):
            topics = {}
        sub = topics.get(topic)
        if not isinstance(sub, dict):
            sub = {"box": 1, "seen": 0, "know": 0, "learning": 0}
        topics[topic] = bump_record(sub, result)
        rec["topics"] = topics
    store[pid] = rec
    save_state(state)
    return jsonify(rec)


@app.route("/api/quiz-log", methods=["POST"])
def api_quiz_log():
    body = request.get_json(force=True, silent=True) or {}
    deck = current_deck(body)
    topic = request_topic(body)
    pid = body.get("id")
    correct = body.get("correct")
    if pid not in deck.by_id or not isinstance(correct, bool):
        return jsonify({"error": "bad request"}), 400
    state = load_state()
    log = state.get("quiz_log")
    if not isinstance(log, list):
        log = []
    log.append(
        {
            "t": datetime.now(timezone.utc).isoformat(),
            "subject": deck.key,
            "topic": topic,
            "id": pid,
            "correct": correct,
        }
    )
    if len(log) > QUIZ_LOG_LIMIT:
        log = log[-QUIZ_LOG_LIMIT:]
    state["quiz_log"] = log
    save_state(state)
    return jsonify({"ok": True, "attempts": len(log)})


def _card_name(subject: str, pid: str) -> str:
    deck = DECKS.get(subject)
    card = deck.by_id.get(pid) if deck else None
    if not card:
        return pid
    return card.get("common_name") or pid


def _downsample(points: list[tuple[int, float]], limit: int = 48) -> list[dict]:
    if len(points) <= limit:
        chosen = points
    else:
        step = (len(points) - 1) / (limit - 1)
        chosen = []
        seen = set()
        for index in range(limit):
            item = points[round(index * step)]
            if item[0] in seen:
                continue
            seen.add(item[0])
            chosen.append(item)
    return [{"n": n, "accuracy": round(accuracy, 4)} for n, accuracy in chosen]


def quiz_stats(state: dict) -> dict:
    log = state.get("quiz_log")
    if not isinstance(log, list):
        log = []
    labels = {"plants": dict(TOPICS), "birds": dict(BIRD_TOPICS)}
    topics = {
        subject: {
            key: {"label": label, "attempts": 0, "correct": 0}
            for key, label in pairs.items()
        }
        for subject, pairs in labels.items()
    }
    running_correct = 0
    running = []
    daily: dict[str, dict] = {}
    species: dict[tuple[str, str], dict] = {}
    for item in log:
        subject = item["subject"]
        topic = item["topic"]
        correct = bool(item["correct"])
        bucket = topics[subject][topic]
        bucket["attempts"] += 1
        bucket["correct"] += int(correct)
        running_correct += int(correct)
        running.append((len(running) + 1, running_correct / (len(running) + 1)))
        day = str(item.get("t") or "")[:10]
        day_bucket = daily.setdefault(day, {"day": day, "attempts": 0, "correct": 0})
        day_bucket["attempts"] += 1
        day_bucket["correct"] += int(correct)
        key = (subject, item["id"])
        spec = species.setdefault(
            key,
            {
                "subject": subject,
                "id": item["id"],
                "common_name": _card_name(subject, item["id"]),
                "attempts": 0,
                "correct": 0,
            },
        )
        spec["attempts"] += 1
        spec["correct"] += int(correct)
    attempts = len(log)
    correct_n = sum(1 for item in log if item["correct"])
    weak = [row for row in species.values() if row["attempts"] >= 2]
    weak.sort(key=lambda row: (row["correct"] / row["attempts"], -row["attempts"]))
    recent = []
    for item in reversed(log[-8:]):
        recent.append(
            {
                "t": item["t"],
                "subject": item["subject"],
                "topic": item["topic"],
                "topic_label": labels[item["subject"]].get(item["topic"], item["topic"]),
                "id": item["id"],
                "common_name": _card_name(item["subject"], item["id"]),
                "correct": item["correct"],
            }
        )
    mastery = {}
    for deck in (PLANT_DECK, BIRD_DECK):
        store = record_store(state, deck)
        mastery[deck.key] = {}
        for key, label in deck.topic_labels:
            known = 0
            for pid in deck.order:
                if known_for(store.get(pid) or {}, key) > 0:
                    known += 1
            mastery[deck.key][key] = {
                "label": label,
                "known": known,
                "total": len(deck.order),
            }
    return {
        "attempts": attempts,
        "correct": correct_n,
        "running": _downsample(running),
        "daily": [daily[day] for day in sorted(daily)],
        "topics": topics,
        "mastery": mastery,
        "weak": weak[:6],
        "recent": recent,
    }


@app.route("/api/quiz-stats")
def api_quiz_stats():
    return jsonify(quiz_stats(load_state()))


def known_for(rec: dict, topic: str) -> int:
    if topic == "name":
        return int((rec or {}).get("know") or 0)
    sub = ((rec or {}).get("topics") or {}).get(topic) or {}
    if not isinstance(sub, dict):
        return 0
    return int(sub.get("know") or 0)


def path_payload(deck: Deck, topic: str | None = None) -> dict:
    state = load_state()
    topic = topic if topic in deck_topic_ids(deck) else "name"
    topics = topic_map(state, deck)
    unlocked = int(topics[topic])
    progress = record_store(state, deck)
    groups = []
    for n in range(1, deck.group_count + 1):
        ids = group_ids(deck, n)
        members = []
        known = 0
        for pid in ids:
            card = deck.by_id[pid]
            rec = progress.get(pid) or {}
            if known_for(rec, topic) > 0:
                known += 1
            members.append(
                {
                    "id": pid,
                    "common_name": card["common_name"],
                    "scientific_name": card["scientific_name"],
                    "category": card["category"],
                    "origin": card["origin"],
                    "image": card.get("image") or "",
                    "know": known_for(rec, topic),
                    "seen": int(rec.get("seen") or 0),
                }
            )
        groups.append(
            {
                "number": n,
                "title": deck.titles.get(n, f"Group {n}"),
                "unlocked": n <= unlocked,
                "known": known,
                "size": len(ids),
                "members": members,
            }
        )
    return {
        "subject": deck.key,
        "noun": deck.noun,
        "topic": topic,
        "topic_label": dict(deck.topic_labels)[topic],
        "topics": [
            {
                "id": key,
                "label": label,
                "unlocked_groups": int(topics[key]),
            }
            for key, label in deck.topic_labels
        ],
        "unlocked_groups": unlocked,
        "group_count": deck.group_count,
        "group_size": GROUP_SIZE,
        "unlocked_count": len(unlocked_ids(deck, unlocked)),
        "total": len(deck.order),
        "groups": groups,
    }


def _is_abbrev(text: str, period_at: int) -> bool:
    word = text[:period_at].split()[-1] if text[:period_at].strip() else ""
    bare = re.sub(r"[^A-Za-z.]", "", word).rstrip(".")
    if bare.lower() in {"mr", "mrs", "ms", "dr", "st", "vs", "etc", "e.g", "i.e", "u.s", "n.c", "sp", "spp"}:
        return True
    return len(bare) <= 2 and bare.isalpha() and bare[:1].isupper()


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", (text or "").strip())
    parts: list[str] = []
    start = 0
    i = 0
    while i < len(text):
        if text[i] in ".!?":
            nxt_i = i + 1
            if _is_abbrev(text[start:i], i - start):
                i += 1
                continue
            if nxt_i >= len(text) or text[nxt_i].isspace():
                j = nxt_i
                while j < len(text) and text[j].isspace():
                    j += 1
                if j >= len(text) or text[j].isupper():
                    parts.append(text[start : i + 1].strip())
                    start = j
                    i = j
                    continue
        i += 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def snippet(text: str, limit: int = 200) -> str:
    parts = sentences(text)
    if not parts:
        return ""
    out = ""
    for part in parts:
        out = part if not out else f"{out} {part}"
        if len(out) >= 90:
            break
    if len(out) > limit:
        cut = out[:limit].rsplit(" ", 1)[0].rstrip(",;:")
        out = cut + "…"
    return out


_NAME_SUFFIXES = ("tree", "weed", "wood", "bush", "root", "berry", "apple", "fern", "grass", "vine", "wort", "gum", "shrub")


def _name_variants(phrase: str) -> set[str]:
    phrase = re.sub(r"\s+", " ", (phrase or "").strip(" ."))
    if len(phrase) < 3:
        return set()
    found = {phrase}
    if " " in phrase:
        found.add(phrase.replace(" ", "-"))
    if "-" in phrase:
        found.add(phrase.replace("-", " "))
    for suffix in _NAME_SUFFIXES:
        for item in list(found):
            low = item.lower()
            for tail in (suffix, "-" + suffix, " " + suffix):
                if low.endswith(tail) and len(item) - len(tail) >= 4:
                    found.add(item[: len(item) - len(tail)].strip("- "))
    return {item for item in found if len(item) >= 3}


def censor_phrases(card: dict, skip: set[str] | None = None) -> list[str]:
    """Names to hide in a fact, longest first."""
    skip = _TOKEN_SKIP if skip is None else skip
    phrases: set[str] = set()
    common = card.get("common_name") or ""
    for raw in (
        common,
        card.get("scientific_name") or "",
        *(card.get("also_known_as") or []),
    ):
        phrases |= _name_variants(raw)
    parts = [part for part in re.split(r"[\s-]+", common) if part]
    if parts and parts[0].lower() in _NAME_QUALIFIERS and len(parts) > 1:
        phrases |= _name_variants(" ".join(parts[1:]))
    for part in parts:
        if len(part) >= 3 and part.lower() not in skip:
            phrases |= _name_variants(part)
    return sorted(phrases, key=len, reverse=True)


def _blank_phrases(text: str, phrases) -> str:
    for phrase in phrases:
        if phrase.lower().endswith("s"):
            suffix = r"(?:'s|’s)?"
        else:
            suffix = r"(?:'s|’s|s)?"

        def _blank(match: re.Match) -> str:
            return BLANK + (" " if match.group(0).endswith("-") else "")

        text = re.sub(
            rf"\b{re.escape(phrase)}{suffix}(?:-|(?=\b))",
            _blank,
            text,
            flags=re.IGNORECASE,
        )
    return text


def _tidy_blanks(text: str) -> str:
    blank = re.escape(BLANK)
    text = re.sub(rf"(?:{blank}(?:[\s\-–]+))+{blank}", BLANK, text)
    text = re.sub(rf"\(\s*{blank}\s*\)", BLANK, text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def choice_text(card: dict, topic: str, target: dict | None = None, deck: Deck | None = None) -> str:
    deck = deck or PLANT_DECK
    if topic == "name":
        return card.get("common_name") or ""
    field = TOPIC_FIELD[topic]
    text = snippet(card.get(field) or "")
    text = _blank_phrases(text, censor_phrases(card, deck.token_skip))
    if target and target.get("id") != card.get("id"):
        text = _blank_phrases(text, censor_phrases(target, deck.token_skip))
    text = _blank_phrases(text, deck.giveaways)
    return _tidy_blanks(text)


def choice_payload(card: dict, topic: str, target: dict | None = None, deck: Deck | None = None) -> dict:
    deck = deck or PLANT_DECK
    payload = {
        "id": card["id"],
        "common_name": card["common_name"],
        "scientific_name": card["scientific_name"],
        "origin": card["origin"],
    }
    if topic == "call":
        payload["image"] = card.get("image") or ""
        return payload
    if topic != "name":
        payload["text"] = choice_text(card, topic, target, deck)
        payload["common_name"] = ""
        payload["scientific_name"] = ""
    return payload


def photos_for(card: dict) -> list[dict]:
    raw = card.get("photos") or []
    photos = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        filename = item.get("file") or ""
        if not filename:
            continue
        photos.append(
            {
                "file": filename,
                "label": item.get("label") or "Photo",
                "credit": item.get("credit") or card.get("image_credit") or "",
            }
        )
    if not photos and card.get("image"):
        photos.append(
            {
                "file": card["image"],
                "label": "Photo",
                "credit": card.get("image_credit") or "",
            }
        )
    return photos


def card_payload(card: dict, deck: Deck, full: bool = True) -> dict:
    group = deck.id_to_group[card["id"]]
    out = {
        "id": card["id"],
        "common_name": card["common_name"],
        "scientific_name": card["scientific_name"],
        "family": card.get("family", ""),
        "category": card.get("category", ""),
        "origin": card.get("origin", ""),
        "abundance": card.get("abundance", ""),
        "also_known_as": card.get("also_known_as") or [],
        "image": card.get("image") or "",
        "image_credit": card.get("image_credit") or "",
        "audio": card.get("audio") or "",
        "audio_credit": card.get("audio_credit") or "",
        "photos": photos_for(card),
        "group": group,
        "group_title": deck.titles.get(group, f"Group {group}"),
    }
    if full:
        out.update(
            {
                "id_tips": card.get("id_tips", ""),
                "habitat": card.get("habitat", ""),
                "wnc": card.get("wnc", ""),
                "uses": card.get("uses", ""),
                "caution": card.get("caution", ""),
                "lookalikes": card.get("lookalikes", ""),
                "wikipedia_url": card.get("wikipedia_url", ""),
                "wikipedia_extract": card.get("wikipedia_extract", ""),
            }
        )
    return out


def main() -> None:
    print(
        f"Flashcards — {len(PLANT_DECK.rows)} plants in {PLANT_DECK.group_count} groups, "
        f"{len(BIRD_DECK.rows)} birds in {BIRD_DECK.group_count} groups"
    )
    print("Open http://127.0.0.1:5055")
    app.run(host="127.0.0.1", port=5055, debug=False)


if __name__ == "__main__":
    main()
