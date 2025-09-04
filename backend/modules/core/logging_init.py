import sys, io, os, logging

class SafeFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        try:
            enc = getattr(sys.stdout, "encoding", None) or "utf-8"
            msg = msg.encode(enc, errors="replace").decode(enc, errors="replace")
        except Exception:
            msg = msg.encode("ascii", errors="replace").decode("ascii", errors="replace")
        return msg

def init_safe_logging(level=logging.INFO):
    """Initialize safe logging that never crashes on unicode"""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        else:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass
    
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    root = logging.getLogger()
    if not root.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(SafeFormatter("%(asctime)s %(levelname)-5s %(name)s :: %(message)s"))
        root.addHandler(h)
    root.setLevel(level)