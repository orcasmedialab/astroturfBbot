"""Run locally (Windows):

    .\.venv\Scripts\activate
    pip install fastapi uvicorn pydantic
    python -m uvicorn brain.app:app --reload
"""

from typing import List, Optional, Literal

from fastapi import FastAPI
from pydantic import BaseModel

from brain import settings
from brain.scoring.heuristics import select_response


app = FastAPI()
VERSION = "0.1.0"


class Post(BaseModel):
    """Minimal shape for Reddit submissions the Brain service evaluates."""

    id: str
    title: str
    selftext: Optional[str] = None
    subreddit: Optional[str] = None
    url: Optional[str] = None


class DraftPayload(BaseModel):
    text: str
    include_link: bool
    link_token: Optional[str] = None


class ScoreResult(BaseModel):
    id: str
    score: float
    rationale: str
    category: Literal["goodwill", "product", "skip"]
    draft: DraftPayload
    risk_notes: Optional[str] = None


class ScoreAndDraftRequest(BaseModel):
    posts: List[Post]


class ScoreAndDraftResponse(BaseModel):
    results: List[ScoreResult]


@app.get("/health")
def health() -> dict:
    """Simple readiness probe for monitoring."""

    return {"ok": True, "service": "brain", "version": VERSION}


@app.get("/config")
def config() -> dict:
    """Expose non-secret runtime configuration for downstream services."""

    user_agent = settings.REDDIT_USER_AGENT
    return {
        "subreddits": settings.SUBREDDITS,
        "poll_interval_seconds": settings.POLL_INTERVAL_SECONDS,
        "max_comments_per_sub_per_day": settings.MAX_COMMENTS_PER_SUB_PER_DAY,
        "link_cooldown_hours": settings.LINK_COOLDOWN_HOURS,
        "quiet_hours": settings.QUIET_HOURS,
        "env": settings.ENV,
        "user_agent_set": bool(user_agent and "<your_username>" not in user_agent),
        "openai_key_present": bool(settings.OPENAI_API_KEY),
        "config_files": {
            "defaults": settings.config_file_exists(settings.CONFIG_DEFAULTS_PATH),
            "persona": settings.config_file_exists(settings.CONFIG_PERSONA_PATH),
            "subs": settings.config_file_exists(settings.CONFIG_SUBS_PATH),
            "keywords": settings.config_file_exists(settings.CONFIG_KEYWORDS_PATH),
        },
    }


@app.post("/score_and_draft", response_model=ScoreAndDraftResponse)
def score_and_draft(payload: ScoreAndDraftRequest) -> ScoreAndDraftResponse:
    """Score candidate posts and return placeholder drafts for human review."""

    results: List[ScoreResult] = []
    for post in payload.posts:
        analysis, category, rationale, draft_payload, risk_notes = select_response(post)
        results.append(
            ScoreResult(
                id=post.id,
                score=round(analysis.score, 2),
                rationale=rationale,
                category=category,
                draft=DraftPayload(**draft_payload),
                risk_notes=risk_notes,
            )
        )

    return ScoreAndDraftResponse(results=results)


# curl http://127.0.0.1:8000/health
# curl http://127.0.0.1:8000/config
# curl -X POST http://127.0.0.1:8000/score_and_draft -H "Content-Type: application/json" -d "{"posts":[{"id":"t3_demo","title":"Ski rack worry","selftext":null}]}"

