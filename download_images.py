#!/usr/bin/env python3
"""Download Wikipedia lead photos for each plant (Wikimedia Commons)."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "data"))
from seed_plants import PLANTS  # noqa: E402

IMAGES = ROOT / "images"
DATA = ROOT / "data" / "plants.json"
API = "https://en.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": "WNCPlantFlashcards/1.0 (educational local app; brandon@localhost)"
}


def api_get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_commons_thumb(filename: str) -> tuple[str, str] | None:
    """Return (thumb_url, file_title) for an explicit Commons filename."""
    title = filename if filename.startswith("File:") else f"File:{filename}"
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": "960",
    }
    data = api_get(params)
    for page in data.get("query", {}).get("pages", {}).values():
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        url = info.get("thumburl") or info.get("url")
        if url:
            return url, page.get("title", title).replace("File:", "")
    return None


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
    data = api_get(params)
    pages = data.get("query", {}).get("pages", {})
    redirects = {
        r["from"]: r["to"] for r in data.get("query", {}).get("redirects", [])
    }
    normalized = {
        n["from"]: n["to"] for n in data.get("query", {}).get("normalized", [])
    }
    by_title: dict[str, dict] = {}
    for page in pages.values():
        if "title" in page:
            by_title[page["title"]] = page

    result: dict[str, dict] = {}
    for original in titles:
        title = original
        if title in normalized:
            title = normalized[title]
        if title in redirects:
            title = redirects[title]
        result[original] = by_title.get(title, {})
    return result


def standard_thumb(url: str) -> str:
    """Wikimedia rejects non-standard sizes and many original files (HTTP 429)."""
    url = url.split("?")[0]
    if "/thumb/" in url:
        return url
    # Original commons URL -> 500px thumb (a documented standard size).
    marker = "/wikipedia/commons/"
    if marker not in url:
        return url
    rest = url.split(marker, 1)[1]
    name = rest.rsplit("/", 1)[-1]
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{rest}/500px-{name}"


def download_file(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    candidates = [standard_thumb(url)]
    if candidates[0] != url.split("?")[0]:
        candidates.append(url.split("?")[0])
    for candidate in candidates:
        for attempt in range(3):
            req = urllib.request.Request(candidate, headers=HEADERS)
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = resp.read()
                    ctype = resp.headers.get("Content-Type", "")
            except urllib.error.HTTPError as exc:
                print(f"  HTTP {exc.code} for {candidate}")
                if exc.code == 429:
                    time.sleep(2 + attempt * 2)
                    continue
                break
            if not data or len(data) < 800:
                break
            if "svg" in ctype or "html" in ctype:
                break
            dest.write_bytes(data)
            return True
    return False


def ext_for(url: str) -> str:
    path = urllib.parse.urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    records = []
    titles = [p["wikipedia"] for p in PLANTS]
    info: dict[str, dict] = {}
    chunk = 16
    for i in range(0, len(titles), chunk):
        batch = titles[i : i + chunk]
        print(f"Wikipedia lookup {i + 1}–{i + len(batch)} of {len(titles)}")
        try:
            info.update(fetch_batch(batch))
        except Exception as exc:
            print(f"  batch failed: {exc}")
            time.sleep(2)
            info.update(fetch_batch(batch))
        time.sleep(0.4)

    previous: dict[str, dict] = {}
    if DATA.exists():
        try:
            previous = {
                row["id"]: row
                for row in json.loads(DATA.read_text(encoding="utf-8"))
                if isinstance(row, dict) and row.get("id")
            }
        except json.JSONDecodeError:
            previous = {}

    missing = []
    for plant in PLANTS:
        rec = dict(plant)
        wiki = info.get(plant["wikipedia"], {})
        extract = (wiki.get("extract") or "").strip()
        if extract:
            rec["wikipedia_extract"] = extract[:900]
        rec["wikipedia_url"] = wiki.get("fullurl") or (
            "https://en.wikipedia.org/wiki/"
            + urllib.parse.quote(plant["wikipedia"].replace(" ", "_"))
        )
        thumb = (wiki.get("thumbnail") or {}).get("source")
        image_page = wiki.get("pageimage")
        rec["image_credit"] = ""
        rec["image"] = ""
        override_name = plant.get("commons_file")
        if override_name:
            try:
                override = fetch_commons_thumb(override_name)
            except Exception as exc:
                print(f"  commons override failed for {plant['id']}: {exc}")
                override = None
            if override:
                thumb, image_page = override
        if thumb:
            ext = ext_for(thumb)
            dest = IMAGES / f"{plant['id']}{ext}"
            if dest.exists() and dest.stat().st_size > 800:
                rec["image"] = dest.name
            elif download_file(thumb, dest):
                rec["image"] = dest.name
                print(f"  saved {dest.name}")
                time.sleep(0.15)
            if rec["image"] and image_page:
                rec["image_credit"] = (
                    f"Photo via Wikipedia / Wikimedia Commons "
                    f"(File:{image_page}). Used for local study."
                )
            elif rec["image"]:
                rec["image_credit"] = "Photo via Wikipedia / Wikimedia Commons."
        if not rec["image"]:
            missing.append(plant["id"])
            print(f"  NO IMAGE: {plant['id']} ({plant['wikipedia']})")
        old = previous.get(plant["id"]) or {}
        if old.get("photos"):
            rec["photos"] = old["photos"]
        records.append(rec)

    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {DATA} ({len(records)} plants)")
    print(f"Images: {len(records) - len(missing)} ok, {len(missing)} missing")
    if missing:
        print("Missing:", ", ".join(missing))


if __name__ == "__main__":
    main()
