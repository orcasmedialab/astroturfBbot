"""Keyword-based scoring helpers for the Brain service."""

from __future__ import annotations

import re
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for type checkers
    from brain.app import Draft, Post


def simple_relevance_score(title: str, body: Optional[str]) -> float:
    """Score a post using problem/context/solution heuristics."""

    text = _normalize_text(f"{title or ''} {body or ''}")

    has_problem = any(pattern.search(text) for pattern in PROBLEM_VERB_REGEXES)
    has_context = any(pattern.search(text) for pattern in CONTEXT_REGEXES)
    has_solution = any(pattern.search(text) for pattern in SOLUTION_REGEXES)
    has_beginner = any(pattern.search(text) for pattern in BEGINNER_REGEXES)

    score = 0.0
    if has_problem and has_context:
        score += 0.5
    elif has_problem:
        score += 0.3

    if has_solution:
        score += 0.2

    if has_beginner:
        score += 0.2

    return min(score, 1.0)


def _normalize_text(raw: str) -> str:
    """Lowercase and stabilize punctuation for consistent regex matching."""

    text = raw or ""
    for curly in ("\u2018", "\u2019", "\u2032"):
        text = text.replace(curly, "'")
    for dash in ("-", "\u2013", "\u2014"):
        text = text.replace(dash, " ")
    text = text.lower()
    return " ".join(text.split())


PROBLEM_VERB_PATTERNS = [
    r"\bslide\b",
    r"\bsliding\b",
    r"\bslip\b",
    r"fall[\s-]?off",
    r"\bskate\b",
    r"\bwander\b",
]

CONTEXT_PATTERNS = [
    r"buckling?\s+boots?",
    r"boot\s+buckle",
    r"parking[\s-]?lot",
    r"parking\s+lot\s+changeover",
    r"tailgate",
    r"lean(?:ing)?\s+(?:on|against)\s+(?:the\s+)?(?:car|vehicle)",
]

SOLUTION_PATTERNS = [
    r"protect(?:ing)?\s+edges?",
    r"edge\s+dings?",
    r"\bpaint\b",
    r"holder",
    r"lean\s+spot",
    r"compact\s+holder",
]


PROBLEM_VERB_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in PROBLEM_VERB_PATTERNS]
CONTEXT_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in CONTEXT_PATTERNS]
SOLUTION_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in SOLUTION_PATTERNS]
BEGINNER_REGEXES = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"first\s+season",
        r"beginner",
        r"new\s+to\s+skiing",
        r"tips\s+for",
        r"organize\s+gear",
        r"car\s+setup",
        r"winter\s+prep",
        r"parking\s+lot\s+routine",
    )
]


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
