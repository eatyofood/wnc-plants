#!/usr/bin/env python3
"""Download one Wikipedia lead photo per North Carolina bird.

Stops on the first HTTP 429. A 404 or a rejected file is skipped.
Each accepted photo is written into data/birds.json immediately.
Does not read or write data/plants.json.
"""

from __future__ import annotations

import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "data"))
from bird_path import BIRD_ORDER  # noqa: E402
from seed_birds import BIRDS  # noqa: E402

IMAGES = ROOT / "images"
DATA = ROOT / "data" / "birds.json"
WIKI = "https://en.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
HEADERS = {
    "User-Agent": "WNCPlantFlashcards/1.0 (educational local app; brandon@localhost)"
}
BAD_WORDS = {
    "map", "maps", "distribution", "range", "locator", "icon", "stamp",
    "illustration", "illustrations", "diagram", "painting", "drawing",
    "sketch", "artwork", "engraving", "lithograph", "plate", "audio",
    "spectrogram", "skeleton", "specimen", "chart", "charts", "pdf",
    "scan", "scans",
}
OK_MIME = {"image/jpeg", "image/png", "image/webp"}


class RateLimit(Exception):
    pass


def api_get(base: str, params: dict) -> dict:
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimit(url) from exc
        raise


def bad_filename(name: str) -> bool:
    words = re.split(r"[^a-z0-9]+", name.lower())
    return any(word in BAD_WORDS for word in words)


def fetch_batch(titles: list[str]) -> dict[str, dict]:
    params = {
        "action": "query",
        "format": "json",
        "redirects": "1",
        "titles": "|".join(titles),
        "prop": "pageimages|extracts|info",
        "inprop": "url",
        "pithumbsize": "960",
        "pilicense": "any",
        "exintro": "1",
        "explaintext": "1",
        "exlimit": str(len(titles)),
        "pilimit": str(len(titles)),
    }
    data = api_get(WIKI, params)
    pages = data.get("query", {}).get("pages", {})
    redirects = {r["from"]: r["to"] for r in data.get("query", {}).get("redirects", [])}
    normalized = {n["from"]: n["to"] for n in data.get("query", {}).get("normalized", [])}
    by_title = {}
    for page in pages.values():
        if "title" in page:
            by_title[page["title"]] = page
    result = {}
    for original in titles:
        title = normalized.get(original, original)
        title = redirects.get(title, title)
        result[original] = by_title.get(title, {})
    return result


def search_photo(title: str) -> tuple[str, str] | None:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{title} bird",
        "gsrnamespace": "6",
        "gsrlimit": "12",
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": "960",
    }
    data = api_get(COMMONS, params)
    pages = list((data.get("query") or {}).get("pages", {}).values())
    pages.sort(key=lambda page: page.get("index", 999))
    for page in pages:
        name = (page.get("title") or "").replace("File:", "")
        if not name or bad_filename(name):
            continue
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        mime = (info.get("mime") or "").lower()
        if mime not in OK_MIME:
            continue
        url = info.get("thumburl") or info.get("url")
        if url:
            return url, name
    return None


def fetch_bytes(url: str) -> tuple[bytes | None, str]:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimit(url) from exc
        print(f"  HTTP {exc.code} for {url}")
        return None, ""


def standard_thumb(url: str) -> str:
    url = url.split("?")[0]
    if "/thumb/" in url:
        return url
    marker = "/wikipedia/commons/"
    if marker not in url:
        return url
    rest = url.split(marker, 1)[1]
    name = rest.rsplit("/", 1)[-1]
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{rest}/960px-{name}"


def save_jpeg(data: bytes, dest: Path) -> bool:
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
        image = image.convert("RGB")
        image.thumbnail((1200, 1200))
        dest.parent.mkdir(parents=True, exist_ok=True)
        image.save(dest, "JPEG", quality=86)
    except Exception as exc:
        print(f"  could not read image for {dest.name}: {exc}")
        if dest.exists():
            dest.unlink()
        return False
    return dest.stat().st_size > 800


def download_photo(url: str, dest: Path) -> bool:
    candidates = [standard_thumb(url)]
    plain = url.split("?")[0]
    if plain not in candidates:
        candidates.append(plain)
    for candidate in candidates:
        data, ctype = fetch_bytes(candidate)
        if data is None:
            continue
        if "svg" in ctype or "gif" in ctype or "html" in ctype or len(data) < 800:
            continue
        if save_jpeg(data, dest):
            return True
    return False


def write_records(records: list[dict]) -> None:
    payload = json.dumps(records, indent=2, ensure_ascii=False) + "\n"
    tmp = DATA.with_suffix(".json.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(DATA)


def main() -> int:
    by_seed = {bird["id"]: bird for bird in BIRDS}
    missing = [pid for pid in BIRD_ORDER if pid not in by_seed]
    extra = [pid for pid in by_seed if pid not in BIRD_ORDER]
    if missing or extra or len(BIRD_ORDER) != len(set(BIRD_ORDER)):
        print(f"seed mismatch missing={missing} extra={extra}")
        return 1

    plants_path = ROOT / "data" / "plants.json"
    plant_ids = set()
    if plants_path.exists():
        plant_ids = {
            row.get("id")
            for row in json.loads(plants_path.read_text(encoding="utf-8"))
            if isinstance(row, dict)
        }
    overlap = sorted(set(BIRD_ORDER) & plant_ids)
    if overlap:
        print("bird ids collide with plants:", ", ".join(overlap))
        return 1

    previous = {}
    if DATA.exists():
        try:
            previous = {
                row["id"]: row
                for row in json.loads(DATA.read_text(encoding="utf-8"))
                if isinstance(row, dict) and row.get("id")
            }
        except json.JSONDecodeError:
            previous = {}

    titles = [by_seed[pid]["wikipedia"] for pid in BIRD_ORDER]
    info: dict[str, dict] = {}
    limited = False
    for start in range(0, len(titles), 16):
        batch = titles[start : start + 16]
        print(f"Wikipedia lookup {start + 1}–{start + len(batch)} of {len(titles)}", flush=True)
        try:
            info.update(fetch_batch(batch))
        except RateLimit:
            print("HTTP 429 on Wikipedia lookup. Stopping.", flush=True)
            limited = True
            break
        time.sleep(2.0)

    rows = {pid: dict(by_seed[pid]) for pid in BIRD_ORDER}

    def publish() -> None:
        write_records([rows[pid] for pid in BIRD_ORDER])

    saved = 0
    for pid in BIRD_ORDER:
        bird = rows[pid]
        old = previous.get(pid) or {}
        wiki = info.get(bird["wikipedia"], {})
        extract = (wiki.get("extract") or "").strip()
        if extract:
            bird["wikipedia_extract"] = extract[:900]
        elif old.get("wikipedia_extract"):
            bird["wikipedia_extract"] = old["wikipedia_extract"]
        bird["wikipedia_url"] = wiki.get("fullurl") or old.get("wikipedia_url") or (
            "https://en.wikipedia.org/wiki/"
            + urllib.parse.quote(bird["wikipedia"].replace(" ", "_"))
        )
        dest = IMAGES / f"{pid}.jpg"
        if old.get("image") == dest.name and dest.exists() and dest.stat().st_size > 800:
            bird["image"] = dest.name
            bird["image_credit"] = old.get("image_credit") or ""
            if old.get("photos"):
                bird["photos"] = old["photos"]
            saved += 1
            publish()
            continue

        pageimage = wiki.get("pageimage") or ""
        thumb = (wiki.get("thumbnail") or {}).get("source") or ""
        credit_name = pageimage
        if pageimage and bad_filename(pageimage):
            print(f"  skip lead {pageimage}", flush=True)
            thumb = ""
            credit_name = ""
        if not thumb and not limited:
            print(f"  search photo for {bird['common_name']}", flush=True)
            time.sleep(2.0)
            try:
                found = search_photo(bird["wikipedia"])
            except RateLimit:
                print("HTTP 429 on Commons search. Stopping.", flush=True)
                bird["image"] = ""
                bird["image_credit"] = ""
                publish()
                return 2
            if found:
                thumb, credit_name = found
        bird["image"] = ""
        bird["image_credit"] = ""
        if thumb and not limited:
            try:
                ok = download_photo(thumb, dest)
            except RateLimit:
                print("HTTP 429 on image download. Stopping.", flush=True)
                if dest.exists() and dest.stat().st_size < 800:
                    dest.unlink()
                publish()
                return 2
            if ok:
                bird["image"] = dest.name
                bird["image_credit"] = (
                    f"Photo via Wikipedia / Wikimedia Commons (File:{credit_name}). "
                    "Used for local study."
                ) if credit_name else "Photo via Wikipedia / Wikimedia Commons."
                bird["photos"] = [{
                    "file": dest.name,
                    "label": "Photo",
                    "credit": bird["image_credit"],
                }]
                saved += 1
                print(f"  saved {dest.name}", flush=True)
                publish()
                time.sleep(1.2)
                continue
            print(f"  NO IMAGE: {pid}", flush=True)
            if dest.exists() and dest.stat().st_size < 800:
                dest.unlink()
        else:
            print(f"  NO IMAGE: {pid}", flush=True)
        publish()

    publish()
    print(f"Wrote {DATA} ({len(BIRD_ORDER)} birds, {saved} photos)", flush=True)
    return 2 if limited else 0


if __name__ == "__main__":
    sys.exit(main())
