"""Keyword-based scoring helpers for the Brain service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, Literal, Iterable

if TYPE_CHECKING:  # pragma: no cover - import only for type checkers
    from brain.app import Post

from brain import settings


def _compile_patterns(patterns: Optional[Iterable[str]]) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    if not patterns:
        return compiled
    for pattern in patterns:
        compiled.append(re.compile(pattern, re.IGNORECASE))
    return compiled


@dataclass(frozen=True)
class PostAnalysis:
    score: float
    has_problem: bool
    has_context: bool
    has_solution: bool
    has_beginner: bool


DEFAULT_KEYWORDS = {
    "product_signals": {
        "problem": [r"\bslip\b", r"\bsliding\b", r"fall[\s-]?off", r"\bscratch\b", r"\bscuff\b"],
        "context": [
            r"entryway",
            r"commute",
            r"doorway",
            r"car\s+door",
            r"desk\s+setup",
            r"pet\s+area",
        ],
        "solution": [
            r"holder",
            r"organizer",
            r"hook",
            r"mat",
            r"tray",
        ],
    },
    "goodwill_signals": {
        "beginner": [
            r"first\s+time",
            r"beginner",
            r"new\s+here",
            r"any\s+tips",
            r"how\s+do\s+you\s+organize",
            r"checklist",
            r"setup\s+tips",
        ]
    },
    "weights": {
        "problem_and_context": 0.5,
        "problem_only": 0.3,
        "solution": 0.2,
        "beginner": 0.2,  # TODO: document default beginner weight.
    },
    "normalize": {
        "replace": [
            {"from": "[’]", "to": "'"},
            {"from": "[-–—]", "to": " "},
        ]
    },
}


KEYWORD_CFG = DEFAULT_KEYWORDS | (settings.KEYWORDS_CFG or {})
_WEIGHTS = KEYWORD_CFG.get("weights", {})
WEIGHT_PROBLEM_AND_CONTEXT = _WEIGHTS.get("problem_and_context", 0.5)
WEIGHT_PROBLEM_ONLY = _WEIGHTS.get("problem_only", 0.3)
WEIGHT_SOLUTION = _WEIGHTS.get("solution", 0.2)
WEIGHT_BEGINNER = _WEIGHTS.get("beginner", 0.2)

_PRODUCT_SIGNALS = KEYWORD_CFG.get("product_signals", {})
_GOODWILL_SIGNALS = KEYWORD_CFG.get("goodwill_signals", {})

PROBLEM_VERB_REGEXES = _compile_patterns(_PRODUCT_SIGNALS.get("problem"))
CONTEXT_REGEXES = _compile_patterns(_PRODUCT_SIGNALS.get("context"))
SOLUTION_REGEXES = _compile_patterns(_PRODUCT_SIGNALS.get("solution"))
BEGINNER_REGEXES = _compile_patterns(_GOODWILL_SIGNALS.get("beginner"))


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
        score += WEIGHT_PROBLEM_AND_CONTEXT
    elif has_problem:
        score += WEIGHT_PROBLEM_ONLY

    if has_solution:
        score += WEIGHT_SOLUTION

    if has_beginner:
        score += WEIGHT_BEGINNER

    cap = (settings.DEFAULTS_CFG or {}).get("scoring", {}).get("cap", 1.0)

    return PostAnalysis(
        score=min(score, cap),
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
    risk_notes = None

    if category == "product":
        # TODO: consult subreddit rule cache to confirm link allowances.
        risk_notes = "Links may be restricted in this subreddit"
    elif category == "skip":
        risk_notes = "Low-signal thread; skip for now."

    return analysis, category, rationale, draft_payload, risk_notes


def _normalize_text(raw: str) -> str:
    """Lowercase and stabilize punctuation for consistent regex matching."""

    text = (raw or "")
    for rule in KEYWORD_CFG.get("normalize", {}).get("replace", []):
        pattern = rule.get("from")
        replacement = rule.get("to", "")
        if not pattern:
            continue
        text = re.sub(pattern, replacement, text)

    text = text.lower()
    return " ".join(text.split())


def _matches(patterns: list[re.Pattern[str]], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _categorize(analysis: PostAnalysis) -> tuple[Literal["goodwill", "product", "skip"], str]:
    scoring_cfg = (settings.DEFAULTS_CFG or {}).get("scoring", {})
    product_threshold = scoring_cfg.get("product_threshold", 0.45)
    goodwill_threshold = scoring_cfg.get("goodwill_threshold", 0.15)

    if analysis.has_problem and analysis.has_context and analysis.score >= product_threshold:
        return "product", "organizer slip signals"
    if analysis.score >= goodwill_threshold or analysis.has_beginner or analysis.has_context or analysis.has_solution:
        return "goodwill", "beginner/setup keywords"
    return "skip", "no strong match"


def _build_draft(category: str, post: "Post") -> dict[str, object]:
    topic = _topic_hint(post)

    drafting_cfg = (settings.DEFAULTS_CFG or {}).get("drafting", {})
    link_token = drafting_cfg.get("link_token", "{{PRODUCT_URL}}")
    include_link_for_product = drafting_cfg.get("include_link_for_product", True)
    goodwill_allow_links = drafting_cfg.get("goodwill_allow_links", False)

    if category == "product":
        text = _choose_draft_text("product", link_token)
        return {"text": text, "include_link": include_link_for_product, "link_token": link_token}

    if category == "goodwill":
        text = _choose_draft_text("goodwill", link_token)
        return {
            "text": text,
            "include_link": bool(goodwill_allow_links),
            "link_token": link_token if goodwill_allow_links else None,
        }

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


def _choose_draft_text(category: str, link_token: str) -> str:
    drafts_cfg = settings.DRAFTS_CFG or {}
    options = drafts_cfg.get(category, [])
    if isinstance(options, list) and options:
        return str(options[0])

    if category == "product":
        return f"A compact organizer like {link_token} keeps things steady while you finish setup."

    return "A quick organizer prevents scuffs while you set up."

