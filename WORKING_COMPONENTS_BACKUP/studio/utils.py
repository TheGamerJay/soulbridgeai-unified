# =================================
# 📁 FILE: backend/studio/utils.py
# =================================
import time, uuid

def new_id():
    return f"{int(time.time())}_{uuid.uuid4().hex[:8]}"