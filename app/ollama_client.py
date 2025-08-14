import os, time, requests
from typing import Iterable

OLLAMA_BASE = os.getenv("LLM_BASE", os.getenv("OLLAMA_BASE", "http://ollama-ai.railway.internal:11434"))
SESSION = requests.Session()
DEFAULT_TIMEOUT = 120

def _retry(fn, retries=3, backoff=0.7):
    last = None
    for i in range(retries):
        try:
            return fn()
        except Exception as e:
            last = e
            time.sleep(backoff * (2**i))
    raise last

def tags():
    return _retry(lambda: SESSION.get(f"{OLLAMA_BASE}/api/tags", timeout=15).json())

def chat(model: str, messages: list[dict], stream: bool=False, **kwargs):
    payload = {"model": model, "messages": messages} | kwargs
    if not stream:
        def call():
            r = SESSION.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            return r.json()
        return _retry(call)
    else:
        with SESSION.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=DEFAULT_TIMEOUT, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if line:
                    yield line

def is_available() -> bool:
    try:
        t = tags()
        return "models" in t or isinstance(t, dict)
    except Exception:
        return False