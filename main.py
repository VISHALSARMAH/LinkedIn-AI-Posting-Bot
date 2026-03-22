from modules.news_fetcher import fetch_articles
from modules.article_scraper import scrape_article
from modules.relevance_analyzer import rank_articles
from modules.duplicate_filter import filter_duplicates
from modules.post_generator import generate_posts
from modules.post_parser import split_posts
from modules.post_ranker import score_posts
from modules.post_validator import clean_post, validate_post, rewrite_post
from modules.linkedin_poster import post_to_linkedin
from modules.post_history import is_already_posted, add_posted_url
from modules.logger import log_event
from modules.topic_manager import get_topic

import json
import os
import re


CONFIG_PATH = "config/config.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def init_data_files():
    from modules.paths import POST_HISTORY_FILE, LOG_FILE, COOKIES_FILE

    if not os.path.exists(POST_HISTORY_FILE):
        with open(POST_HISTORY_FILE, "w") as f:
            json.dump({"posted_urls": []}, f)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)

    if not os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "w") as f:
            json.dump({}, f)


def add_source_link(post, url):
    parts = post.split("#")

    if len(parts) > 1:
        main = parts[0].strip()
        hashtags = "#" + "#".join(parts[1:])
        return f"{main}\n\n🔗 Read more: {url}\n\n{hashtags}"

    return post + f"\n\n🔗 Read more: {url}"


def save_posts(posts):
    os.makedirs("generated_posts", exist_ok=True)

    for i, post in enumerate(posts, start=1):
        filename = f"generated_posts/post_{i}.txt"
        with open(filename, "w") as f:
            f.write(post.strip())
        print(f"Saved {filename}")


def scrape_articles(articles):
    scraped = []

    for article in articles[:10]:
        print("Scraping:", article["title"])

        result = scrape_article(article["link"])

        if result and len(result["title"]) > 10:
            scraped.append(result)

    return scraped


def process_posts(raw_text):
    posts = split_posts(raw_text)

    # Clean posts
    posts = [clean_post(p) for p in posts]

    # Validate + rewrite if needed
    validated = []
    for p in posts:
        if not validate_post(p):
            print("⚠ Rewriting a post...")
            p = rewrite_post(p)
            p = clean_post(p)
        validated.append(p)

    return validated


def select_best_post(posts, scores_text):
    match = re.search(r'BEST POST: POST\s+(\d+)', scores_text)

    if match:
        index = int(match.group(1)) - 1
        if 0 <= index < len(posts):
            return posts[index]

    print("⚠ Fallback: selecting first post")
    return posts[0]


def main():
    os.makedirs("data", exist_ok=True)
    init_data_files()

    log_event("Script started")

    config = load_config()
    topic = get_topic(config)

    print("\nFetching articles...\n")
    articles = fetch_articles()
    print(f"Fetched {len(articles)} candidate articles\n")

    scraped_articles = scrape_articles(articles)

    print(f"\nScraped {len(scraped_articles)} valid articles\n")

    if not scraped_articles:
        print("No valid articles scraped.")
        return

    ranked = rank_articles(topic, scraped_articles)
    filtered_articles = filter_duplicates(ranked)

    filtered_articles = [
        a for a in filtered_articles
        if not is_already_posted(a["url"])
    ]

    if not filtered_articles:
        print("No new articles to post.")
        return

    print("\nTop ranked articles:\n")
    for article in filtered_articles[:3]:
        print(article["relevance_score"], "-", article["title"])

    best_article = filtered_articles[0]

    print("\nSelected article:\n")
    print(best_article["title"])
    print(best_article["url"])
    log_event(f"Selected article: {best_article['title']}")

    print("\nGenerating LinkedIn posts...\n")

    raw_text = generate_posts(best_article)

    posts = process_posts(raw_text)

    print("\nPosts validated")

    scores = score_posts(posts)

    print("\nScoring result:\n")
    print(scores)

    best_post = select_best_post(posts, scores)
    best_post = add_source_link(best_post, best_article["url"])

    print("\n" + "=" * 40)
    print("Selected Best Post:")
    print("=" * 40)
    print(best_post)
    print("=" * 40)

    print("\nSaving posts...\n")
    save_posts(posts)

    print("\nPosting to LinkedIn...\n")
    posted_ok = post_to_linkedin(best_post)

    if posted_ok:
        add_posted_url(best_article["url"])
        log_event("Post successfully published")

    print("\nDone.")


if __name__ == "__main__":
    main()