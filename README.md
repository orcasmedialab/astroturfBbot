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
  config/
    defaults.yaml
    keywords.yaml
    persona.json
    subs.json
    templates.md
    examples/
      defaults.example.yaml
      keywords.example.yaml
      persona.example.json
      subs.example.json
      templates.example.md
  brain/
    __init__.py
    app.py
    settings.py
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
   pip install fastapi uvicorn pydantic python-dotenv pyyaml
   ```
3. Launch the API:
   ```powershell
   python -m uvicorn brain.app:app --reload
   ```
4. Test the endpoints:
   ```bash
   curl http://127.0.0.1:8000/health
   curl http://127.0.0.1:8000/config
   curl -X POST http://127.0.0.1:8000/score_and_draft -H "Content-Type: application/json" -d '{"posts":[{"id":"t3_demo","title":"Need a better organizer","selftext":null}]}'
   ```

### `/score_and_draft` response snapshot
```json
{
  "results": [
    {
      "id": "t3_demo",
      "score": 0.7,
      "rationale": "organizer slip signals",
      "category": "product",
      "draft": {
        "text": "If things keep slipping during setup, a compact organizer like this {{PRODUCT_URL}} keeps them in place until you're ready.",
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

## Configuration files
Configuration lives under `config/` and is loaded via environment variables:

- `CONFIG_DEFAULTS_PATH` → YAML of scoring thresholds and drafting knobs (default `config/defaults.yaml`).
- `CONFIG_PERSONA_PATH` → JSON persona/tone guidance.
- `CONFIG_SUBS_PATH` → JSON array describing subreddit rules.
- `CONFIG_KEYWORDS_PATH` → YAML of keyword patterns and weights.
- `CONFIG_DRAFTS_PATH` → YAML containing goodwill and product draft templates (with optional `{{PRODUCT_URL}}` token).

Tracked `*.example.*` files under `config/examples/` provide neutral defaults—copy them to their non-example counterparts for real use:

```bash
cp config/examples/defaults.example.yaml config/defaults.yaml
cp config/examples/persona.example.json config/persona.json
cp config/examples/subs.example.json config/subs.json
cp config/examples/keywords.example.yaml config/keywords.yaml
cp config/examples/templates.example.md config/templates.md
```

Keep product- or campaign-specific data in those config files rather than in Python modules or prompts. Draft templates should reference `{{PRODUCT_URL}}` when a human needs to swap in a real link. If you rely on YAML configs, ensure `pyyaml` is installed (see install step above).

Legacy `brain/prompts/` assets have been removed. Persona and tone live in `config/persona.json` (copy from `config/examples/persona.example.json`), and any optional human drafting notes belong in `config/templates.md` (see `config/examples/templates.example.md`).

## Quickstart
1. Create a Reddit app (type `script`) -> capture `client_id` and `secret`.
2. Create a Discord webhook (Server Settings -> Integrations -> Webhooks).
3. Copy `.env.example` to `.env`, fill secrets, and adjust the `CONFIG_*` paths if your config files live elsewhere.
4. Copy the example configs under `config/examples/` to their working counterparts and edit them for your brand.
5. Brain:
    ```bash
    cd brain
    python -m venv .venv && source .venv/bin/activate
    pip install fastapi uvicorn httpx openai pyyaml
    uvicorn app:app --reload
    ```
6. n8n:
    ```bash
    cd n8n
    docker compose up -d
    ```
    Import `workflows/reddit-scout.json` and `workflows/reddit-publish.json`, set credentials, then run once manually.
7. Approve a draft in Discord to test end-to-end.

## Phase 2A: n8n skeleton + Discord ping
1. Ensure `DISCORD_WEBHOOK_URL` is set in your repo `.env`.
2. Launch n8n:
   ```powershell
   docker compose -f n8n/docker-compose.yml up -d
   ```
3. Browse to http://localhost:5678 and import `n8n/workflows/reddit-scout.json`.
4. Edit the Discord node URL if needed so it reads `{{$env.DISCORD_WEBHOOK_URL}}`, then click **Execute Node** to test.
5. Confirm a message posts in Discord showing the title, category, score, and draft text.

> Brain must be running locally at http://127.0.0.1:8000 (the workflow reaches it via http://host.docker.internal:8000).

