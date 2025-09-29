# Roadmap

## MVP Checklist
- [ ] Poll a short list of subreddits via the Reddit script OAuth API.
- [ ] Score fetched posts with simple keyword heuristics inside the Brain service.
- [ ] Draft three varied reply options (goodwill, soft recommend, story) that omit disclosures.
- [ ] Package post link plus drafts into a Discord card with Approve/Edit/Decline actions.
- [ ] On Approve, publish the selected draft through the Reddit API.

## Guardrails To Enforce
- [ ] Keep disclosures out of every automated draft so reviewers add them manually.
- [ ] Respect each subreddit's posting limits by throttling per community.
- [ ] Flag no-link windows or other subreddit bans instead of posting.
- [ ] Require human approval before any reply reaches Reddit.

## Operational Setup
- [ ] Populate `.env` with Reddit credentials, OpenAI API key, Discord webhook, subreddit list, and cadence limits.
- [ ] Configure n8n to run the orchestrator flow (timer -> fetch -> Brain -> Discord -> post).
- [ ] Stand up the Python Brain service with the scoring and drafting endpoints.
