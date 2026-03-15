from __future__ import annotations
import re, random, secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from time import time
from urllib.parse import unquote

import jwt as _jwt
from flask import jsonify, request, make_response

from config import JWT_SECRET, JWT_EXP_DAYS, COUNTRY_MAP
from models import User, db
from store import likes_store, ratings_store


# ── API Response Helpers ────────────────────────────────────────────
def err(message: str, status: int = 400, **extra):
    payload = {"ok": False, "error": message}
    payload.update(extra)
    return jsonify(payload), status


# ── JWT ────────────────────────────────────────────────────────────
def make_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXP_DAYS),
    }
    return _jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current_user() -> User | None:
    # Try httpOnly cookie first, then Authorization header fallback
    token = request.cookies.get("auth_token", "")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return None
    try:
        payload = _jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return db.session.get(User, payload["user_id"])
    except Exception:
        return None


def set_auth_cookie(response, token: str):
    response.set_cookie(
        "auth_token", token,
        httponly=True,
        samesite="Lax",
        max_age=JWT_EXP_DAYS * 24 * 3600,
        secure=False,
    )
    return response


def clear_auth_cookie(response):
    response.delete_cookie("auth_token", samesite="Lax")
    return response


# ── Rate Limiting ──────────────────────────────────────────────────
_rate_ts: dict[str, float] = defaultdict(float)
_RATE_WINDOW = {
    "like":         2,
    "comment_anon": 30,
    "comment_auth": 5,
    "comment_like": 2,
}


def rate_ok(action: str, extra: str = "") -> tuple[bool, int]:
    ip  = request.remote_addr or "unknown"
    key = f"{action}:{ip}:{extra}"
    now = time()
    window = _RATE_WINDOW.get(action, 2)
    elapsed = now - _rate_ts[key]
    if elapsed < window:
        return False, int(window - elapsed) + 1
    _rate_ts[key] = now
    return True, 0


# ── CAPTCHA ────────────────────────────────────────────────────────
_captcha_store: dict[str, tuple[int, float]] = {}


def get_captcha(ip: str) -> dict:
    a, b = random.randint(1, 9), random.randint(1, 9)
    _captcha_store[ip] = (a + b, time() + 120)
    return {"question": f"{a} + {b} = ?", "expires_in": 120}


def verify_captcha(ip: str, given: int):
    """Returns None if ok, or error string if failed."""
    entry = _captcha_store.get(ip)
    if not entry:
        return "請先取得驗證碼"
    expected, expires = entry
    if time() > expires:
        _captcha_store.pop(ip, None)
        return "驗證碼已過期，請重新取得"
    if given != expected:
        return "驗證碼錯誤"
    _captcha_store.pop(ip, None)
    return None


# ── Spam Detection ─────────────────────────────────────────────────
def is_spam(text: str) -> bool:
    if re.search(r"(.)\1{6,}", text):
        return True
    ascii_alpha = [c for c in text if c.isascii() and c.isalpha()]
    if len(ascii_alpha) > 8 and sum(c.isupper() for c in ascii_alpha) / len(ascii_alpha) > 0.7:
        return True
    return False


# ── Country / Food Helpers ─────────────────────────────────────────
def kstr(code: str, name: str) -> str:
    return f"{code.upper()}|||{unquote(name)}"


def resolve_country_block(code: str, data: dict):
    cu = code.upper()
    name = COUNTRY_MAP.get(cu)
    if name and name in data:
        return cu, name, data[name]
    if cu in data:
        return cu, cu, data[cu]
    return cu, None, None


# ── Like Helpers ───────────────────────────────────────────────────
def like_entry(key: str) -> dict:
    raw = likes_store.get(key, 0)
    if isinstance(raw, int):
        return {"count": raw, "liked_by": []}
    return raw


def liker_id(u) -> str:
    return f"user:{u.id}" if u else f"ip:{request.remote_addr or 'unknown'}"


def like_count(key: str) -> int:
    return int(like_entry(key).get("count", 0))


# ── Rating Helpers ─────────────────────────────────────────────────
def rater_key(u) -> str:
    return f"user:{u.id}" if u else f"ip:{request.remote_addr or 'unknown'}"


def rating_stats(key: str) -> dict:
    vals = list((ratings_store.get(key) or {}).get("user_ratings", {}).values())
    if not vals:
        return {"avg": 0.0, "count": 0}
    return {"avg": round(sum(vals) / len(vals), 1), "count": len(vals)}
