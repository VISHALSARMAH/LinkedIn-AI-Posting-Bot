import re
import json
import requests
import os
import textwrap

CONFIG_PATH = "config/config.json"

PROMPT_LEAKAGE_TERMS = [
    "curiosity hook",
    "contrarian take",
    "===post===",
    "shorter hook",
    "here is the post",
    "here is your post",
    "here is the rewritten post",
    "here's the rewritten post",
    "rewritten post:",
    "improved post:",
    "takeaway:",
]

WEAK_CTA_PATTERNS = [
    "what do you think",
    "thoughts",
    "agree",
    "your opinion",
    "let me know",
]

DEFAULT_HASHTAGS = [
    "#AI",
    "#Leadership",
    "#Innovation",
    "#Tech",
    "#FutureOfWork",
    "#Business",
    "#LinkedIn",
    "#Growth",
]

ACADEMIC_REPLACEMENTS = {
    "this phenomenon is driven by": "this is happening because",
    "is driven by": "happens because",
    "moreover": "also",
    "therefore": "so",
    "furthermore": "also",
}


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def validate_post(post):
    """
    Validate post with STRICT LinkedIn formatting rules.
    """
    if not post or not post.strip():
        return False

    text = post.replace("\r\n", "\n").strip()
    lines = text.split("\n")
    non_empty = [line.strip() for line in lines if line.strip()]

    if not non_empty:
        return False

    lowered = text.lower()
    if "**" in text:
        return False
    if any(term in lowered for term in PROMPT_LEAKAGE_TERMS):
        return False

    # 1. Hook must be first line, <= 80 chars, one sentence.
    hook = lines[0].strip()
    if not hook or len(hook) > 80:
        return False
    sentence_count = len(re.findall(r"[^.!?]+[.!?]", hook))
    if sentence_count > 1:
        return False

    # 2. Blank line after hook.
    if len(lines) < 2 or lines[1].strip():
        return False

    # 3. Exactly 3 bullets and each bullet starts with `💡 `.
    bullet_lines = [line.strip() for line in lines if line.strip().startswith("💡 ")]
    if len(bullet_lines) != 3:
        return False
    if any("insight:" in line.lower() for line in bullet_lines):
        return False

    # 4. Avoid walls of text.
    regular_block = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            regular_block = 0
            continue
        if stripped.startswith("💡 ") or stripped.startswith("#"):
            regular_block = 0
            continue
        regular_block += 1
        if regular_block > 3:
            return False

    # 5. Must contain a question CTA and it should not be weak.
    cta_candidates = [line for line in non_empty if line.endswith("?")]
    if not cta_candidates:
        return False
    cta = cta_candidates[-1].lower()
    if any(pattern in cta for pattern in WEAK_CTA_PATTERNS):
        return False

    # 6. Check hashtags: 6-10 and on last non-empty line.
    hashtags = re.findall(r"#\w+", text)
    if len(hashtags) < 6 or len(hashtags) > 10:
        return False
    last_non_empty_line = non_empty[-1]
    hashtag_pattern = r"^#\w+(?:\s+#\w+)*$"
    if not re.match(hashtag_pattern, last_non_empty_line):
        return False

    return True


def _replace_academic_language(text):
    output = text
    for source, target in ACADEMIC_REPLACEMENTS.items():
        output = re.sub(source, target, output, flags=re.IGNORECASE)
    return output


def _sanitize_line(line):
    cleaned = line.replace("**", "").replace("__", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = _replace_academic_language(cleaned)
    cleaned = re.sub(r"^insight:\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _enforce_hook(first_line):
    hook = _sanitize_line(first_line)
    if not hook:
        hook = "AI is moving faster than most teams can handle."

    # Keep only one sentence in hook.
    match = re.search(r"[.!?]", hook)
    if match:
        hook = hook[:match.end()].strip()
    else:
        hook = hook.rstrip(".,;:!") + "."

    if len(hook) > 80:
        hook = hook[:80].rstrip()
        if hook and hook[-1] not in ".!?":
            hook = hook.rstrip(".,;:") + "."

    return hook


def _strong_cta(text):
    lowered = text.lower()
    if "data" in lowered or "privacy" in lowered:
        return "Would you trade your data for money?"
    if "risk" in lowered or "safety" in lowered:
        return "What would you do in this situation?"
    return "What would you do in this situation?"


def _collect_hashtags(raw_hashtags):
    seen = set()
    result = []
    for tag in raw_hashtags + DEFAULT_HASHTAGS:
        if not tag.startswith("#"):
            continue
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(tag)
        if len(result) == 10:
            break

    if len(result) < 6:
        for tag in DEFAULT_HASHTAGS:
            if tag.lower() not in seen:
                result.append(tag)
                seen.add(tag.lower())
            if len(result) == 6:
                break

    return result[:10]


def _split_long_paragraph(paragraph, width=72, max_lines=3):
    wrapped = textwrap.wrap(paragraph, width=width)
    if not wrapped:
        return []
    if len(wrapped) <= max_lines:
        return ["\n".join(wrapped)]

    chunks = []
    for i in range(0, len(wrapped), max_lines):
        chunk = wrapped[i:i + max_lines]
        if chunk:
            chunks.append("\n".join(chunk))
    return chunks


def _remove_separators(text):
    """
    Remove separator lines like --- and ===
    """
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped and re.match(r"^[-=]{2,}$", stripped):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _merge_broken_lines(raw_lines):
    """
    Merge lines that were split mid-sentence.
    If a line does NOT end with '.', '?', '!' → merge with next line.
    Exception: lines starting with 💡 are treated as atomic (not merged).
    """
    merged = []
    current = ""

    for line in raw_lines:
        stripped = line.strip()

        # Skip empty lines; they mark paragraph breaks
        if not stripped:
            if current:
                merged.append(current)
                current = ""
            merged.append("")
            continue

        # Bullet points are atomic—never merge them with other lines
        if stripped.startswith("💡"):
            if current:
                merged.append(current)
                current = ""
            merged.append(stripped)
            continue

        # If current buffer is empty, start a new one
        if not current:
            current = stripped
        else:
            # Current buffer has content; check if it's a complete sentence
            if not current.endswith((".", "?", "!", ":")):
                # Incomplete sentence; merge with this line
                current = current + " " + stripped
            else:
                # Complete sentence; push current to result and start fresh
                merged.append(current)
                current = stripped

    # Don't forget the last buffer
    if current:
        merged.append(current)

    return merged


def clean_post(post):
    """
    Enforce strict clean LinkedIn output formatting.
    
    1. Remove separators (---, ===, etc.)
    2. Merge broken lines (lines split mid-sentence)
    3. Filter prompt leakage
    4. Extract bullets and hashtags
    5. Format with strict spacing
    """
    if not post:
        return ""

    text = post.replace("\r\n", "\n")
    text = text.replace("•", "💡 ")
    text = re.sub(r"\*+", "", text)
    text = _remove_separators(text)

    # Remove unwanted labels.
    text = re.sub(r"\b(Insight|Takeaway)\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bHere\s+is\s+the\s+rewritten\s+post\s*:\s*", "", text, flags=re.IGNORECASE)

    # Bullet formatting: put each bullet marker on a new line.
    text = re.sub(r"(?<!\n)\s*💡\s*", "\n💡 ", text)
    text = re.sub(r"\n\s*💡\s*", "\n💡 ", text)

    # Hashtag fixes requested by user.
    text = re.sub(r"(?i)hashtag#", "#", text)
    text = re.sub(r"(\w)#", r"\1 #", text)

    # Normalize spaces and trailing whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.rstrip() for line in text.split("\n")]

    # Smart line merge:
    # if current line does not end with punctuation and next starts lowercase,
    # merge into one sentence. Preserve blank lines, bullets, hashtags.
    merged_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            merged_lines.append("")
            i += 1
            continue

        if line.startswith("💡") or line.startswith("#"):
            merged_lines.append(line)
            i += 1
            continue

        current = line
        while i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if not nxt:
                break
            if nxt.startswith("💡") or nxt.startswith("#"):
                break
            if current.endswith((".", "!", "?", ":")):
                break
            if re.match(r"^[a-z]", nxt):
                current = f"{current} {nxt}"
                i += 1
                continue
            break

        merged_lines.append(current)
        i += 1

    # Collapse multiple blank lines to exactly one blank line between paragraphs.
    normalized_lines = []
    previous_blank = False
    for line in merged_lines:
        stripped = re.sub(r"[ \t]+", " ", line).strip()
        if not stripped:
            if not previous_blank:
                normalized_lines.append("")
            previous_blank = True
            continue
        normalized_lines.append(stripped)
        previous_blank = False

    raw_hashtags = re.findall(r"#\w+", "\n".join(normalized_lines))

    filtered_lines = []
    bullet_candidates = []

    for raw_line in normalized_lines:
        if not raw_line:
            continue

        lower = raw_line.lower()
        if any(term in lower for term in PROMPT_LEAKAGE_TERMS):
            continue

        cleaned_line = _sanitize_line(raw_line)
        cleaned_line = re.sub(r"[ \t]+", " ", cleaned_line).strip()
        if not cleaned_line:
            continue

        if cleaned_line.startswith("💡"):
            bullet_text = cleaned_line.replace("💡", "", 1).strip()
            if bullet_text:
                bullet_candidates.append(bullet_text)
            continue

        if re.match(r"^[-*]\s+", cleaned_line):
            bullet_candidates.append(re.sub(r"^[-*]\s+", "", cleaned_line).strip())
            continue

        # Do not keep standalone hashtag lines in body; we'll append at end.
        if cleaned_line.startswith("#"):
            continue

        filtered_lines.append(cleaned_line)

    if not filtered_lines:
        filtered_lines = [
            "AI is changing how teams make decisions.",
            "The pace is exciting, but the risk is real.",
        ]

    hook = _enforce_hook(filtered_lines[0])

    question_lines = [line for line in filtered_lines[1:] if line.endswith("?")]
    chosen_question = ""
    if question_lines:
        candidate = question_lines[-1].strip()
        lowered = candidate.lower().rstrip("?")
        if not any(pattern in lowered for pattern in WEAK_CTA_PATTERNS):
            chosen_question = candidate

    cta = chosen_question or _strong_cta(" ".join(filtered_lines))

    body_lines = []
    for line in filtered_lines[1:]:
        if line == chosen_question:
            continue
        if line.endswith("?"):
            continue
        body_lines.append(line)

    if not bullet_candidates:
        seed = body_lines[:3] if body_lines else filtered_lines[:3]
        bullet_candidates = seed

    normalized_bullets = []
    for entry in bullet_candidates:
        clean_entry = _sanitize_line(entry)
        clean_entry = re.sub(r"^insight:\s*", "", clean_entry, flags=re.IGNORECASE)
        clean_entry = re.sub(r"[ \t]+", " ", clean_entry).strip().rstrip(".")
        if clean_entry:
            normalized_bullets.append(f"💡 {clean_entry}")
        if len(normalized_bullets) == 3:
            break

    while len(normalized_bullets) < 3:
        normalized_bullets.append(f"💡 Key insight {len(normalized_bullets) + 1}")

    hashtags = _collect_hashtags(raw_hashtags)
    hashtags_line = " ".join(hashtags)

    sections = [hook]
    sections.extend([line for line in body_lines if line.strip()])
    sections.append("\n".join(normalized_bullets))
    sections.append(cta.strip())
    sections.append(hashtags_line.strip())

    clean_sections = [section.strip() for section in sections if section and section.strip()]
    return "\n\n".join(clean_sections).strip()


def build_rewrite_prompt(post):
    """
    Build a strict formatting prompt for post rewriting.
    """
    prompt = f"""You are a LinkedIn content expert. Rewrite the following post with STRICT formatting.

STRICT FORMAT RULES (MUST FOLLOW):

1. Hook must be first line only
2. Hook max 80 characters and one sentence only
3. Add a blank line after hook
4. Use short paragraphs with blank lines between sections
5. No paragraph should exceed 2-3 lines
6. MUST include exactly 3 bullets and each bullet must start with "💡 "
7. Remove "Insight:" style labels
8. End with ONE strong engaging question (not "What do you think?")
9. Add 6-10 hashtags on a NEW LINE as the final line
10. DO NOT include prompt leakage phrases or markdown (**)

EXAMPLE FORMAT:
🚨 AI Just Crossed a Dangerous Line.

Context paragraph explaining the news.

Another short paragraph with industry insight.

💡 First insight
💡 Second insight
💡 Third insight

Final takeaway thought here.

What would you do in this situation?

#LinkedIn #Tech #AI #Innovation #Future #Growth

POST TO REWRITE:
{post}

IMPORTANT: Return ONLY the final post. No explanations. No extra text."""

    return prompt


def rewrite_post(post):
    """
    Rewrite a post using OpenRouter API with strict LinkedIn formatting.
    Uses meta-llama/llama-3-8b-instruct model.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")

    prompt = build_rewrite_prompt(post)

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
        "max_tokens": 1500
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print("\nOpenRouter API Error during rewrite:")
        print(response.text)

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"].strip()


def post_process(post):
    """
    Backward-compatible wrapper around clean_post().
    """
    return clean_post(post)


def process_posts(posts):
    """
    Process posts with strict formatting and validation.

    Flow:
    1. Apply post_process() to all posts (clean & format)
    2. Validate each post
    3. If invalid: rewrite with rewrite_post(), then post_process again
    4. Return all validated & formatted posts
    """
    # First pass: strict clean all posts
    formatted_posts = [clean_post(p) for p in posts]

    validated_posts = []

    for i, post in enumerate(formatted_posts, start=1):
        if validate_post(post):
            print(f"✓ Post {i} is valid")
            validated_posts.append(post)
        else:
            print(f"⚠ Post {i} needs rewriting...")
            rewritten = rewrite_post(post)
            rewritten = clean_post(rewritten)
            validated_posts.append(rewritten)

    return validated_posts
