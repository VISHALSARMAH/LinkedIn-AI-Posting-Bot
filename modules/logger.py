import json
from datetime import datetime
from modules.paths import LOG_FILE

def log_event(message):
    log_entry = {
        "time": str(datetime.now()),
        "message": message
    }

    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except Exception:
        logs = []

    logs.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)