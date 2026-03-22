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

## GitHub Actions Automation (Every 2 Days)
This repository includes a scheduled workflow at [.github/workflows/post-linkedin.yml](.github/workflows/post-linkedin.yml).

It runs every 2 days and can also be started manually from the Actions tab.

### Required GitHub Secrets
Add these repository secrets before enabling automation:
- `OPENROUTER_API_KEY`
- `LINKEDIN_STORAGE_STATE_B64`

### Generate LinkedIn Session File
Run this once on your local machine:

```bash
python scripts/create_linkedin_session.py
```

This creates [data/cookies.json](data/cookies.json) with authenticated Playwright storage state.

### Encode Session for GitHub Secret
Use one of these commands and copy the output into `LINKEDIN_STORAGE_STATE_B64`:

```bash
base64 -i data/cookies.json
```

```bash
base64 data/cookies.json
```

### Notes
- GitHub schedule runs from the repository default branch.
- The workflow commits updated [data/post_history.json](data/post_history.json) so URL duplicate prevention persists across runs.

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
