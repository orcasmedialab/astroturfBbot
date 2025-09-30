"""Keyword-based scoring helpers for the Brain service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, Literal

if TYPE_CHECKING:  # pragma: no cover - import only for type checkers
    from brain.app import Post


@dataclass(frozen=True)
class PostAnalysis:
    score: float
    has_problem: bool
    has_context: bool
    has_solution: bool
    has_beginner: bool


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

BEGINNER_PATTERNS = [
    r"first\s+season",
    r"beginner",
    r"new\s+to\s+skiing",
    r"tips\s+for",
    r"organize\s+gear",
    r"car\s+setup",
    r"winter\s+prep",
    r"parking\s+lot\s+routine",
]


PROBLEM_VERB_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in PROBLEM_VERB_PATTERNS]
CONTEXT_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in CONTEXT_PATTERNS]
SOLUTION_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in SOLUTION_PATTERNS]
BEGINNER_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in BEGINNER_PATTERNS]


def simple_relevance_score(title: str, body: Optional[str]) -> float:
    """Score a post using problem/context/solution heuristics."""

    return analyze_post(title, body).score


def analyze_post(title: str, body: Optional[str]) -> PostAnalysis:
    """Return scoring signals for a candidate post."""

    text = _normalize_text(f"{title or ''} {body or ''}")

    has_problem = _matches(PROBLEM_VERB_REGEXES, text)
    has_context = _matches(CONTEXT_REGEXES, text)
    has_solution = _matches(SOLUTION_REGEXES, text)
    has_beginner = _matches(BEGINNER_REGEXES, text)

    score = 0.0
    if has_problem and has_context:
        score += 0.5
    elif has_problem:
        score += 0.3

    if has_solution:
        score += 0.2

    if has_beginner:
        score += 0.2

    return PostAnalysis(
        score=min(score, 1.0),
        has_problem=has_problem,
        has_context=has_context,
        has_solution=has_solution,
        has_beginner=has_beginner,
    )


def select_response(
    post: "Post",
) -> tuple[PostAnalysis, Literal["goodwill", "product", "skip"], str, dict[str, object], Optional[str]]:
    """Choose a single draft payload and category for the post."""

    title = getattr(post, "title", "")
    body = getattr(post, "selftext", None)
    analysis = analyze_post(title, body)

    category, rationale = _categorize(analysis)
    draft_payload = _build_draft(category, post)
    risk_notes = "Low-signal thread; skip for now." if category == "skip" else None

    return analysis, category, rationale, draft_payload, risk_notes


def _normalize_text(raw: str) -> str:
    """Lowercase and stabilize punctuation for consistent regex matching."""

    text = raw or ""
    for curly in ("\u2018", "\u2019", "\u2032"):
        text = text.replace(curly, "'")
    for dash in ("-", "\u2013", "\u2014"):
        text = text.replace(dash, " ")
    text = text.lower()
    return " ".join(text.split())


def _matches(patterns: list[re.Pattern[str]], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _categorize(analysis: PostAnalysis) -> tuple[Literal["goodwill", "product", "skip"], str]:
    if analysis.has_problem and analysis.has_context:
        return "product", "rack/parking-lot slip signals"
    if analysis.has_beginner or analysis.has_context or analysis.has_solution:
        return "goodwill", "beginner/setup keywords"
    return "skip", "no strong match"


def _build_draft(category: str, post: "Post") -> dict[str, object]:
    topic = _topic_hint(post)

    if category == "product":
        text = (
            "If your skis are sliding while you buckle boots, a compact clamp holder like this "
            "{{PRODUCT_URL}} keeps them locked until you're rolling again."
        )
        return {"text": text, "include_link": True, "link_token": "{{PRODUCT_URL}}"}

    if category == "goodwill":
        text = (
            f"If you're dialing {topic}, brushing snow off the rack pads and snugging a quick strap before you "
            "buckle keeps the edges off the paint."
        )
        return {"text": text, "include_link": False, "link_token": None}

    return {"text": "", "include_link": False, "link_token": None}


def _topic_hint(post: "Post") -> str:
    title = getattr(post, "title", "") or ""
    if title:
        clipped = title.strip().split("?")[0][:60]
        return clipped or "your setup"

    subreddit = getattr(post, "subreddit", None)
    if subreddit:
        return f"the crew in r/{subreddit}"

    return "your setup"

