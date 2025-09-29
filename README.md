# Astroturf Bot

A hybrid workflow for Reddit community participation with **human-in-the-loop approvals**.
- Orchestration: n8n (cron → fetch → score/draft → Discord approval → post)
- Brain: Python FastAPI service that scores threads and drafts 2–3 natural replies (no auto-disclosure)

> **Disclosure policy**: Drafts do **not** mention founder status or include disclosure. The human reviewer adds disclosure when appropriate before posting.

## Architecture
n8n (Cron)
- Fetch new posts (Reddit API, script app)
- POST /score_and_draft → Brain (FastAPI + Codex)
- Return top candidates + 3 drafts
- Discord webhook (Approve / Edit / Decline)
- On Approve → Post via Reddit API

## Repo layout
```bash
├── astroturf-bot/
│   ├── brain/
│   │   ├── app.py
│   ├── prompts/
│   │   ├── persona_skiing.json
│   │   ├── goodwill.txt
│   │   ├── soft_reco.txt
│   │   ├── story.txt
│   ├── scoring/
│   │   ├── heuristics.py
│   │   ├── embeddings.py
│   │   ├── settings.py
│   ├── n8n/
│   │   ├── docker-compose.yml
│   ├── workflows/
│   │   ├── reddit-scout.json
│   │   ├── reddit-publish.json
│   ├── ops/
│   ├── README.md
│   ├── .env.example
```

## Quickstart
1. Create a **Reddit app** (type `script`) → get `client_id` & `secret`.
2. Create a **Discord webhook** (Server Settings → Integrations → Webhooks).
3. Copy `.env.example` to `.env` and fill secrets.
4. **Brain**:
    ```bash
    cd brain
    python -m venv .venv && source .venv/bin/activate
    pip install fastapi uvicorn httpx openai
    uvicorn app:app --reload
    ```
5. n8n:
    cd n8n
    docker compose up -d
    Import workflows/reddit-scout.json and workflows/reddit-publish.json, set credentials, and run once manually.
6. Approve a draft in Discord to test end-to-end.

