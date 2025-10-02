# brain/settings.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


load_dotenv()


def _load_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError(
            f"PyYAML is required to read YAML config files. Unable to load {path}."
        )
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data


def load_config_file(path_str: str | None, fallback_example_path: str | None) -> Any:
    """Load configuration from the provided path or fall back to the example file."""

    candidates = []
    if path_str:
        candidates.append(Path(path_str))
    if fallback_example_path:
        candidates.append(Path(fallback_example_path))

    for candidate in candidates:
        if candidate.exists():
            if candidate.suffix.lower() in {".yaml", ".yml"}:
                return _load_yaml(candidate)
            if candidate.suffix.lower() == ".json":
                return _load_json(candidate)
    return {}


REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME      = os.getenv("REDDIT_USERNAME")
# Interactive prompts should happen when posting, not during module import.
REDDIT_PASSWORD      = os.getenv("REDDIT_PASSWORD")
REDDIT_USER_AGENT    = os.getenv("REDDIT_USER_AGENT", "slopeScout/0.1 (by u/<your_username>)")

OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL  = os.getenv("DISCORD_WEBHOOK_URL")

SUBREDDITS           = [s.strip() for s in os.getenv("SUBREDDITS","").split(",") if s.strip()]
POLL_INTERVAL_SECONDS= int(os.getenv("POLL_INTERVAL_SECONDS","300"))
MAX_COMMENTS_PER_SUB_PER_DAY = int(os.getenv("MAX_COMMENTS_PER_SUB_PER_DAY","3"))
LINK_COOLDOWN_HOURS  = int(os.getenv("LINK_COOLDOWN_HOURS","96"))
QUIET_HOURS          = os.getenv("QUIET_HOURS","01:00-06:30")

DATABASE_URL         = os.getenv("DATABASE_URL","sqlite:///./astroturf.db")
ENV                  = os.getenv("ENV","dev")

CONFIG_DEFAULTS_PATH = os.getenv("CONFIG_DEFAULTS_PATH", "config/defaults.yaml")
CONFIG_PERSONA_PATH  = os.getenv("CONFIG_PERSONA_PATH", "config/persona.json")
CONFIG_SUBS_PATH     = os.getenv("CONFIG_SUBS_PATH", "config/subs.json")
CONFIG_KEYWORDS_PATH = os.getenv("CONFIG_KEYWORDS_PATH", "config/keywords.yaml")

DEFAULTS_CFG = load_config_file(CONFIG_DEFAULTS_PATH, "config/examples/defaults.example.yaml")
PERSONA_CFG  = load_config_file(CONFIG_PERSONA_PATH, "config/examples/persona.example.json")
SUBS_CFG     = load_config_file(CONFIG_SUBS_PATH, "config/examples/subs.example.json")
KEYWORDS_CFG = load_config_file(CONFIG_KEYWORDS_PATH, "config/examples/keywords.example.yaml")


def config_file_exists(path_str: str | None) -> bool:
    return bool(path_str and Path(path_str).exists())
