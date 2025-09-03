"""
Production-Grade Horoscope API
Handles horoscope requests with routing, quota management, and daily/monthly/compatibility features
"""
import logging
from flask import Blueprint, request, jsonify, session
from modules.horoscope.service import HoroscopeService
from quota_limits import get_quota_status
from billing.costing import track_horoscope_cost

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('horoscope', __name__)

# Initialize horoscope service
horoscope_service = HoroscopeService()

@bp.route('/api/horoscope/signs', methods=['GET'])
def get_zodiac_signs():
    """Get list of all zodiac signs"""
    try:
        signs = horoscope_service.get_zodiac_signs()
        return jsonify({
            "success": True,
            "signs": signs
        })
    except Exception as e:
        logger.error(f"Error fetching zodiac signs: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch zodiac signs"
        }), 500

@bp.route('/api/horoscope/daily', methods=['POST'])
def get_daily_horoscope():
    """Generate daily horoscope for a zodiac sign"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400

        sign = data.get('sign')
        reading_type = data.get('type', 'general')  # general, love, career, health
        user_id = session.get('user_id')

        if not sign:
            return jsonify({
                "success": False,
                "error": "Zodiac sign is required"
            }), 400

        # Check usage limits with unified tier system
        if user_id:
            from modules.creative.usage_tracker import CreativeUsageTracker
            from modules.creative.features_config import get_feature_limit
            from modules.user_profile.profile_service import ProfileService
            
            usage_tracker = CreativeUsageTracker()
            
            try:
                profile_service = ProfileService()
                user_profile_result = profile_service.get_user_profile(user_id)
                user_profile = user_profile_result.get('user') if user_profile_result.get('success') else None
                user_plan = user_profile.get('plan', 'bronze') if user_profile else 'bronze'
                trial_active = user_profile.get('trial', {}).get('active', False) if user_profile else False
            except Exception:
                user_plan = 'bronze'
                trial_active = False
            
            if not usage_tracker.can_use_feature(user_id, 'horoscope', user_plan, trial_active):
                limit = get_feature_limit('horoscope', user_plan, trial_active)
                return jsonify({
                    "success": False,
                    "error": f"Daily horoscope limit reached ({limit} uses). Upgrade for more readings."
                }), 429

        # Generate horoscope
        result = horoscope_service.generate_daily_horoscope(
            sign=sign,
            user_id=user_id,
            reading_type=reading_type
        )

        if result.get('success'):
            # Record usage with unified system
            if user_id:
                usage_tracker.record_usage(user_id, 'horoscope')
            
            # Track usage/cost
            try:
                track_horoscope_cost(user_id, 'daily', result)
            except Exception as e:
                logger.error(f"Cost tracking failed for daily horoscope: {e}")

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error generating daily horoscope: {e}")
        return jsonify({
            "success": False,
            "error": "Horoscope generation failed"
        }), 500

@bp.route('/api/horoscope/monthly', methods=['POST'])
def get_monthly_horoscope():
    """Generate monthly horoscope for a zodiac sign"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400

        sign = data.get('sign')
        user_id = session.get('user_id')

        if not sign:
            return jsonify({
                "success": False,
                "error": "Zodiac sign is required"
            }), 400

        # Check quota limits (monthly horoscopes might have different limits)
        quota_status = get_quota_status(user_id, 'horoscope_monthly')
        if not quota_status.get('allowed', False):
            return jsonify({
                "success": False,
                "error": "Monthly horoscope limit reached",
                "quota": quota_status
            }), 429

        # Generate monthly horoscope (extend service for this)
        result = horoscope_service.generate_monthly_horoscope(
            sign=sign,
            user_id=user_id
        )

        if result.get('success'):
            # Track usage/cost
            try:
                track_horoscope_cost(user_id, 'monthly', result)
            except Exception as e:
                logger.error(f"Cost tracking failed for monthly horoscope: {e}")

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error generating monthly horoscope: {e}")
        return jsonify({
            "success": False,
            "error": "Monthly horoscope generation failed"
        }), 500

@bp.route('/api/horoscope/compatibility', methods=['POST'])
def get_compatibility():
    """Get zodiac compatibility analysis between two signs"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400

        sign1 = data.get('sign1')
        sign2 = data.get('sign2')
        user_id = session.get('user_id')

        if not sign1 or not sign2:
            return jsonify({
                "success": False,
                "error": "Both zodiac signs are required"
            }), 400

        # Check quota limits
        quota_status = get_quota_status(user_id, 'horoscope')
        if not quota_status.get('allowed', False):
            return jsonify({
                "success": False,
                "error": "Horoscope limit reached",
                "quota": quota_status
            }), 429

        # Get compatibility analysis
        result = horoscope_service.get_compatibility(sign1, sign2)

        if result.get('success'):
            # Track usage/cost
            try:
                track_horoscope_cost(user_id, 'compatibility', result)
            except Exception as e:
                logger.error(f"Cost tracking failed for compatibility: {e}")

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error calculating compatibility: {e}")
        return jsonify({
            "success": False,
            "error": "Compatibility calculation failed"
        }), 500

@bp.route('/api/horoscope/sign/<sign>', methods=['GET'])
def get_sign_info(sign):
    """Get detailed information about a specific zodiac sign"""
    try:
        result = horoscope_service.get_sign_info(sign)
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Invalid zodiac sign"
            }), 404

        return jsonify({
            "success": True,
            "sign": result
        })

    except Exception as e:
        logger.error(f"Error fetching sign info for {sign}: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch sign information"
        }), 500

# Import the enhanced horoscope system
import os, math, random, hashlib, datetime as dt
from typing import Dict, Any, List, Tuple

# Zodiac data from standalone system
SIGNS: List[str] = [
    "aries","taurus","gemini","cancer","leo","virgo",
    "libra","scorpio","sagittarius","capricorn","aquarius","pisces"
]

ZODIAC: Dict[str, Dict[str, Any]] = {
    "aries": {"name":"Aries","symbol":"Ram","glyph":"♈","dates":"Mar 21 – Apr 19",
              "element":"Fire","modality":"Cardinal","planet":"Mars",
              "strengths":["bold","decisive","energetic","direct"],
              "weaknesses":["impulsive","impatient","combative","restless"]},
    "taurus": {"name":"Taurus","symbol":"Bull","glyph":"♉","dates":"Apr 20 – May 20",
              "element":"Earth","modality":"Fixed","planet":"Venus",
              "strengths":["steady","loyal","sensual","patient"],
              "weaknesses":["stubborn","possessive","comfort-seeking"]},
    "gemini": {"name":"Gemini","symbol":"Twins","glyph":"♊","dates":"May 21 – Jun 20",
              "element":"Air","modality":"Mutable","planet":"Mercury",
              "strengths":["curious","witty","adaptable","expressive"],
              "weaknesses":["scattered","inconsistent","restless"]},
    "cancer": {"name":"Cancer","symbol":"Crab","glyph":"♋","dates":"Jun 21 – Jul 22",
              "element":"Water","modality":"Cardinal","planet":"Moon",
              "strengths":["nurturing","intuitive","protective","devoted"],
              "weaknesses":["moody","clingy","avoidant"]},
    "leo": {"name":"Leo","symbol":"Lion","glyph":"♌","dates":"Jul 23 – Aug 22",
              "element":"Fire","modality":"Fixed","planet":"Sun",
              "strengths":["radiant","confident","generous","playful"],
              "weaknesses":["proud","dramatic","attention-seeking"]},
    "virgo": {"name":"Virgo","symbol":"Maiden","glyph":"♍","dates":"Aug 23 – Sep 22",
              "element":"Earth","modality":"Mutable","planet":"Mercury",
              "strengths":["precise","helpful","grounded","analytical"],
              "weaknesses":["critical","perfectionist","overthinking"]},
    "libra": {"name":"Libra","symbol":"Scales","glyph":"♎","dates":"Sep 23 – Oct 22",
              "element":"Air","modality":"Cardinal","planet":"Venus",
              "strengths":["charming","fair","diplomatic","artful"],
              "weaknesses":["indecisive","people-pleasing","avoidant of conflict"]},
    "scorpio": {"name":"Scorpio","symbol":"Scorpion","glyph":"♏","dates":"Oct 23 – Nov 21",
              "element":"Water","modality":"Fixed","planet":"Mars/Pluto",
              "strengths":["intense","loyal","strategic","transformative"],
              "weaknesses":["jealous","secretive","all-or-nothing"]},
    "sagittarius": {"name":"Sagittarius","symbol":"Archer","glyph":"♐","dates":"Nov 22 – Dec 21",
              "element":"Fire","modality":"Mutable","planet":"Jupiter",
              "strengths":["adventurous","optimistic","big-picture","honest"],
              "weaknesses":["blunt","restless","commitment-averse"]},
    "capricorn": {"name":"Capricorn","symbol":"Sea-Goat","glyph":"♑","dates":"Dec 22 – Jan 19",
              "element":"Earth","modality":"Cardinal","planet":"Saturn",
              "strengths":["ambitious","disciplined","pragmatic","resilient"],
              "weaknesses":["stoic","rigid","work-obsessed"]},
    "aquarius": {"name":"Aquarius","symbol":"Water-Bearer","glyph":"♒","dates":"Jan 20 – Feb 18",
              "element":"Air","modality":"Fixed","planet":"Saturn/Uranus",
              "strengths":["innovative","independent","humanitarian","original"],
              "weaknesses":["aloof","contrarian","detached"]},
    "pisces": {"name":"Pisces","symbol":"Fishes","glyph":"♓","dates":"Feb 19 – Mar 20",
              "element":"Water","modality":"Mutable","planet":"Jupiter/Neptune",
              "strengths":["empathetic","imaginative","spiritual","artistic"],
              "weaknesses":["escapist","over-idealistic","boundary-blurry"]},
}

ELEMENT_GROUPS = {
    "Fire": {"best":["Fire","Air"], "challenging":["Water","Earth"]},
    "Earth": {"best":["Earth","Water"], "challenging":["Fire","Air"]},
    "Air": {"best":["Air","Fire"], "challenging":["Earth","Water"]},
    "Water": {"best":["Water","Earth"], "challenging":["Air","Fire"]},
}

# Enhanced horoscope generation
def _seed(sign: str, date: dt.date, period: str):
    base = f"{sign}|{period}|{date.isoformat()}"
    h = hashlib.sha256(base.encode()).hexdigest()
    random.seed(int(h[:16], 16))

BLURB_OPENERS = [
    "Your energy today gravitates toward",
    "The lesson surfacing revolves around",
    "A gentle nudge pushes you toward",
    "Cosmic weather highlights",
    "Your focus is best placed on",
    "An opportunity unfolds through",
]

DOMAINS = ["communication","work & craft","home & foundations","relationships","health & routines",
           "creativity","learning","finances","boundaries","long-term goals","self-trust","recovery"]

ADVICE_VERBS = ["ground","simplify","commit","experiment with","reframe","reach out about","prioritize",
                "declutter","set boundaries around","journal about","celebrate","rest before"]
TONES = ["confident","curious","steady","reflective","optimistic","protective","playful","pragmatic"]

LUCKY_COLORS = ["crimson","emerald","sapphire","gold","silver","indigo","rose","teal","amber","ivory","charcoal","coral"]
LUCKY_TIMES = ["08:08","10:10","11:11","12:12","14:44","16:16","20:20"]
MOODS = ["focused","cozy","electric","expansive","tender","quiet","brave","clear-headed"]
NUMBERS = list(range(1, 78))

def _sentence(sign: str) -> str:
    s = ZODIAC[sign]
    opener = random.choice(BLURB_OPENERS)
    domain = random.choice(DOMAINS)
    verb = random.choice(ADVICE_VERBS)
    tone = random.choice(TONES)
    target = 'that' if verb != 'celebrate' else 'what you have already achieved'
    return (f"{opener} {domain}. Lean into your {s['element'].lower()} nature and {verb} "
            f"{target}. Keep your tone {tone} and the path clarifies.")

def _lucky() -> Dict[str, Any]:
    return {
        "color": random.choice(LUCKY_COLORS),
        "time": random.choice(LUCKY_TIMES),
        "numbers": random.sample(NUMBERS, 3),
        "mood": random.choice(MOODS),
    }

def _period_dates(date: dt.date, period: str) -> Tuple[dt.date, dt.date]:
    if period == "weekly":
        start = date - dt.timedelta(days=date.weekday())
        end = start + dt.timedelta(days=6)
        return start, end
    if period == "monthly":
        start = date.replace(day=1)
        if start.month == 12:
            next_month = start.replace(year=start.year+1, month=1, day=1)
        else:
            next_month = start.replace(month=start.month+1, day=1)
        end = next_month - dt.timedelta(days=1)
        return start, end
    return date, date

def enhanced_generate(sign: str, date: dt.date, period: str) -> Dict[str, Any]:
    if sign not in SIGNS:
        raise ValueError("Unknown sign.")
    if period not in ("daily","weekly","monthly"):
        raise ValueError("period must be daily|weekly|monthly")

    _seed(sign, date, period)
    s_meta = ZODIAC[sign]
    start, end = _period_dates(date, period)

    lines = [
        _sentence(sign),
        f"Your {s_meta['modality'].lower()} drive pairs with {s_meta['planet']}'s influence—progress favors small consistent steps.",
    ]
    if period != "daily":
        lines.append("Expect momentum mid-period; late window rewards review and tidy follow-through.")

    return {
        "sign": sign,
        "date": date.isoformat(),
        "period": period,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "summary": " ".join(lines),
        "lucky": _lucky(),
        "meta": s_meta,
    }

def enhanced_compatibility(a: str, b: str, rel_type: str = "romantic") -> Dict[str, Any]:
    if a not in SIGNS or b not in SIGNS:
        raise ValueError("Unknown sign(s).")
    A, B = ZODIAC[a], ZODIAC[b]
    eA, eB = A["element"], B["element"]
    score = 50
    
    if eB in ELEMENT_GROUPS[eA]["best"]: score += 25
    if eB in ELEMENT_GROUPS[eA]["challenging"]: score -= 15
    if A["modality"] == B["modality"]: score += 5
    
    if rel_type == "friendship":
        if eB in ELEMENT_GROUPS[eA]["challenging"]: score += 10
        if A["element"] == "Air" or B["element"] == "Air": score += 5
        if A["modality"] == "Mutable" or B["modality"] == "Mutable": score += 3
    
    score = max(5, min(95, score))
    elem_a, elem_b = A["element"], B["element"]
    mod_a, mod_b = A["modality"], B["modality"]
    rel_icon = "💖" if rel_type == "romantic" else "👯"
    note = f"{elem_a} + {elem_b} {rel_type} dynamic; {mod_a} meeting {mod_b}."
    return {"a":a,"b":b,"score":score,"note":note,"type":rel_type,"icon":rel_icon}

@bp.route('/api/horoscope/period', methods=['POST'])
def enhanced_period():
    """Enhanced horoscope reading endpoint"""
    data = request.get_json(silent=True) or {}
    sign = (data.get("sign") or "").lower().strip()
    period = (data.get("period") or "daily").lower().strip()
    date_str = data.get("date")
    
    if date_str:
        try:
            date = dt.date.fromisoformat(date_str)
        except Exception:
            return jsonify({"error":"date must be YYYY-MM-DD"}), 400
    else:
        date = dt.date.today()
    
    try:
        result = enhanced_generate(sign, date, period)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/api/horoscope/compat', methods=['GET'])
def enhanced_compat():
    """Enhanced compatibility endpoint"""
    a = (request.args.get("a") or "").lower().strip()
    b = (request.args.get("b") or "").lower().strip()
    rel_type = (request.args.get("type") or "romantic").lower().strip()
    try:
        return jsonify(enhanced_compatibility(a, b, rel_type)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Interpretation system
INTERPRET_PHRASES = {
    "cosmic_weather": [
        "This suggests the universe is aligning to bring focus to",
        "The cosmic energies are drawing your attention toward",
        "This indicates a spiritual shift happening around",
        "The celestial forces are highlighting the importance of"
    ],
    "element_meaning": {
        "Fire": "your passionate, action-oriented nature is being called upon",
        "Earth": "your grounded, practical wisdom needs to take the lead", 
        "Air": "your intellectual and communicative gifts are essential now",
        "Water": "your intuitive, emotional intelligence holds the key"
    },
    "modality_meaning": {
        "Cardinal": "This is a time for leadership and initiating new directions",
        "Fixed": "Stability and determination will serve you best during this period",
        "Mutable": "Flexibility and adaptability are your greatest strengths right now"
    },
    "lucky_meanings": {
        "color": {
            "crimson": "bold action and courage", "emerald": "growth and healing",
            "sapphire": "wisdom and clarity", "gold": "success and abundance",
            "silver": "intuition and reflection", "indigo": "deep spiritual insight",
            "rose": "love and compassion", "teal": "emotional balance",
            "amber": "warmth and protection", "ivory": "purity and new beginnings",
            "charcoal": "grounding and mystery", "coral": "creativity and vitality"
        },
        "mood": {
            "focused": "concentrated effort will yield the best results",
            "cozy": "comfort and nurturing environments support your growth",
            "electric": "high energy and dynamic action are favored",
            "expansive": "thinking big and embracing possibilities serves you",
            "tender": "gentle, caring approaches will open doors",
            "quiet": "stillness and reflection bring important insights",
            "brave": "courage to face challenges head-on is your superpower",
            "clear-headed": "logical thinking and clarity will guide you well"
        }
    }
}

def generate_interpretation(reading: Dict[str, Any]) -> str:
    sign_meta = reading["meta"]
    lucky = reading["lucky"]
    period = reading["period"]
    
    date = dt.date.fromisoformat(reading["date"])
    _seed(reading["sign"], date, f"{period}_interpret")
    
    lines = []
    
    opener = random.choice(INTERPRET_PHRASES["cosmic_weather"])
    lines.append(f"{opener} your personal growth and life path.")
    
    element_meaning = INTERPRET_PHRASES["element_meaning"][sign_meta["element"]]
    modality_meaning = INTERPRET_PHRASES["modality_meaning"][sign_meta["modality"]]
    lines.append(f"As a {sign_meta['element']} sign, {element_meaning}. {modality_meaning}.")
    
    color = lucky["color"]
    color_meaning = INTERPRET_PHRASES["lucky_meanings"]["color"].get(color, "positive transformation")
    lines.append(f"Your cosmic gift of {color} energy represents {color_meaning} - incorporate this color into your environment or wardrobe to amplify these qualities.")
    
    time = lucky["time"]
    lines.append(f"The {time} power hour is when cosmic energies are most aligned with your personal vibration - use this time for meditation, important decisions, or creative work.")
    
    mood = lucky["mood"]
    mood_meaning = INTERPRET_PHRASES["lucky_meanings"]["mood"].get(mood, "balanced energy serves you well")
    lines.append(f"Embodying {mood} vibes means {mood_meaning} during this {period} period.")
    
    numbers = lucky["numbers"]
    lines.append(f"Your lucky numbers {', '.join(map(str, numbers))} may appear as signs of alignment - watch for them in addresses, times, or important documents.")
    
    planet = sign_meta["planet"]
    planet_guidance = {
        "Mars": "brings courage and drive - take bold action on your goals",
        "Venus": "enhances love and creativity - focus on relationships and artistic pursuits", 
        "Mercury": "sharpens communication - important conversations and learning opportunities await",
        "Moon": "heightens intuition - trust your feelings and nurture your emotional needs",
        "Sun": "illuminates your path - step into your power and let your light shine",
        "Jupiter": "expands possibilities - think big and embrace opportunities for growth",
        "Saturn": "teaches discipline - hard work now builds lasting foundations",
        "Mars/Pluto": "transforms through intensity - embrace change and release what no longer serves",
        "Jupiter/Neptune": "inspires through dreams - pay attention to your visions and spiritual insights",
        "Saturn/Uranus": "innovates through structure - blend tradition with progressive ideas"
    }
    planet_msg = planet_guidance.get(planet, "guides your journey with cosmic wisdom")
    lines.append(f"Your ruling planet {planet} {planet_msg}.")
    
    return " ".join(lines)

def generate_compatibility_interpretation(compat_data: Dict[str, Any]) -> str:
    a, b = compat_data["a"], compat_data["b"]
    score = compat_data["score"]
    rel_type = compat_data.get("type", "romantic")
    
    A, B = ZODIAC[a], ZODIAC[b]
    elem_A, elem_B = A["element"], B["element"]
    mod_A, mod_B = A["modality"], B["modality"]
    
    rel_context = "romantic relationship" if rel_type == "romantic" else "friendship"
    
    lines = []
    
    lines.append(f"**Compatibility Breakdown:**")
    lines.append(f"• Base compatibility starts at 50%")
    
    if elem_B in ELEMENT_GROUPS[elem_A]["best"]:
        lines.append(f"• {elem_A} + {elem_B} elements = +25% (harmonious combination)")
        element_desc = f"{elem_A} and {elem_B} signs naturally complement each other, creating balance and mutual support."
    elif elem_B in ELEMENT_GROUPS[elem_A]["challenging"]:
        lines.append(f"• {elem_A} + {elem_B} elements = -15% (challenging but growth-oriented)")
        element_desc = f"{elem_A} and {elem_B} signs have different approaches, which can create tension but also opportunities for learning and growth."
    else:
        lines.append(f"• {elem_A} + {elem_B} elements = neutral (balanced dynamic)")
        element_desc = f"{elem_A} and {elem_B} signs have a balanced relationship with both supportive and challenging aspects."
    
    if mod_A == mod_B:
        lines.append(f"• Both {mod_A} signs = +5% (shared life approach)")
        modality_desc = f"You both share a {mod_A.lower()} approach to life, understanding each other's timing and methods."
    else:
        lines.append(f"• {mod_A} + {mod_B} modalities = neutral (different paces)")
        modality_desc = f"Your {mod_A.lower()} nature and their {mod_B.lower()} style can create interesting dynamics - you approach change and timing differently."
    
    lines.append(f"• **Final Score: {score}%**")
    lines.append("")
    
    lines.append("**What This Means:**")
    lines.append(element_desc)
    lines.append(modality_desc)
    
    if rel_type == "friendship":
        if score >= 75:
            lines.append("This is a naturally harmonious friendship with great potential for lifelong connection and mutual support.")
        elif score >= 60:
            lines.append("This friendship has solid potential with occasional need for understanding different perspectives.")
        elif score >= 45:
            lines.append("This friendship requires some effort but can be very rewarding and help both friends grow.")
        else:
            lines.append("This friendship may have challenges but can offer valuable learning experiences and different viewpoints.")
    else:
        if score >= 75:
            lines.append("This is a naturally harmonious pairing with strong potential for long-term romantic success.")
        elif score >= 60:
            lines.append("This relationship has good potential with some areas requiring understanding and compromise.")
        elif score >= 45:
            lines.append("This pairing requires effort but can lead to significant personal growth for both partners.")
        else:
            lines.append("This is a challenging combination that requires deep commitment and patience, but can teach valuable lessons.")
    
    strengths = A["strengths"] + B["strengths"]
    challenges = A["weaknesses"] + B["weaknesses"]
    
    lines.append(f"**Combined Strengths:** {', '.join(strengths[:4])}")
    lines.append(f"**Areas for Growth:** Balance {', '.join(challenges[:3])} tendencies with patience and communication.")
    
    return " ".join(lines)

@bp.route('/api/horoscope/interpret', methods=['POST'])
def interpret_reading():
    """Generate interpretation for horoscope reading"""
    data = request.get_json(silent=True) or {}
    sign = (data.get("sign") or "").lower().strip()
    period = (data.get("period") or "daily").lower().strip()
    date_str = data.get("date")
    
    if date_str:
        try:
            date = dt.date.fromisoformat(date_str)
        except Exception:
            return jsonify({"error":"date must be YYYY-MM-DD"}), 400
    else:
        date = dt.date.today()
    
    try:
        reading = enhanced_generate(sign, date, period)
        interpretation = generate_interpretation(reading)
        return jsonify({"interpretation": interpretation}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/api/horoscope/interpret-compat', methods=['POST'])
def interpret_compatibility():
    """Generate interpretation for compatibility reading"""
    data = request.get_json(silent=True) or {}
    a = (data.get("a") or "").lower().strip()
    b = (data.get("b") or "").lower().strip()
    rel_type = (data.get("type") or "romantic").lower().strip()
    
    try:
        compat = enhanced_compatibility(a, b, rel_type)
        interpretation = generate_compatibility_interpretation(compat)
        return jsonify({"interpretation": interpretation}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/api/horoscope/limits', methods=['GET'])
def get_limits():
    """Get user's horoscope usage limits"""
    try:
        from flask import session
        from modules.creative.usage_tracker import CreativeUsageTracker
        from modules.creative.features_config import get_feature_limit
        
        usage_tracker = CreativeUsageTracker()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                "success": True,
                "daily_limit": 5,
                "usage_today": 0,
                "remaining": 5,
                "unlimited": False,
                "message": "Login to track your usage"
            }), 200
            
        try:
            from modules.user_profile.profile_service import ProfileService
            profile_service = ProfileService()
            user_profile_result = profile_service.get_user_profile(user_id)
            user_profile = user_profile_result.get('user') if user_profile_result.get('success') else None
            user_plan = user_profile.get('plan', 'bronze') if user_profile else 'bronze'
            trial_active = user_profile.get('trial', {}).get('active', False) if user_profile else False
        except Exception:
            # Fallback to default values if profile service fails
            user_plan = 'bronze'
            trial_active = False
        
        limit = get_feature_limit('horoscope', user_plan, trial_active)
        usage_today = usage_tracker.get_usage_today(user_id, 'horoscope')
        
        return jsonify({
            "success": True,
            "daily_limit": limit,
            "usage_today": usage_today,
            "remaining": max(0, limit - usage_today) if limit < 999 else 999,
            "unlimited": limit >= 999,
            "user_tier": user_plan
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting horoscope limits: {e}")
        return jsonify({"success": False, "error": str(e)}), 500