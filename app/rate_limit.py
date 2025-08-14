from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def init_limiter(app):
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["60 per minute"],  # sane default
        storage_uri="memory://",
        headers_enabled=True,
    )
    limiter.init_app(app)
    return limiter