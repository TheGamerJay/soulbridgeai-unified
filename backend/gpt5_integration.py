#!/usr/bin/env python3
"""
GPT-5 Integration for SoulBridge AI
Tier-based model routing, cost tracking, and feature caps
"""

import os
import datetime as dt
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
#  GPT-5 Tier Configuration
# =========================

# GPT-5 Model Mapping
TIER_MODEL = {
    "bronze": "gpt-5-nano",     # Ultra affordable: $0.05 in / $0.40 out per 1M tokens
    "silver": "gpt-5-mini",     # Great value: $0.25 in / $2.00 out per 1M tokens  
    "gold":   "gpt-5"           # Premium: $1.25 in / $10.0 out per 1M tokens
}

# Fallback for development/testing
TIER_MODEL_FALLBACK = {
    "bronze": "gpt-4o-mini",
    "silver": "gpt-4o", 
    "gold":   "gpt-4o"
}

DEFAULT_TIER = "silver"

# Pricing per 1M tokens (USD)
PRICING: Dict[str, Dict[str, float]] = {
    "gpt-5":       {"in": 1.25,  "out": 10.0},
    "gpt-5-mini":  {"in": 0.25,  "out": 2.0},
    "gpt-5-nano":  {"in": 0.05,  "out": 0.40},
    # Fallback pricing
    "gpt-4o":      {"in": 2.50,  "out": 10.0},
    "gpt-4o-mini": {"in": 0.15,  "out": 0.60},
}

# Feature-specific token caps per tier
FEATURE_MAX_TOKENS = {
    "story":           {"bronze": 900,  "silver": 1200, "gold": 2000},
    "decoder":         {"bronze": 900,  "silver": 1200, "gold": 1600},
    "horoscope":       {"bronze": 500,  "silver": 650,  "gold": 800},
    "fortune":         {"bronze": 900,  "silver": 1200, "gold": 1500},
    "chat":            {"bronze": 600,  "silver": 900,  "gold": 1200},
    "creative_writer": {"bronze": 800,  "silver": 1000, "gold": 1500},
    "relationship":    {"bronze": 700,  "silver": 900,  "gold": 1200},
    "dream":           {"bronze": 600,  "silver": 800,  "gold": 1000},
    "json":            {"bronze": 200,  "silver": 250,  "gold": 300},
}

# Image costs and limits
IMAGE_COST_USD = float(os.getenv("IMAGE_COST_USD", "0.04"))  # Per image
IMAGE_DAILY_LIMIT = 5  # Per tier per day

def pick_model(tier: str, use_fallback: bool = False) -> str:
    """Select model based on tier, with fallback option"""
    tier = (tier or DEFAULT_TIER).lower()
    model_map = TIER_MODEL_FALLBACK if use_fallback else TIER_MODEL
    return model_map.get(tier, model_map[DEFAULT_TIER])

def pick_cap(feature: str, tier: str) -> int:
    """Get token limit for feature and tier"""
    feature = (feature or "chat").lower()
    tier = (tier or DEFAULT_TIER).lower()
    table = FEATURE_MAX_TOKENS.get(feature, FEATURE_MAX_TOKENS["chat"])
    return table.get(tier, table[DEFAULT_TIER])

# =========================
#  Cost Tracking System
# =========================

def _today():
    return dt.date.today().isoformat()

@dataclass
class UsageRow:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    image_count: int = 0
    image_cost_usd: float = 0.0
    api_calls: int = 0

# day -> user_id -> tier -> feature -> UsageRow
COST_LEDGER: Dict[str, Dict[str, Dict[str, Dict[str, UsageRow]]]] = defaultdict(
    lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(UsageRow)))
)

def add_tokens(user_id: str, tier: str, feature: str, model: str, prompt_toks: int, completion_toks: int):
    """Record token usage and calculate costs"""
    day = _today()
    prices = PRICING.get(model, PRICING.get("gpt-4o-mini", {"in": 0.15, "out": 0.60}))
    
    # Calculate costs (prices are per 1M tokens)
    in_cost = (prompt_toks * prices["in"]) / 1_000_000.0
    out_cost = (completion_toks * prices["out"]) / 1_000_000.0

    row = COST_LEDGER[day][user_id][tier][feature]
    row.prompt_tokens += prompt_toks
    row.completion_tokens += completion_toks
    row.input_cost_usd += in_cost
    row.output_cost_usd += out_cost
    row.api_calls += 1
    
    logger.info(f"💰 Cost tracking - User: {user_id}, Tier: {tier}, Feature: {feature}, "
                f"Tokens: {prompt_toks}+{completion_toks}, Cost: ${in_cost + out_cost:.6f}")
    
    return in_cost, out_cost

def add_image_cost(user_id: str, tier: str, feature: str = "image", count: int = 1):
    """Record image generation costs"""
    day = _today()
    row = COST_LEDGER[day][user_id][tier][feature]
    cost = IMAGE_COST_USD * count
    row.image_count += count
    row.image_cost_usd += cost
    row.api_calls += 1
    return cost

def get_user_costs(user_id: str, day: Optional[str] = None):
    """Get cost summary for a user"""
    day = day or _today()
    tiers = COST_LEDGER.get(day, {}).get(user_id, {})
    
    summary = []
    total_cost = 0.0
    
    for tier, features in tiers.items():
        for feature, row in features.items():
            subtotal = row.input_cost_usd + row.output_cost_usd + row.image_cost_usd
            total_cost += subtotal
            summary.append({
                "tier": tier,
                "feature": feature,
                "prompt_tokens": row.prompt_tokens,
                "completion_tokens": row.completion_tokens,
                "image_count": row.image_count,
                "api_calls": row.api_calls,
                "input_cost_usd": round(row.input_cost_usd, 6),
                "output_cost_usd": round(row.output_cost_usd, 6),
                "image_cost_usd": round(row.image_cost_usd, 6),
                "subtotal_usd": round(subtotal, 6)
            })
    
    return {
        "day": day,
        "user_id": user_id,
        "items": summary,
        "total_usd": round(total_cost, 6)
    }

def get_daily_costs(day: Optional[str] = None):
    """Get cost summary for entire day"""
    day = day or _today()
    users = COST_LEDGER.get(day, {})
    
    total_cost = 0.0
    items = []
    
    for user_id, tiers in users.items():
        user_total = 0.0
        for tier, features in tiers.items():
            for feature, row in features.items():
                user_total += (row.input_cost_usd + row.output_cost_usd + row.image_cost_usd)
        total_cost += user_total
        items.append({"user_id": user_id, "total_usd": round(user_total, 6)})
    
    return {
        "day": day,
        "users": items,
        "grand_total_usd": round(total_cost, 6)
    }

# =========================
#  GPT-5 API Wrapper
# =========================

def gpt5_complete(*, user_id: str, tier: str, feature: str, system: str, user_content: str,
                  temperature: float = 0.7, explicit_model: Optional[str] = None,
                  max_tokens: Optional[int] = None, use_fallback: bool = False) -> Tuple[str, Dict[str, Any], float]:
    """
    Enhanced GPT completion with GPT-5 tier routing and cost tracking
    
    Returns: (response_text, usage_dict, total_cost_usd)
    """
    # Select model and token cap
    model = explicit_model or pick_model(tier, use_fallback)
    cap = max_tokens if max_tokens is not None else pick_cap(feature, tier)
    
    logger.info(f"🤖 GPT-5 Call - User: {user_id}, Tier: {tier}, Feature: {feature}, Model: {model}, Cap: {cap}")
    
    try:
        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content}
            ],
            max_tokens=cap,
            temperature=temperature
        )
        
        # Extract response and usage
        text = response.choices[0].message.content
        usage = getattr(response, "usage", None)
        prompt_toks = getattr(usage, "prompt_tokens", 0) or 0
        comp_toks = getattr(usage, "completion_tokens", 0) or 0
        
        # Track costs
        in_cost, out_cost = add_tokens(
            user_id=user_id, tier=tier, feature=feature, model=model,
            prompt_toks=prompt_toks, completion_toks=comp_toks
        )
        
        total_cost = in_cost + out_cost
        
        usage_dict = {
            "model": model,
            "prompt_tokens": prompt_toks,
            "completion_tokens": comp_toks,
            "total_tokens": prompt_toks + comp_toks,
            "input_cost_usd": round(in_cost, 6),
            "output_cost_usd": round(out_cost, 6),
            "total_cost_usd": round(total_cost, 6)
        }
        
        return text, usage_dict, round(total_cost, 6)
        
    except Exception as e:
        logger.error(f"❌ GPT-5 API Error: {e}")
        if not use_fallback and "gpt-5" in model:
            # Try fallback models if GPT-5 fails
            logger.info("🔄 Falling back to GPT-4o models...")
            return gpt5_complete(
                user_id=user_id, tier=tier, feature=feature,
                system=system, user_content=user_content,
                temperature=temperature, explicit_model=explicit_model,
                max_tokens=max_tokens, use_fallback=True
            )
        raise

# =========================
#  Real Horoscope Integration
# =========================

def fetch_real_horoscope(sign: str) -> str:
    """Fetch real daily horoscope from aztro API"""
    import requests
    
    try:
        response = requests.post(
            f"https://aztro.sameerkumar.website/?sign={sign}&day=today",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("description", "")
    except Exception as e:
        logger.warning(f"⚠️ Horoscope API error: {e}")
    
    # Fallback if API fails
    return "Today invites steady steps. Focus on what you can control and move gently forward."

# =========================
#  Image Generation with Daily Limits
# =========================

# Simple in-memory daily limits tracker
_image_usage = defaultdict(int)  # key: f"{date}:{user_id}:{tier}"

def check_image_quota(user_id: str, tier: str) -> Tuple[bool, int]:
    """Check if user can generate more images today"""
    key = f"{_today()}:{user_id}:{tier}"
    used = _image_usage[key]
    
    if used >= IMAGE_DAILY_LIMIT:
        return False, used
    
    _image_usage[key] += 1
    return True, _image_usage[key]

def generate_image(user_id: str, tier: str, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
    """Generate image with quota checking and cost tracking"""
    # Check daily quota
    can_generate, used_today = check_image_quota(user_id, tier)
    if not can_generate:
        return {
            "success": False,
            "error": f"Daily image limit reached ({IMAGE_DAILY_LIMIT} per day for {tier} tier)",
            "used_today": used_today,
            "limit": IMAGE_DAILY_LIMIT
        }
    
    try:
        # Generate image
        response = client.images.generate(
            model=os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3"),
            prompt=prompt,
            size=size,
            n=1,
            response_format="b64_json"
        )
        
        # Track cost
        cost = add_image_cost(user_id, tier, "image", 1)
        
        return {
            "success": True,
            "tier": tier,
            "used_today": used_today,
            "limit": IMAGE_DAILY_LIMIT,
            "image_b64": response.data[0].b64_json,
            "cost_usd": round(cost, 6),
            "size": size
        }
        
    except Exception as e:
        logger.error(f"❌ Image generation error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# =========================
#  Enhanced Tarot System
# =========================

def generate_tarot_reading(focus: str = "love", spread: str = "three_card", seed: Optional[str] = None) -> Dict[str, Any]:
    """Generate comprehensive tarot reading with real deck"""
    import random
    
    # Complete 78-card deck
    MAJOR_ARCANA = [
        "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor", "The Hierophant",
        "The Lovers", "The Chariot", "Strength", "The Hermit", "Wheel of Fortune", "Justice", "The Hanged Man",
        "Death", "Temperance", "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"
    ]
    
    SUITS = ["Wands", "Cups", "Swords", "Pentacles"]
    RANKS = ["Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Page", "Knight", "Queen", "King"]
    
    SUIT_KEYWORDS = {
        "Wands": ["creativity", "energy", "initiative", "passion"],
        "Cups": ["emotion", "relationship", "intuition", "healing"],
        "Swords": ["thought", "truth", "conflict", "decision"],
        "Pentacles": ["work", "resources", "home", "stability"],
    }
    
    SPREADS = {
        "one_card": ["Message"],
        "three_card": ["Past", "Present", "Future"],
        "five_card": ["Situation", "Challenge", "Guidance", "Hidden Factor", "Likely Outcome"]
    }
    
    # Build deck
    deck = []
    for name in MAJOR_ARCANA:
        deck.append({"name": name, "arcana": "Major", "keywords": []})
    
    for suit in SUITS:
        for rank in RANKS:
            deck.append({
                "name": f"{rank} of {suit}",
                "arcana": "Minor",
                "keywords": SUIT_KEYWORDS[suit]
            })
    
    # Draw cards
    rng = random.Random(seed or str(dt.datetime.utcnow()))
    positions = SPREADS.get(spread, SPREADS["three_card"])
    drawn_cards = rng.sample(deck, len(positions))
    
    cards = []
    for pos, card in zip(positions, drawn_cards):
        reversed = rng.random() < 0.45
        cards.append({
            "position": pos,
            "name": card["name"],
            "arcana": card["arcana"],
            "keywords": card.get("keywords", []),
            "reversed": reversed
        })
    
    return {
        "focus": focus,
        "spread": spread,
        "cards": cards
    }