from newspaper import Article
from playwright.sync_api import sync_playwright



MIN_WORDS = 500
MEANINGLESS_TITLE_FRAGMENTS = {
    "skip to content",
    "menu",
    "navigation",
    "search",
}


def _extract_playwright_title(text, url):
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        normalized_line = line.lower()

        if len(line) <= 30:
            continue

        if any(fragment in normalized_line for fragment in MEANINGLESS_TITLE_FRAGMENTS):
            continue

        return line[:120]

    return url


def scrape_with_newspaper(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text

        if len(text.split()) < MIN_WORDS:
            return None

        return {
            "title": article.title,
            "url": url,
            "article_text": text
        }

    except Exception:
        return None


def scrape_with_playwright(url):
    try:
        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=60000)

            text = page.inner_text("body")

            browser.close()

            if len(text.split()) < MIN_WORDS:
                return None

            title = _extract_playwright_title(text, url)

            return {
                "title": title,
                "url": url,
                "article_text": text
            }

    except Exception:
        return None


def scrape_article(url):

    article = scrape_with_newspaper(url)

    if article:
        return article

    return scrape_with_playwright(url)