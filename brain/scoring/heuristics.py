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
        "problem": [r"\bslide\b", r"\bsliding\b", r"\bslip\b", r"fall[\s-]?off", r"\bskate\b", r"\bwander\b"],
        "context": [
            r"buckling?\s+boots?",
            r"boot\s+buckle",
            r"parking[\s-]?lot",
            r"parking\s+lot\s+changeover",
            r"tailgate",
            r"lean(?:ing)?\s+(?:on|against)\s+(?:the\s+)?(?:car|vehicle)",
        ],
        "solution": [
            r"protect(?:ing)?\s+edges?",
            r"edge\s+dings?",
            r"\bpaint\b",
            r"holder",
            r"lean\s+spot",
            r"compact\s+holder",
        ],
    },
    "goodwill_signals": {
        "beginner": [
            r"first\s+season",
            r"beginner",
            r"new\s+to\s+skiing",
            r"tips\s+for",
            r"organize\s+gear",
            r"car\s+setup",
            r"winter\s+prep",
            r"parking\s+lot\s+routine",
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
        return "product", "rack/parking-lot slip signals"
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
        text = (
            "If your skis are sliding while you buckle boots, a compact clamp holder like this "
            f"{link_token} keeps them locked until you're rolling again."
        )
        return {"text": text, "include_link": include_link_for_product, "link_token": link_token}

    if category == "goodwill":
        text = (
            "Quick wipe of the rack pads and a snug strap before you buckle keeps the skis off the paint."
            " Did that on a Crystal lot changeover last week and it held fine."
        )
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

