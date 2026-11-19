#!/usr/bin/env python3
"""Continue bird calls and extra plant photos.

Takes one bird, then one plant, so both move before a rate limit.
The first HTTP 429 stops the run. Nothing is retried.
Does not read or write progress.json.
Existing call files and existing plant galleries are left as they are.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))

import download_bird_calls as calls  # noqa: E402
import download_birds as photos  # noqa: E402
from learn_path import LEARN_ORDER as ORDER  # noqa: E402

PLANTS = ROOT / "data" / "plants.json"
IMAGES = ROOT / "images"
START = "japanese-barberry"

BAD = (
    "map", "diagram", "illustration", "drawing", "icon", "logo", "stamp",
    "painting", "sketch", "chart", "graph", "microscope", "collage",
    "distribution", "range", "flag", "coin", "svg", "herbarium",
    "engraving", "lithograph", "watercolor", "artwork", "postage",
    "schematic", "cladogram", "phylogen", "range map",
)

STEMS = {
    "leaves": ("leaf", "leaves", "foliage"),
    "needles": ("needle", "needles", "foliage", "branch"),
    "flowers": ("flower", "bloom", "blossom"),
    "flower": ("flower", "bloom", "blossom"),
    "fruit": ("fruit", "berry", "berries"),
    "frond": ("frond", "fern"),
    "bark": ("bark", "trunk"),
    "habit": (),
    "plant": (),
}

VIEWS = {
    "tree": [("bark", "Bark", "bark"), ("leaves", "Leaves", "leaves"), ("habit", "Tree", "plant")],
    "shrub": [("leaves", "Leaves", "leaves"), ("flowers", "Flowers", "flowers"), ("fruit", "Fruit", "fruit")],
    "vine": [("leaves", "Leaves", "leaves"), ("flowers", "Flowers", "flowers")],
    "wildflower": [("flower", "Flower", "flowers"), ("leaves", "Leaves", "leaves")],
    "fern": [("frond", "Fronds", "fronds"), ("plant", "Plant", "plant")],
    "grass": [("plant", "Plant", "plant"), ("flower", "Flowers", "flowers")],
}
CONIFER = ("pine", "fir", "spruce", "hemlock", "cedar")


def plant_views(plant: dict) -> list[tuple[str, str, str]]:
    views = list(VIEWS.get(plant.get("category") or "", VIEWS["shrub"]))
    name = (plant.get("common_name") or "").lower()
    if plant.get("category") == "tree" and any(word in name for word in CONIFER):
        views[1] = ("needles", "Needles", "needles")
    return views


def lead_filename(credit: str) -> str:
    marker = "File:"
    if marker not in (credit or ""):
        return ""
    return credit.split(marker, 1)[1].split(")", 1)[0].strip().lower()


def search_images(query: str) -> list[dict]:
    data = calls.api_get(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": "6",
            "gsrlimit": "8",
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
        }
    )
    pages = list((data.get("query") or {}).get("pages", {}).values())
    pages.sort(key=lambda page: page.get("index", 999))
    return pages


def good_page(page: dict, genus: str, species: str, keyword: str, used: str) -> bool:
    info = (page.get("imageinfo") or [None])[0]
    if not info:
        return False
    mime = (info.get("mime") or "").lower()
    if mime not in ("image/jpeg", "image/png", "image/webp"):
        return False
    size = int(info.get("size") or 0)
    if size < 15_000 or size > 20_000_000:
        return False
    title = (page.get("title") or "").replace("File:", "")
    low = title.lower()
    if genus not in low or species not in low:
        return False
    if any(word in low for word in BAD):
        return False
    if used and title.lower() == used:
        return False
    stems = STEMS.get(keyword, (keyword,))
    if stems and not any(stem in low for stem in stems):
        return False
    return True


def save_plant_view(plant: dict) -> str:
    """Return saved, miss, or raise RateLimit."""
    if plant.get("photos"):
        return "skip"
    binomial = (plant.get("scientific_name") or "").split()
    if len(binomial) < 2:
        print(f"  NO NAME: {plant['id']}", flush=True)
        return "miss"
    genus, species = binomial[0].lower(), binomial[1].lower()
    used = lead_filename(plant.get("image_credit") or "")
    for keyword, label, slug in plant_views(plant):
        query = f'"{binomial[0]} {binomial[1]}" {keyword}'
        print(f"  search {query}", flush=True)
        pages = search_images(query)
        time.sleep(1.5)
        for page in pages:
            if not good_page(page, genus, species, keyword, used):
                continue
            info = page["imageinfo"][0]
            url = photos.standard_thumb(info.get("url") or "")
            dest = IMAGES / f"{plant['id']}-{slug}.jpg"
            print(f"  get {page.get('title')}", flush=True)
            data, ctype = photos.fetch_bytes(url)
            if not data or "html" in ctype or "svg" in ctype or not photos.save_jpeg(data, dest):
                continue
            title = (page.get("title") or "").replace("File:", "")
            credit = (
                "Photo via Wikipedia / Wikimedia Commons "
                f"(File:{title}). Used for local study."
            )
            lead = plant.get("image")
            photos_list = [{"file": dest.name, "label": label, "credit": credit}]
            if lead:
                photos_list.append({
                    "file": lead,
                    "label": "Plant",
                    "credit": plant.get("image_credit") or credit,
                })
            plant["photos"] = photos_list
            print(f"  saved {dest.name} ({label})", flush=True)
            return "saved"
    print(f"  NO EXTRA: {plant['id']}", flush=True)
    return "miss"


def load_plants() -> list[dict]:
    rows = json.loads(PLANTS.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit("plants.json is not a list")
    return rows


def write_plants(rows: list[dict]) -> None:
    payload = json.dumps(rows, indent=2, ensure_ascii=False) + "\n"
    tmp = PLANTS.with_suffix(".json.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(PLANTS)


def bird_queue(rows: dict[str, dict]) -> list[str]:
    pending = []
    for pid in calls.BIRD_ORDER:
        bird = rows[pid]
        dest = calls.SOUNDS / f"{pid}.mp3"
        if bird.get("audio") == dest.name and dest.exists() and dest.stat().st_size > 4000:
            continue
        pending.append(pid)
    return pending


def save_bird(bird: dict) -> str:
    pid = bird["id"]
    dest = calls.SOUNDS / f"{pid}.mp3"
    print(bird["common_name"], flush=True)
    pages = calls.choose_pages(bird)
    time.sleep(1.5)
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        data = calls.fetch_bytes(info.get("url") or "")
        if not data:
            continue
        raw = calls.SOUNDS / f"{pid}.part"
        raw.write_bytes(data)
        if not calls.trim_clip(raw, dest):
            raw.unlink(missing_ok=True)
            continue
        raw.unlink(missing_ok=True)
        bird["audio"] = dest.name
        bird["audio_credit"] = calls.credit_for(page)
        print(f"  saved {dest.name}", flush=True)
        return "saved"
    print(f"  NO CALL: {pid}", flush=True)
    bird.pop("audio", None)
    bird.pop("audio_credit", None)
    return "miss"


def main() -> int:
    plants = load_plants()
    by_plant = {row["id"]: row for row in plants if row.get("id")}
    if START not in ORDER:
        print("start plant missing from learn path")
        return 1
    start_at = ORDER.index(START)
    plant_ids = [
        pid for pid in ORDER[start_at:]
        if pid in by_plant and not by_plant[pid].get("photos")
    ]
    bird_rows = {
        row["id"]: row
        for row in json.loads(calls.DATA.read_text(encoding="utf-8"))
        if isinstance(row, dict) and row.get("id")
    }
    if set(bird_rows) != set(calls.BIRD_ORDER):
        print("birds.json does not match the study order")
        return 1
    birds = bird_queue(bird_rows)
    print(f"pending birds {len(birds)}, pending plants {len(plant_ids)}", flush=True)
    calls.SOUNDS.mkdir(parents=True, exist_ok=True)
    saved_birds = 0
    saved_plants = 0
    try:
        while birds or plant_ids:
            if birds:
                pid = birds.pop(0)
                kind = save_bird(bird_rows[pid])
                calls.write_records(bird_rows)
                if kind == "saved":
                    saved_birds += 1
                time.sleep(1.2)
            if plant_ids:
                pid = plant_ids.pop(0)
                print(by_plant[pid]["common_name"], flush=True)
                kind = save_plant_view(by_plant[pid])
                write_plants(plants)
                if kind == "saved":
                    saved_plants += 1
                time.sleep(1.2)
    except (calls.RateLimit, photos.RateLimit):
        print("HTTP 429. Stopping.", flush=True)
        calls.write_records(bird_rows)
        write_plants(plants)
        print(f"stopped with {saved_birds} new calls and {saved_plants} new plant photos", flush=True)
        return 2
    print(f"finished {saved_birds} new calls and {saved_plants} new plant photos", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
