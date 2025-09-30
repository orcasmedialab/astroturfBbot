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
- Receive scored candidates plus a single recommended draft payload
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

### `/score_and_draft` response snapshot
```json
{
  "results": [
    {
      "id": "t3_demo",
      "score": 0.7,
      "rationale": "rack/parking-lot slip signals",
      "category": "product",
      "draft": {
        "text": "If your skis are sliding while you buckle boots, a compact clamp holder like this {{PRODUCT_URL}} keeps them locked until you're rolling again.",
        "include_link": true,
        "link_token": "{{PRODUCT_URL}}"
      },
      "risk_notes": "Links may be restricted in this subreddit"
    }
  ]
}
```

- `category` signals intent: `product` drafts invite a product mention, `goodwill` stays link-free, `skip` surfaces low-signal threads.
- `include_link` is `true` only when the draft expects a human to swap the `link_token` (e.g., `{{PRODUCT_URL}}`) before posting.
- `link_token` is a placeholder string you replace with the approved URL when posting; it is `null` for goodwill drafts.
- `risk_notes` captures guardrails, such as subreddit link bans, to review before approving.

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
