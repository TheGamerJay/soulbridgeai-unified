# tarot_engine.py — shim to satisfy `import tarot_engine` in production
# - Loads a 78-card deck from static/data/tarot_deck.json if available
# - Draws cards (upright/reversed)
# - Generates a summary using the right GPT model per plan
# - Exposes small, predictable API your app can call

from __future__ import annotations
import json, os, random
from typing import List, Dict, Optional

# ---- Tier → model mapping (matches your app's logic) ----
MODEL_BY_PLAN = {
    "bronze": "gpt-3.5-turbo",
    "silver": "gpt-4.0",
    "gold":   "gpt-5",
}

# Lazy OpenAI import (only when we actually call it)
def _openai_client():
    import openai  # imported here to avoid import errors if key not set during app boot
    return openai

# ---- Deck loading ----
_DECK: Optional[List[Dict]] = None

def load_deck() -> List[Dict]:
    """
    Load full 78-card deck from static/data/tarot_deck.json.
    The file should be the combined Blocks B–F you already added.
    Falls back to a minimal major-only deck if not found (so the API never 500s).
    """
    global _DECK
    if _DECK is not None:
        return _DECK

    candidates = [
        os.path.join(os.getcwd(), "static", "data", "tarot_deck.json"),
        os.path.join(os.path.dirname(__file__), "static", "data", "tarot_deck.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _DECK = json.load(f)
                break

    if _DECK is None:
        # Safe fallback: majors only (keeps prod alive; replace by putting the full JSON in place)
        _DECK = [
            {"name":"The Fool","category":"Major","upright":"Beginnings, innocence, leap of faith, spontaneity.","reversed":"Recklessness, naivety, holding back, poor judgment."},
            {"name":"The Magician","category":"Major","upright":"Manifestation, willpower, resourcefulness, skill.","reversed":"Manipulation, trickery, illusions, wasted talent."},
            {"name":"The High Priestess","category":"Major","upright":"Intuition, hidden knowledge, the subconscious mind.","reversed":"Secrets, withdrawal, silence, ignoring intuition."},
            {"name":"The Empress","category":"Major","upright":"Nurture, fertility, abundance, beauty, creation.","reversed":"Creative block, dependence, stagnation, insecurity."},
            {"name":"The Emperor","category":"Major","upright":"Authority, structure, stability, discipline, control.","reversed":"Tyranny, domination, rigidity, loss of control."},
            {"name":"The Hierophant","category":"Major","upright":"Tradition, conformity, morality, spiritual guidance.","reversed":"Rebellion, new methods, personal belief, freedom."},
            {"name":"The Lovers","category":"Major","upright":"Partnership, union, alignment of values, heart-led choice.","reversed":"Disharmony, imbalance, misalignment, hard decision."},
            {"name":"The Chariot","category":"Major","upright":"Determination, willpower, triumph, control.","reversed":"Aggression, self-doubt, lack of direction."},
            {"name":"Strength","category":"Major","upright":"Courage, inner strength, compassion, patience.","reversed":"Weakness, insecurity, self-doubt."},
            {"name":"The Hermit","category":"Major","upright":"Soul-searching, introspection, inner guidance.","reversed":"Isolation, withdrawal, lost path."},
            {"name":"Wheel of Fortune","category":"Major","upright":"Change, cycles, destiny, turning point.","reversed":"Resistance to change, setbacks."},
            {"name":"Justice","category":"Major","upright":"Truth, fairness, cause and effect, accountability.","reversed":"Dishonesty, unfairness, imbalance."},
            {"name":"The Hanged Man","category":"Major","upright":"Pause, surrender, new perspective.","reversed":"Delays, stalling, fear of sacrifice."},
            {"name":"Death","category":"Major","upright":"Endings, transformation, transition, rebirth.","reversed":"Fear of change, stagnation, clinging."},
            {"name":"Temperance","category":"Major","upright":"Balance, moderation, harmony, patience.","reversed":"Imbalance, excess, conflict."},
            {"name":"The Devil","category":"Major","upright":"Attachment, shadow, temptation, bondage.","reversed":"Breaking free, detachment, reclaiming power."},
            {"name":"The Tower","category":"Major","upright":"Upheaval, revelation, awakening, sudden change.","reversed":"Avoiding disaster, internal collapse."},
            {"name":"The Star","category":"Major","upright":"Hope, renewal, serenity, guidance.","reversed":"Doubt, discouragement, disconnection."},
            {"name":"The Moon","category":"Major","upright":"Illusion, intuition, dreams, the unknown.","reversed":"Clarity, truth revealed, release of fear."},
            {"name":"The Sun","category":"Major","upright":"Joy, vitality, success, clarity.","reversed":"Temporary cloud, unrealistic expectations."},
            {"name":"Judgement","category":"Major","upright":"Reflection, reckoning, inner calling, renewal.","reversed":"Self-doubt, ignoring the call, harsh judgment."},
            {"name":"The World","category":"Major","upright":"Completion, integration, wholeness, travel.","reversed":"Lack of closure, delays, unfinished business."},
        ]
    return _DECK

# ---- Core API used by your app ----

def get_model_for_plan(plan: str) -> str:
    return MODEL_BY_PLAN.get((plan or "bronze").lower(), "gpt-3.5-turbo")

def draw_cards(num_cards: int, rng: Optional[random.Random] = None) -> List[Dict]:
    deck = load_deck()
    r = rng or random.Random()
    chosen = r.sample(deck, num_cards)
    out = []
    for c in chosen:
        orientation = r.choice(["upright", "reversed"])
        out.append({
            "name": c["name"],
            "orientation": orientation.title(),
            "meaning": c[orientation],
            "category": c.get("category", "General"),
        })
    return out

def generate_summary(cards: List[Dict], spread: str, question: Optional[str], plan: str) -> str:
    """
    Uses OpenAI per tier. If OpenAI fails, falls back to a deterministic text.
    """
    model = get_model_for_plan(plan)
    # Build prompt
    pos3 = ["Past","Present","Future"]
    pos5 = ["Situation","Challenge","Hidden","Advice","Outcome"]
    lines = []
    if question:
        lines.append(f"Question: {question}")
    lines.append(f"Spread: {spread}")
    for i, c in enumerate(cards):
        tag = "Card"
        if spread == "three":
            tag = pos3[i]
        elif spread == "five":
            tag = pos5[i]
        lines.append(f"{tag} — {c['name']} ({c['orientation']}): {c['meaning']}")
    prompt = "\n".join(lines) + "\n\nWrite a concise mystical but clear summary (3–6 sentences)."

    try:
        openai = _openai_client()
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role":"system","content":"You are a mystical tarot fortune teller who speaks clearly and kindly."},
                {"role":"user","content":prompt}
            ],
            max_tokens=320,
            temperature=0.7,
        )
        return resp.choices[0].message["content"].strip()
    except Exception:
        # Fallback summary to avoid 500s
        basics = "; ".join([f"{c['name']} ({c['orientation']})" for c in cards])
        return f"Your reading shows: {basics}. Trust your timing and proceed with intention."


def generate_tarot_reading(focus: str = "general", spread: str = "three_card", seed: Optional[int] = None) -> Dict:
    """
    Main function called by your Flask app.
    Returns a dict with cards and interpretation that matches your expected structure.
    """
    # Set up seeded random if provided
    rng = random.Random(seed) if seed else None
    
    # Map spread names to card counts
    spread_counts = {
        "three_card": 3,
        "three": 3,
        "single_card": 1,
        "single": 1,
        "celtic_cross": 5,  # Simplified 5-card version
        "five": 5
    }
    
    num_cards = spread_counts.get(spread.lower(), 3)
    cards_drawn = draw_cards(num_cards, rng)
    
    # Convert to expected format with positions
    positions = {
        1: ["Card"],
        3: ["Past", "Present", "Future"],
        5: ["Situation", "Challenge", "Hidden", "Advice", "Outcome"]
    }
    
    pos_list = positions.get(num_cards, ["Card"] * num_cards)
    formatted_cards = []
    
    for i, card in enumerate(cards_drawn):
        formatted_cards.append({
            "name": card["name"],
            "position": pos_list[i] if i < len(pos_list) else f"Card {i+1}",
            "reversed": card["orientation"] == "Reversed",
            "keywords": [word.strip() for word in card["meaning"].split(",")[:3]],  # First 3 keywords
            "meaning": card["meaning"]
        })
    
    # Generate summary (this will use GPT or fallback)
    interpretation = generate_summary(cards_drawn, spread, focus, "bronze")  # Default to bronze plan
    
    return {
        "cards": formatted_cards,
        "interpretation": interpretation,
        "spread": spread,
        "focus": focus
    }