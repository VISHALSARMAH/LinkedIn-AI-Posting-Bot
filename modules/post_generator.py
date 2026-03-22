import json
import requests
import os

CONFIG_PATH = "config/config.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def build_prompt(article):

    article_text = article["article_text"][:2000]

    prompt = f"""
ROLE
You are a LinkedIn technology creator who writes highly engaging and viral tech posts.

TASK
Based on the article provided, generate EXACTLY 3 different LinkedIn posts.

Each post must present a unique perspective or framing of the story.

IMPORTANT:
Generate exactly 3 posts. No more. No less.


POST FORMAT

Each post must follow this flow, but DO NOT write the section names:

1. Start with a strong hook.
2. Write a short paragraph explaining the news/event.
3. Write a short paragraph explaining the larger industry shift.
4. Write exactly 3 bullet insights using this format:

💡 Insight  
💡 Insight  
💡 Insight  

5. Write a short takeaway paragraph summarizing the key lesson.
6. End with a question to drive engagement.
7. Add 8 to 12 relevant hashtags at the end and this is must.
8. The hashtags must be relevant to the article and the topic, and they must only appear at the very end of the post.


CRITICAL RULES( must follow these strictly)

• DO NOT write labels like:
HOOK
CONTEXT
INDUSTRY SHIFT
INSIGHTS
TAKEAWAY
QUESTION


• Each post must be under 1200 characters

• Write in a conversational LinkedIn creator tone (not academic)

• Use short sentences and whitespace for readability

• Hashtags must appear only at the very end of each post

Important: (must follow these strictly)

1.no need to mention the hook style in the post, just write the post with the appropriate hook style.
2. Separate the posts using this delimiter: "===POST==="


HOOK STYLES

Use a different hook style for each post.

Style 1 — Surprising Statement  
Example:  
🚨 AI Just Crossed a Dangerous Line.

Style 2 — Curiosity Hook  
Example:  
Most people think AI is about chatbots.  
But something bigger is happening.

Style 3 — Contrarian Take  
Example:  
Everyone is celebrating this AI breakthrough.  
But very few understand the real impact.


ARTICLE TITLE:
{article["title"]}

ARTICLE CONTENT:
{article_text}


"""
    return prompt

def generate_posts(article):
    config = load_config()
    api_key = os.getenv("OPENROUTER_API_KEY")

    prompt = build_prompt(article)

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "linkedin-auto-poster"
    }

    payload = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    response = requests.post(url, headers=headers, json=payload)

    # print debug info if API fails
    if response.status_code != 200:
        print("\nOpenRouter API Error:")
        print(response.text)

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]