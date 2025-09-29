"""Keyword-based scoring helpers for the Brain service."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for type checkers
    from brain.app import Draft, Post


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


def simple_relevance_score(title: str, body: Optional[str]) -> float:
    """Score a post using keyword presence in title and body."""

    text = f"{title or ''} {body or ''}".lower()
    score = 0.0

    for keyword, weight in RELEVANCE_KEYWORDS.items():
        if keyword in text:
            score += weight

    for keyword, weight in GOODWILL_KEYWORDS.items():
        if keyword in text:
            score += weight

    return min(score, 1.0)


def _topic_hint(post: "Post") -> str:
    title = getattr(post, "title", "") or ""
    if title:
        clipped = title.strip().split("?")[0][:60]
        return clipped or "your setup"

    subreddit = getattr(post, "subreddit", None)
    if subreddit:
        return f"the crew in r/{subreddit}"

    return "your setup"


def make_drafts(post: "Post") -> List["Draft"]:
    """Return three tone-distinct drafts for the supplied post."""

    from brain.app import Draft  # Local import to avoid circular dependency.

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
