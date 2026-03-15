from __future__ import annotations
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FOODS_JSON    = DATA_DIR / "foods.json"
LIKES_JSON    = DATA_DIR / "likes.json"
COMMENTS_JSON = DATA_DIR / "comments.json"
RATINGS_JSON  = DATA_DIR / "ratings.json"

JWT_SECRET   = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
JWT_EXP_DAYS = 7

CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "http://localhost:5173")

COUNTRY_MAP = {
    "JP": "Japan",
    "TW": "Taiwan",
    "KR": "Korea",
    "US": "United States",
    "CA": "Canada",
}
