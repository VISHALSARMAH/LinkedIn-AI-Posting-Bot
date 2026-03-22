import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from modules.paths import COOKIES_FILE


def main():
    os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")

        input("Login to LinkedIn in the opened browser, then press ENTER...")

        context.storage_state(path=COOKIES_FILE)
        browser.close()

    print(f"Saved LinkedIn session to {COOKIES_FILE}")


if __name__ == "__main__":
    main()