"""Run locally (Windows):

    .\.venv\Scripts\activate
    pip install fastapi uvicorn pydantic
    python -m uvicorn brain.app:app --reload
"""

from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from brain import settings


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
    tone: str = Field(..., regex="^(goodwill|soft_reco|story)$")
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


RELEVANCE_KEYWORDS = {
    "ski rack": 0.35,
    "roof rack": 0.25,
    "skis falling": 0.3,
    "skis slipping": 0.3,
    "parking lot": 0.15,
    "tailgate": 0.15,
    "dings": 0.2,
    "strap": 0.15,
    "bungee": 0.15,
    "magnet": 0.2,
    "protect edges": 0.25,
}

GOODWILL_KEYWORDS = {
    "first season": 0.1,
    "any tips": 0.1,
    "car setup": 0.1,
    "winter prep": 0.1,
    "newbie": 0.1,
}


def _combined_text(post: Post) -> str:
    fields = [post.title, post.selftext or ""]
    return " ".join(part for part in fields if part).lower()


def _score_post(post: Post) -> tuple[float, str]:
    text = _combined_text(post)
    score = 0.0

    for keyword, weight in RELEVANCE_KEYWORDS.items():
        if keyword in text:
            score += weight

    for keyword, weight in GOODWILL_KEYWORDS.items():
        if keyword in text:
            score += weight

    score = min(score, 1.0)
    rationale = "keyword match" if score > 0 else "no strong match"
    return score, rationale


def _topic_hint(post: Post) -> str:
    if post.title:
        clipped = post.title.strip().split("?")[0][:60]
        return clipped or "your setup"
    if post.subreddit:
        return f"the crew in r/{post.subreddit}"
    return "your setup"


def _generate_drafts(post: Post) -> List[Draft]:
    topic = _topic_hint(post)

    goodwill_text = (
        f"If you're dialing {topic}, wiping the rack pads before loading keeps edges"
        " happy on the drive back down."
    )
    soft_reco_text = (
        "A compact clamp-style holder that leans skis at a steady angle kept ours"
        " from chattering on Snoqualmie runs last winter."
    )
    story_text = (
        "Had a night mission at Stevens where a quick bungee around the tips stopped"
        " the slide and saved the hatch paint."
    )

    return [
        Draft(tone="goodwill", text=goodwill_text),
        Draft(tone="soft_reco", text=soft_reco_text),
        Draft(tone="story", text=story_text),
    ]


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
        score, rationale = _score_post(post)
        drafts = _generate_drafts(post)
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
