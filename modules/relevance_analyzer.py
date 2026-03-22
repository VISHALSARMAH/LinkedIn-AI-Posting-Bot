from sentence_transformers import util
from modules.model_loader import get_model

model = get_model()


def build_article_text(article):
    text = article["title"] + " " + article["article_text"][:1000]
    return text


def rank_articles(topic, articles):

    topic_embedding = model.encode(topic, convert_to_tensor=True)

    scored_articles = []

    for article in articles:

        article_text = build_article_text(article)

        article_embedding = model.encode(article_text, convert_to_tensor=True)

        score = util.cos_sim(topic_embedding, article_embedding).item()

        article["relevance_score"] = score

        scored_articles.append(article)

    scored_articles.sort(key=lambda x: x["relevance_score"], reverse=True)

    return scored_articles