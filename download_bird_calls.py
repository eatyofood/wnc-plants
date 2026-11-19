#!/usr/bin/env python3
"""Save a short call or song for each North Carolina bird.

Clips come from Wikimedia Commons. The first HTTP 429 stops the run.
A missing or rejected file is skipped. birds.json is updated after each
clip. This does not read or write plants.json or progress.json.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "data"))
from bird_path import BIRD_ORDER  # noqa: E402
from seed_birds import BIRDS  # noqa: E402

SOUNDS = ROOT / "sounds"
DATA = ROOT / "data" / "birds.json"
COMMONS = "https://commons.wikimedia.org/w/api.php"
HEADERS = {
    "User-Agent": "WNCPlantFlashcards/1.0 (educational local app; brandon@localhost)"
}
OK_MIME = {
    "audio/mpeg",
    "audio/ogg",
    "application/ogg",
    "audio/wav",
    "audio/x-wav",
    "audio/flac",
    "audio/mp4",
    "audio/webm",
}


class RateLimit(Exception):
    pass


def api_get(params: dict) -> dict:
    url = COMMONS + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimit(url) from exc
        raise


def plain(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def binomials(bird: dict) -> list[str]:
    found = []
    for raw in (bird.get("scientific_name"), *(bird.get("also_known_as") or [])):
        parts = re.sub(r"[()]", "", raw or "").split()
        if len(parts) >= 2 and parts[0][:1].isupper() and parts[1][:1].islower():
            name = f"{parts[0]} {parts[1]}"
            if name not in found:
                found.append(name)
    return found


def search_audio(query: str) -> list[dict]:
    data = api_get(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": "6",
            "gsrlimit": "12",
            "prop": "imageinfo",
            "iiprop": "url|mime|size|extmetadata",
            "iiextmetadatafilter": "LicenseShortName|Artist",
        }
    )
    pages = list((data.get("query") or {}).get("pages", {}).values())
    pages.sort(key=lambda page: page.get("index", 999))
    return pages


def candidate_score(page: dict, names: list[str], common: str) -> float | None:
    info = (page.get("imageinfo") or [None])[0]
    if not info:
        return None
    mime = (info.get("mime") or "").lower()
    if mime not in OK_MIME:
        return None
    size = int(info.get("size") or 0)
    if size < 20_000 or size > 12_000_000:
        return None
    title = page.get("title") or ""
    low = title.lower()
    if any(word in low for word in ("spectrogram", "sonogram", "range map", "distribution")):
        return None
    matched = False
    for name in names:
        genus, species = name.lower().split()
        if genus in low and species in low:
            matched = True
            break
    if not matched and common.lower() in low:
        matched = True
    if not matched:
        return None
    score = 20.0
    if any(name.lower().replace(" ", "_") in low or name.lower() in low for name in names):
        score += 40
    if any(word in low for word in (" song", " call", "xc", "crying", "drum")):
        score += 12
    if mime == "audio/mpeg":
        score += 4
    if 80_000 <= size <= 1_500_000:
        score += 10
    elif size > 4_000_000:
        score -= 8
    return score


def fetch_bytes(url: str) -> bytes | None:
    clean = url.split("?")[0]
    req = urllib.request.Request(clean, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").lower()
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimit(clean) from exc
        print(f"  HTTP {exc.code}", flush=True)
        return None
    if not data or data[:1] == b"<" or "html" in ctype or len(data) < 20_000:
        return None
    return data


def trim_clip(src: Path, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src),
        "-af", "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.2:detection=peak",
        "-t", "12",
        "-ac", "1", "-ar", "22050",
        "-c:a", "libmp3lame", "-b:a", "64k",
        str(dest),
    ]
    try:
        subprocess.run(cmd, check=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"  ffmpeg failed: {exc}", flush=True)
        if dest.exists():
            dest.unlink()
        return False
    probe = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(dest),
    ]
    try:
        out = subprocess.run(probe, check=True, capture_output=True, text=True, timeout=20)
        duration = float(out.stdout.strip() or "0")
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
        duration = 0
    if duration < 0.8 or dest.stat().st_size < 4000:
        dest.unlink(missing_ok=True)
        return False
    return True


def credit_for(page: dict) -> str:
    info = (page.get("imageinfo") or [{}])[0]
    meta = info.get("extmetadata") or {}
    artist = plain((meta.get("Artist") or {}).get("value") or "")
    license_name = plain((meta.get("LicenseShortName") or {}).get("value") or "")
    filename = (page.get("title") or "").replace("File:", "")
    bits = [f"Call via Wikimedia Commons (File:{filename})."]
    if artist:
        bits.append(f"Recorded by {artist}.")
    if license_name:
        bits.append(f"{license_name}.")
    bits.append("Used for local study.")
    return " ".join(bits)


def write_records(rows: dict[str, dict]) -> None:
    payload = json.dumps([rows[pid] for pid in BIRD_ORDER], indent=2, ensure_ascii=False) + "\n"
    tmp = DATA.with_suffix(".json.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(DATA)


def choose_pages(bird: dict) -> list[dict]:
    names = binomials(bird)
    common = bird["common_name"]
    queries = [f'"{name}" filetype:audio' for name in names]
    queries.append(f'"{common}" bird filetype:audio')
    for query in queries:
        print(f"  search {query}", flush=True)
        pages = search_audio(query)
        ranked = []
        for page in pages:
            score = candidate_score(page, names, common)
            if score is not None:
                ranked.append((score, page))
        ranked.sort(key=lambda item: item[0], reverse=True)
        if ranked:
            return [page for _score, page in ranked[:3]]
        time.sleep(2.0)
    return []


def main() -> int:
    by_seed = {bird["id"]: bird for bird in BIRDS}
    if set(by_seed) != set(BIRD_ORDER):
        print("seed and path ids differ")
        return 1
    if not DATA.exists():
        print("missing data/birds.json")
        return 1
    rows = {
        row["id"]: row
        for row in json.loads(DATA.read_text(encoding="utf-8"))
        if isinstance(row, dict) and row.get("id")
    }
    if set(rows) != set(BIRD_ORDER):
        print("birds.json does not match the study order")
        return 1
    SOUNDS.mkdir(parents=True, exist_ok=True)
    saved = 0
    for pid in BIRD_ORDER:
        bird = rows[pid]
        dest = SOUNDS / f"{pid}.mp3"
        if bird.get("audio") == dest.name and dest.exists() and dest.stat().st_size > 4000:
            saved += 1
            continue
        print(bird["common_name"], flush=True)
        try:
            pages = choose_pages(bird)
        except RateLimit:
            print("HTTP 429 on Commons search. Stopping.", flush=True)
            write_records(rows)
            return 2
        time.sleep(2.0)
        saved_this = False
        for page in pages:
            info = (page.get("imageinfo") or [{}])[0]
            try:
                data = fetch_bytes(info.get("url") or "")
            except RateLimit:
                print("HTTP 429 on audio download. Stopping.", flush=True)
                write_records(rows)
                return 2
            if not data:
                continue
            raw = SOUNDS / f"{pid}.part"
            raw.write_bytes(data)
            if not trim_clip(raw, dest):
                raw.unlink(missing_ok=True)
                continue
            raw.unlink(missing_ok=True)
            bird["audio"] = dest.name
            bird["audio_credit"] = credit_for(page)
            saved += 1
            saved_this = True
            print(f"  saved {dest.name}", flush=True)
            break
        if not saved_this:
            print(f"  NO CALL: {pid}", flush=True)
            bird.pop("audio", None)
            bird.pop("audio_credit", None)
        write_records(rows)
        time.sleep(1.2)
    write_records(rows)
    print(f"Wrote {DATA} ({saved} calls of {len(BIRD_ORDER)})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
