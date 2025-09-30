Project: Astroturf Bot

Goal: Orchestrate a Reddit helper that (a) builds goodwill with natural, useful comments and (b) surfaces opportunities to optionally mention my product.

Hard rules:
1. Do not hard-code FTC disclosures. Drafts must never mention that I’m the founder; I will add disclosure at approval time.
2. Use Reddit official API (script app OAuth). No scraping, no vote manipulation.
3. Use Discord (not Slack) for human-in-the-loop approval via webhook.

Architecture (hybrid):
1. n8n for orchestration (timer → fetch new posts → call Brain → send to Discord for Approve/Edit/Decline → post on Approve).
2. Brain = small Python service that scores posts and produces 2–3 natural-sounding drafts (no disclosure, I will add those manually).

MVP scope:
- Poll a short list of subreddits.
- Score by simple heuristics (keywords) to start.
- Draft 2–3 varied replies (“goodwill”, “soft recommend”, “story”).
- Send a Discord card with post link + drafts + buttons.
- On Approve, post via Reddit API.

Configs:
.env at repo root with: Reddit creds (script app), OPENAI_API_KEY, DISCORD_WEBHOOK_URL, SUBREDDITS, cadence limits.

Out of scope (for later): 
embeddings, vector store, AutoMod simulation, historical pattern reuse.
