import requests
import feedparser
import json
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse

from bs4 import BeautifulSoup


GOOGLE_NEWS_HOST = "news.google.com"
GOOGLE_NEWS_DECODE_ENDPOINT = "https://news.google.com/_/DotsSplashUi/data/batchexecute"


def _extract_google_news_article_id(url):
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]

    if parsed.netloc != GOOGLE_NEWS_HOST:
        return None

    if len(path_parts) < 2:
        return None

    if path_parts[-2] not in {"articles", "read"}:
        return None

    return path_parts[-1]


def _extract_external_url_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()

        if not href.startswith("http"):
            continue

        host = urlparse(href).netloc
        if not host:
            continue

        # Keep only publisher domains, not Google internal links.
        if host.endswith("google.com") or host.endswith("gstatic.com"):
            continue

        return href

    return None


def _extract_decode_params_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    data_div = soup.select_one("c-wiz > div[jscontroller][data-n-a-sg][data-n-a-ts]")

    if not data_div:
        return None, None

    signature = data_div.get("data-n-a-sg")
    timestamp = data_div.get("data-n-a-ts")

    if not signature or not timestamp:
        return None, None

    return signature, timestamp


def _decode_google_news_url(article_id, signature, timestamp):
    payload = [
        "Fbv4je",
        (
            '["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,'
            "null,null,null,null,0,1],\"X\",\"X\",1,[1,1,1],1,1,null,0,0,null,0],"
            f'"{article_id}",{timestamp},"{signature}"]'
        ),
    ]

    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": "Mozilla/5.0",
    }

    body = f"f.req={quote(json.dumps([[payload]]))}"
    response = requests.post(
        GOOGLE_NEWS_DECODE_ENDPOINT,
        headers=headers,
        data=body,
        timeout=10,
    )
    response.raise_for_status()

    parsed_data = json.loads(response.text.split("\n\n")[1])[:-2]
    resolved_url = json.loads(parsed_data[0][2])[1]

    if isinstance(resolved_url, str) and resolved_url.startswith("http"):
        return resolved_url

    return None


def resolve_google_news_url(url):
    article_id = _extract_google_news_article_id(url)
    if not article_id:
        return url

    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        html = response.text

        direct_external_url = _extract_external_url_from_html(html)
        if direct_external_url:
            return direct_external_url

        signature, timestamp = _extract_decode_params_from_html(html)
        if not signature or not timestamp:
            return url

        decoded_url = _decode_google_news_url(article_id, signature, timestamp)
        return decoded_url or url

    except Exception:
        return url


CONFIG_PATH = "config/config.json"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def generate_search_queries(topic):
    topic = topic.lower()

    return [
        topic,
        f"{topic} technology",
        f"{topic} startup",
        f"{topic} research",
        f"{topic} innovation"
    ]


def build_rss_url(query):
    encoded_query = quote(query)
    return f"https://news.google.com/rss/search?q={encoded_query}"


def fetch_articles():
    config = load_config()

    topic = config["topic"]
    freshness_hours = config["article_freshness_hours"]

    MAX_ARTICLES_PER_QUERY = 10

    queries = generate_search_queries(topic)

    articles = []
    seen_urls = set()

    cutoff_time = datetime.utcnow() - timedelta(hours=freshness_hours)

    for query in queries:
        rss_url = build_rss_url(query)

        feed = feedparser.parse(rss_url)

        for entry in feed.entries[:MAX_ARTICLES_PER_QUERY]:

            url = resolve_google_news_url(entry.link)
            if url in seen_urls:
                continue
            seen_urls.add(url)

            published = datetime(*entry.published_parsed[:6])

            if published < cutoff_time:
                continue

            article = {
                "title": entry.title,
                "link": url,
                "published": published.isoformat(),
                "source": entry.source.title if "source" in entry else "unknown"
            }

            articles.append(article)
    print(f"Unique articles collected: {len(articles)}")
    return articles