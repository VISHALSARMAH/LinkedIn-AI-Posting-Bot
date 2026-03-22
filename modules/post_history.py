import json
import os
from modules.paths import POST_HISTORY_FILE as HISTORY_FILE

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"posted_urls": []}
    with open(HISTORY_FILE, "r") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "posted_urls" not in data:
        return {"posted_urls": []}
    if not isinstance(data["posted_urls"], list):
        data["posted_urls"] = []
    return data


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def is_already_posted(url):
    history = load_history()
    return url in history["posted_urls"]


def add_posted_url(url):
    history = load_history()
    if url not in history["posted_urls"]:
        history["posted_urls"].append(url)
    save_history(history)