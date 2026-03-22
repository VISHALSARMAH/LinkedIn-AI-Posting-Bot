from sentence_transformers import util
from modules.model_loader import get_model

model = get_model()

def is_duplicate(article, history):

    # URL duplicate check
    for past in history:
        if isinstance(past, dict):
            if article["url"] == past.get("url"):
                return True
        elif isinstance(past, str):
            if article["url"] == past:
                return True

    # Semantic title similarity
    if not history:
        return False

    article_embedding = model.encode(article["title"], convert_to_tensor=True)

    past_titles = [h["title"] for h in history if isinstance(h, dict) and h.get("title")]
    if not past_titles:
        return False

    past_embeddings = model.encode(past_titles, convert_to_tensor=True)

    scores = util.cos_sim(article_embedding, past_embeddings)

    if scores.max().item() > 0.9:
        return True

    return False


def filter_duplicates(articles):
    unique_articles = []

    for article in articles:
        if not is_duplicate(article, unique_articles):
            unique_articles.append(article)

    return unique_articles


def save_post(article):
    # URL persistence is managed by modules.post_history.
    return article