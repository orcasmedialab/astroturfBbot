# Astroturf Bot

A hybrid workflow for Reddit community participation with **human-in-the-loop approvals**.
- Orchestration: n8n (cron -> fetch -> score/draft -> Discord approval -> post)
- Brain: Python FastAPI service that scores threads and drafts 2-3 natural replies (no auto-disclosure)

See `docs/CODING_PLAN.md` for the delivery outline and `docs/GUARDRAILS.md` for the operating guardrails.

> **Disclosure policy**: All drafts must exclude disclosures; the human reviewer adds disclosure when appropriate before posting.

## Project Docs
- `docs/CODING_PLAN.md` - MVP scope, constraints, and deferred items.
- `docs/GUARDRAILS.md` - Posting safeguards and disclosure rules.
- `docs/ROADMAP.md` - Execution checklist for the MVP, guardrails, and ops setup.

## Architecture
n8n (Cron)
- Fetch new posts (Reddit API, script app)
- POST /score_and_draft -> Brain (FastAPI + Codex)
- Return top candidates + 3 drafts
- Discord webhook (Approve / Edit / Decline)
- On Approve -> Post via Reddit API

## Repo layout
```
astroturfBbot/
  brain/
    __init__.py
    app.py
    settings.py
    prompts/
      goodwill.txt
      persona_skiing.json
      soft_reco.txt
      story.txt
    scoring/
      __init__.py
      embeddings.py
      heuristics.py
  docs/
    CODING_PLAN.md
    GUARDRAILS.md
    ROADMAP.md
  n8n/
    workflows/
      reddit-publish.json
      reddit-scout.json
  ops/
  .env
  .env.example
  README.md
```

## Run the Brain locally (Windows)
1. Activate the virtualenv:
   ```powershell
   .\.venv\Scripts\activate
   ```
2. Install dependencies:
   ```powershell
   pip install fastapi uvicorn pydantic python-dotenv
   ```
3. Launch the API:
   ```powershell
   python -m uvicorn brain.app:app --reload
   ```
4. Test the endpoints:
   ```bash
   curl http://127.0.0.1:8000/health
   curl http://127.0.0.1:8000/config
   curl -X POST http://127.0.0.1:8000/score_and_draft -H "Content-Type: application/json" -d '{"posts":[{"id":"t3_demo","title":"Need a better ski rack","selftext":null}]}'
   ```

## Quickstart
1. Create a Reddit app (type `script`) -> capture `client_id` and `secret`.
2. Create a Discord webhook (Server Settings -> Integrations -> Webhooks).
3. Copy `.env.example` to `.env` and fill secrets.
4. Brain:
    ```bash
    cd brain
    python -m venv .venv && source .venv/bin/activate
    pip install fastapi uvicorn httpx openai
    uvicorn app:app --reload
    ```
5. n8n:
    ```bash
    cd n8n
    docker compose up -d
    ```
    Import `workflows/reddit-scout.json` and `workflows/reddit-publish.json`, set credentials, then run once manually.
6. Approve a draft in Discord to test end-to-end.
