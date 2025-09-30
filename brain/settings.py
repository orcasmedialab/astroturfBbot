# brain/settings.py
from dotenv import load_dotenv
import os

load_dotenv()

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
