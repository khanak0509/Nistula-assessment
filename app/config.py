"""
Env-driven config.

Keys live in .env, never in code — so rotating a key doesn't need a redeploy
and accidental git commits don't leak credentials.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# .env sits at the project root (the parent of the app/ folder).
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

CLAUDE_API_KEY: str | None = os.getenv("CLAUDE_API_KEY")
