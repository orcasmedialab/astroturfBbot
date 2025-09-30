"""Embedding-backed scoring helpers (stubs)."""

from __future__ import annotations

from typing import Optional


# TODO: integrate sentence-transformers behind a feature flag and blend
# heuristic + semantic scores. The helper below will eventually surface
# that semantic component once dependencies are in place.

def semantic_score(title: str, body: Optional[str]) -> float:
    """Placeholder semantic score until embeddings are wired up."""

    _ = title, body
    return 0.0
