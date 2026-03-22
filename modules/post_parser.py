import re

def split_posts(posts_text):

    # Detect many variations of post separators
    separators = [
        r"===POST===",
        r"===POST\s*\d*===",
        r"==POST==",
        r"\*\*POST\*\*",
        r"\*\*POST\s*\d*\*\*",
        r"POST\s*\d*:",
    ]

    pattern = "|".join(separators)

    posts = re.split(pattern, posts_text, flags=re.IGNORECASE)

    cleaned_posts = []

    for p in posts:
        p = p.strip()

        # remove meta text blocks
        if "here are" in p.lower():
            continue

        if len(p) < 120:
            continue

        cleaned_posts.append(p)

    return cleaned_posts