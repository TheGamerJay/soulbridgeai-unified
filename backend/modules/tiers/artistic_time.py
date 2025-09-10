import os
def _envint(name: str, default: int) -> int:
    try: return int(os.getenv(name, default))
    except Exception: return default
def get_effective_access(*_args, **_kwargs):
    limits = {
        "decoder":   _envint("SC_LIMIT_DECODER",   15),
        "fortune":   _envint("SC_LIMIT_FORTUNE",    8),
        "horoscope": _envint("SC_LIMIT_HOROSCOPE", 10),
    }
    return {"plan": "soul_companions", "limits": limits, "features": {"companions": "all"}}
