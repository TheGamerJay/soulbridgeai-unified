#!/usr/bin/env python3
"""
rename_tarot_images.py
Run this INSIDE backend/static/tarot where the 79 PNGs are.

Usage:
  python rename_tarot_images.py            # dry run (preview only)
  python rename_tarot_images.py --apply    # actually rename files

What it does:
- Renames all 78 faces to slugs your app expects (e.g., the_fool.png, ace_of_cups.png).
- Detects/renames the back image to back.png.
"""

import os, re, sys, argparse
from pathlib import Path
from typing import Optional

EXT = ".png"   # you used the 20MB PNG pack

# Canonical names
MAJORS = [
    "The Fool","The Magician","The High Priestess","The Empress","The Emperor",
    "The Hierophant","The Lovers","The Chariot","Strength","The Hermit",
    "Wheel of Fortune","Justice","The Hanged Man","Death","Temperance",
    "The Devil","The Tower","The Star","The Moon","The Sun","Judgement","The World"
]
RANKS = ["Ace","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Page","Knight","Queen","King"]
SUITS = ["Wands","Cups","Swords","Pentacles"]
ALIASES = {"Judgment": "Judgement"}  # normalize US/UK spelling

# Keyword maps to guess names from common zip filenames
MAJOR_KEYS = {
    "fool":"The Fool","magician":"The Magician","priestess":"The High Priestess",
    "empress":"The Empress","emperor":"The Emperor","hierophant":"The Hierophant",
    "lovers":"The Lovers","chariot":"The Chariot","strength":"Strength","hermit":"The Hermit",
    "wheel":"Wheel of Fortune","fortune":"Wheel of Fortune","justice":"Justice",
    "hanged":"The Hanged Man","death":"Death","temperance":"Temperance","devil":"The Devil",
    "tower":"The Tower","star":"The Star","moon":"The Moon","sun":"The Sun",
    "judgement":"Judgement","judgment":"Judgement","world":"The World"
}
SUIT_KEYS = {
    "wand":"Wands","wands":"Wands","cup":"Cups","cups":"Cups",
    "sword":"Swords","swords":"Swords","pentacle":"Pentacles","pentacles":"Pentacles"
}
RANK_KEYS = {
    "ace":"Ace","two":"Two","three":"Three","four":"Four","five":"Five","six":"Six",
    "seven":"Seven","eight":"Eight","nine":"Nine","ten":"Ten",
    "page":"Page","knight":"Knight","queen":"Queen","king":"King",
    # numerals sometimes present in filenames
    "10":"Ten","9":"Nine","09":"Nine","8":"Eight","08":"Eight","7":"Seven","07":"Seven",
    "6":"Six","06":"Six","5":"Five","05":"Five","4":"Four","04":"Four",
    "3":"Three","03":"Three","2":"Two","02":"Two","1":"Ace","01":"Ace","0":"Ace","00":"Ace"
}

def slugify(card_name: str) -> str:
    s = card_name.strip().lower()
    s = s.replace("the ", "the_").replace(" of ", "_of_").replace(" & ", "_and_")
    s = re.sub(r"[^\w]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")

def is_back_name(stem: str) -> bool:
    st = stem.lower()
    return any(k in st for k in ["back", "card_back", "reverse"]) and "background" not in st

def guess_canonical(filename: str) -> Optional[str]:
    stem = Path(filename).stem.lower()

    # back?
    if is_back_name(stem):
        return "BACK"

    # Handle your specific pattern: "00-TheFool.png"
    major_match = re.match(r'(\d+)-(.*)', stem)
    if major_match:
        num, name = major_match.groups()
        name = name.replace('the', ' the ').replace('of', ' of ')
        name = re.sub(r'([A-Z])', r' \1', name).strip()
        name = ' '.join(name.split())
        
        # Try to match with major arcana
        for major in MAJORS:
            if major.lower().replace(' ', '').replace('the', '') == name.lower().replace(' ', '').replace('the', ''):
                return major

    # Handle "Cups01.png" pattern
    suit_match = re.match(r'(cups|wands|swords|pentacles)(\d+)', stem)
    if suit_match:
        suit_name, rank_num = suit_match.groups()
        suit = suit_name.title()
        rank_idx = int(rank_num) - 1
        if 0 <= rank_idx < len(RANKS):
            rank = RANKS[rank_idx]
            return f"{rank} of {suit}"

    # majors by keyword
    for key, title in MAJOR_KEYS.items():
        if re.search(rf"\b{key}\b", stem):
            return title

    # minors by words
    suit = None
    for key, val in SUIT_KEYS.items():
        if re.search(rf"\b{key}\b", stem):
            suit = val; break

    rank = None
    for key, val in RANK_KEYS.items():
        if re.search(rf"\b{key}\b", stem):
            rank = val; break

    if suit and rank:
        return f"{rank} of {suit}"

    # pattern like "cups_10" or "10_cups"
    m = re.search(r"(wand|wands|cup|cups|sword|swords|pentacle|pentacles)", stem)
    n = re.search(r"\b(10|0?[1-9])\b", stem)
    if m and n:
        suit = SUIT_KEYS[m.group(1)]
        rank = RANK_KEYS[n.group(1)]
        return f"{rank} of {suit}"

    return None

def expected_list():
    majors = [slugify(m)+EXT for m in MAJORS]
    minors = [slugify(f"{r} of {s}")+EXT for s in SUITS for r in RANKS]
    return sorted(majors + minors + ["back"+EXT])

def build_plan(folder: Path):
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == EXT]
    if not files:
        raise SystemExit(f"No {EXT} files found in {folder}")

    plan = []      # list[(src, dst)]
    unknown = []   # filenames we couldn't map
    taken = set()  # to avoid collisions

    for src in sorted(files, key=lambda p: p.name):
        guess = guess_canonical(src.name)
        if guess == "BACK":
            target_name = "back" + EXT
        elif guess:
            guess = ALIASES.get(guess, guess)
            target_name = slugify(guess) + EXT
        else:
            unknown.append(src.name)
            continue

        dst = folder / target_name
        # avoid overwriting an existing different file
        i = 2
        while dst.exists() and dst.resolve() != src.resolve():
            dst = folder / f"{Path(target_name).stem}_{i}{EXT}"
            i += 1
        # also avoid duplicates in this session
        while dst.name in taken:
            dst = folder / f"{Path(target_name).stem}_{i}{EXT}"
            i += 1

        if src.name != dst.name:
            plan.append((src, dst))
            taken.add(dst.name)

    return plan, unknown

def main():
    ap = argparse.ArgumentParser(description="Rename 79 PNGs to app-friendly tarot filenames.")
    ap.add_argument("--apply", action="store_true", help="Apply changes (default is dry run).")
    args = ap.parse_args()

    folder = Path.cwd()
    print(f"Working folder: {folder}")

    plan, unknown = build_plan(folder)

    print("\nPlanned renames:")
    if plan:
        for src, dst in plan:
            print(f"  {src.name:<28} -> {dst.name}")
    else:
        print("  (Nothing to rename)")

    if unknown:
        print("\nCould not confidently map these files (rename manually):")
        for u in unknown:
            print(f"  - {u}")

    print("\nExpected checklist:")
    for name in expected_list():
        print("  ", name)

    if not args.apply:
        print("\nDRY RUN ONLY. Re-run with --apply to perform the renames.")
        return

    # Apply renames
    for src, dst in plan:
        src.rename(dst)
    print(f"\nDone. Renamed {len(plan)} files.")

if __name__ == "__main__":
    main()