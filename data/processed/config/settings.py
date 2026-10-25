"""
Centralized configuration module.

Loads all settings from environment variables via python-dotenv.
Every external value (path, key, timeout...) must be declared here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Thư mục lưu persistent browser profile cho Camoufox
BROWSER_PROFILE_DIR: str = os.getenv("BROWSER_PROFILE_DIR", "data/browser_profile")

# File database SQLite — mặc định lưu trong thư mục data/
SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "data/scrap.db")

# ---------------------------------------------------------------------------
# Browser
# ---------------------------------------------------------------------------

# Timeout mặc định (ms) cho Playwright/Camoufox
BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

# Timeout mặc định (giây) cho mọi HTTP request
REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "15.0"))

# ---------------------------------------------------------------------------
# TikTok / Third-party credentials  (KHÔNG hardcode ở đây)
# ---------------------------------------------------------------------------

TIKTOK_SESSION_ID: str = os.getenv("TIKTOK_SESSION_ID", "")

# ---------------------------------------------------------------------------
# Resolve absolute paths
# ---------------------------------------------------------------------------

# Gốc của dự án — thư mục chứa file settings.py là config/, lên 1 cấp là root
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

BROWSER_PROFILE_PATH: Path = _PROJECT_ROOT / BROWSER_PROFILE_DIR
SQLITE_DB_PATH_ABS: Path = _PROJECT_ROOT / SQLITE_DB_PATH
