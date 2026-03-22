# LinkedIn AI Posting Bot

## Overview
This project streamlines the end-to-end workflow for creating and publishing LinkedIn posts from trending AI news.

It automatically:
- Fetches trending AI news
- Analyzes and ranks relevance
- Generates LinkedIn posts using LLMs
- Validates and improves structure
- Scores posts using AI
- Selects the best post
- Publishes to LinkedIn from local execution (manual login step)

## Features
- Automated news aggregation
- AI-powered content generation
- Semantic duplicate filtering
- Post validation and rewriting
- AI scoring system
- LinkedIn posting using Playwright

## Tech Stack
- Python
- OpenRouter (LLMs)
- Sentence Transformers (semantic similarity)
- Playwright (browser automation)

## Project Pipeline
News -> Scrape -> Rank -> Filter -> Generate -> Validate -> Score -> Post

## Setup Instructions
1. Clone repo

```bash
git clone <your-repo-url>
cd LinkedIn-Automation
```

2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set environment variable

```bash
export OPENROUTER_API_KEY="your_api_key"
```

5. Run

```bash
python main.py
```

## Important Notes
- `cookies.json` is not included for security.
- API keys must be set via environment variables.
- Project runs locally and requires LinkedIn login in the browser.

## Future Improvements
- GitHub Actions automation
- Scheduled posting
- Database integration
- Multi-platform posting

## Disclaimer
This project is for educational purposes.
Use responsibly and respect LinkedIn's terms.
