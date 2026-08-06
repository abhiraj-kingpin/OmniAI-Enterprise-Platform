"""Loads backend/.env as a side effect of import. Imported first, and only
for that side effect, by app/main.py — a few modules read environment
variables at import time rather than lazily (e.g. distributed/celery_app.py's
`REDIS_URL`), so .env must already be loaded before those imports run.
Isolating the load_dotenv() call here keeps every other module's imports
clean, instead of needing `# noqa: E402` scattered wherever it would
otherwise sit ahead of them."""

from dotenv import load_dotenv

load_dotenv()
