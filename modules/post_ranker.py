import json
import requests
import os


CONFIG_PATH = "config/config.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def build_scoring_prompt(posts):

    prompt = f"""
You are a LinkedIn growth strategist.

Evaluate the following LinkedIn posts.

Score each post from 1 to 10 based on:

- Hook strength
- Clarity and readability
- Engagement potential
- Professional tone
- LinkedIn friendliness

POST 1:
{posts[0]}

POST 2:
{posts[1]}

POST 3:
{posts[2]}

Return the result strictly in this format:

POST 1 SCORE: X
POST 2 SCORE: X
POST 3 SCORE: X

BEST POST: POST ?
"""

    return prompt


def score_posts(posts):

    config = load_config()
    api_key = os.getenv("OPENROUTER_API_KEY")

    prompt = build_scoring_prompt(posts)

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
        "temperature": 0.3,
        "max_tokens": 300
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print("\nScoring API Error:")
        print(response.text)

    response.raise_for_status()

    data = response.json()

    result = data["choices"][0]["message"]["content"]

    return result