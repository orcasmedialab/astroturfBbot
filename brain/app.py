"""Run locally (Windows):

    .\.venv\Scripts\activate
    pip install fastapi uvicorn pydantic
    python -m uvicorn brain.app:app --reload
"""

from typing import List, Optional, Literal

from fastapi import FastAPI
from pydantic import BaseModel

from brain import settings
from brain.scoring.heuristics import make_drafts, simple_relevance_score


app = FastAPI()
VERSION = "0.1.0"


class Post(BaseModel):
    """Minimal shape for Reddit submissions the Brain service evaluates."""

    id: str
    title: str
    selftext: Optional[str] = None
    subreddit: Optional[str] = None
    url: Optional[str] = None


class Draft(BaseModel):
    tone: Literal["goodwill", "soft_reco", "story"]
    text: str


class ScoreResult(BaseModel):
    id: str
    score: float
    rationale: str
    drafts: List[Draft]
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
    }


@app.post("/score_and_draft", response_model=ScoreAndDraftResponse)
def score_and_draft(payload: ScoreAndDraftRequest) -> ScoreAndDraftResponse:
    """Score candidate posts and return placeholder drafts for human review."""

    results: List[ScoreResult] = []
    for post in payload.posts:
        score = simple_relevance_score(post.title, post.selftext)
        rationale = "keyword match" if score > 0 else "no strong match"
        drafts = make_drafts(post)
        results.append(
            ScoreResult(
                id=post.id,
                score=round(score, 2),
                rationale=rationale,
                drafts=drafts,
                risk_notes=None,
            )
        )

    return ScoreAndDraftResponse(results=results)


# curl http://127.0.0.1:8000/health
# curl http://127.0.0.1:8000/config
# curl -X POST http://127.0.0.1:8000/score_and_draft -H "Content-Type: application/json" -d "{"posts":[{"id":"t3_demo","title":"Ski rack worry","selftext":null}]}"

