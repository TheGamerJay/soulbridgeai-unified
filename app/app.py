from flask import Flask, jsonify, request, Response, abort
import os, json, time
from utils import get_env, setup_logger
from rate_limit import init_limiter
from ollama_client import chat, tags, is_available

LOG = setup_logger(os.getenv("LOG_LEVEL","info"))
app = Flask(__name__)
limiter = init_limiter(app)

FREE_MODEL = os.getenv("FREE_MODEL","tinyllama")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL","llama3.1:8b")
OLLAMA_BASE = os.getenv("LLM_BASE", os.getenv("OLLAMA_BASE","http://ollama-ai.railway.internal:11434"))
API_KEY = os.getenv("APP_API_KEY")

def require_key():
    if not API_KEY:
        return  # allow if not set
    key = request.headers.get("x-api-key") or request.args.get("api_key")
    if key != API_KEY:
        abort(401, description="invalid api key")

@app.get("/healthz")
def healthz():
    return "ok", 200, {"Content-Type":"text/plain"}

@app.get("/debug/ollama")
def debug_ollama():
    require_key()
    return jsonify({"available": is_available(), "tags": tags(), "base": OLLAMA_BASE})

@app.post("/v1/chat")
@limiter.limit("15/minute")
def chat_proxy():
    require_key()
    body = request.get_json(force=True) or {}
    model = body.get("model", DEFAULT_MODEL)
    messages = body.get("messages", [{"role":"user","content":"Say hi in one short line."}])
    opts = {k:v for k,v in body.items() if k not in ("model","messages","stream")}
    stream = bool(body.get("stream", False))

    LOG.info(f"/v1/chat model={model} stream={stream}")

    if not stream:
        out = chat(model=model, messages=messages, stream=False, **opts)
        return jsonify(out)
    else:
        def gen():
            first = True
            for chunk in chat(model=model, messages=messages, stream=True, **opts):
                if first:
                    # SSE header prelude if you prefer; here we just pass lines
                    first = False
                yield chunk + "\n"
        return Response(gen(), mimetype="text/event-stream")

@app.post("/v1/free")
@limiter.limit("30/minute")
def free_plan():
    require_key()
    body = request.get_json(force=True) or {}
    messages = body.get("messages", [{"role":"user","content":"Say hi"}])
    out = chat(model=FREE_MODEL, messages=messages, stream=False)
    return jsonify(out)

# tiny echo to quickly test POST shape
@app.post("/echo")
def echo():
    return jsonify({"ok": True, "json": request.get_json(silent=True)}), 200