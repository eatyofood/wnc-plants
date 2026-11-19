# WNC Plant Flashcards

A local Python flashcard app for learning trees and plants of **Western North Carolina**: common natives, mountain specialties, useful/edible species, and the main invasives.

I looked at existing GitHub flashcard apps first. There are generic Python/Tkinter decks (vocab, periodic table) and an Anki tree-ID deck, but nothing that is a ready-to-run WNC plant teacher with photos and uses. This app is that.

## What you get

- **Study mode:** a photo first. You try to name it, then flip the card for ID tips, habitat, uses, and cautions.
- **Quiz mode:** four-choice ID from the picture.
- **Browse:** the whole deck as a field-guide grid.
- Filters for trees, shrubs, vines, wildflowers, ferns, grasses, native vs invasive.

Photos are Wikipedia / Wikimedia Commons lead images, downloaded to this folder so the app works offline after the first fetch.

## Run it

```bash
cd ~/wnc-plants
python3 download_images.py    # once, or again to refresh photos
python3 app.py
```

Then open [http://127.0.0.1:5055](http://127.0.0.1:5055).

Needs Python 3 and Flask (`pip install -r requirements.txt`).

## What is in the deck

Western NC has more than 2,000 vascular plants. This is not every species. It is the set you actually need in order to start *knowing* the mountains:

- Canopy and understory **trees** of coves, ridges, and spruce-fir peaks
- Signature **shrubs** (rhododendron, mountain laurel, flame azalea, spicebush)
- Common **vines**, **wildflowers**, and **ferns**
- The **invasives** on NC Forest Service / NC-IPC lists (kudzu, stiltgrass, tree-of-heaven, and so on)
- Useful species (pawpaw, ramps, sourwood, ginseng) with honest cautions

Facts were checked against NC Cooperative Extension, the NC Native Plant Society, NC Forest Service invasive lists, and standard field knowledge. Traditional uses are historical. They are **not** medical advice, and they are not a foraging go-ahead. Never eat a plant unless you are sure of the ID and of which part is actually edible.

## Files

- `data/seed_plants.py` — curated species notes
- `data/plants.json` — generated deck (after image download)
- `images/` — local photos
- `app.py` — Flask app
- `download_images.py` — Wikipedia photo fetch
