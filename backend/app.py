from __future__ import annotations
import os, json, tempfile, threading, secrets, re, random
from collections import defaultdict
from pathlib import Path
from time import time
from urllib.parse import unquote
from json import JSONDecodeError
from datetime import datetime, timedelta, timezone

import jwt as _jwt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ── 路徑設定 ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FOODS_JSON    = DATA_DIR / "foods.json"
LIKES_JSON    = DATA_DIR / "likes.json"
COMMENTS_JSON = DATA_DIR / "comments.json"
RATINGS_JSON  = DATA_DIR / "ratings.json"

# ── Flask & DB ─────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["JSON_AS_ASCII"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql://webfinal:webfinal@localhost:5433/webfinal"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

JWT_SECRET   = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
JWT_EXP_DAYS = 7

CORS(app, resources={r"/api/*": {"origins": "*"}})
db = SQLAlchemy(app)

# ── DB 模型 ────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name  = db.Column(db.String(100), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "display_name": self.display_name}


class FavoriteList(db.Model):
    __tablename__ = "favorite_lists"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Favorite(db.Model):
    __tablename__ = "favorites"
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    country_code = db.Column(db.String(10), nullable=False)
    food_name    = db.Column(db.String(200), nullable=False)
    list_id      = db.Column(db.Integer, db.ForeignKey("favorite_lists.id"), nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "country_code", "food_name"),)

    def to_dict(self):
        return {
            "id":           self.id,
            "country_code": self.country_code,
            "food_name":    self.food_name,
            "list_id":      self.list_id,
        }

with app.app_context():
    db.create_all()

# ── JWT helpers ────────────────────────────────────────────────────
def _make_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXP_DAYS),
    }
    return _jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def _current_user() -> User | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        payload = _jwt.decode(auth[7:], JWT_SECRET, algorithms=["HS256"])
        return db.session.get(User, payload["user_id"])
    except Exception:
        return None

# ── 共用 JSON 工具 ─────────────────────────────────────────────────
_lock = threading.Lock()

def _atomic_write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8",
                                     dir=str(path.parent)) as tmp:
        json.dump(obj, tmp, ensure_ascii=False, separators=(",", ":"))
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name
    os.replace(tmp_path, path)

def _save_json(path: Path, obj):
    with _lock:
        _atomic_write(path, obj)

def _load_json(path: Path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            _save_json(path, default)
            return default
        return json.loads(raw)
    except FileNotFoundError:
        _save_json(path, default)
        return default
    except JSONDecodeError:
        _save_json(path, default)
        return default

# ── foods 快取 ─────────────────────────────────────────────────────
_foods_cache: dict = {"mtime": None, "data": {}}

def _load_foods_json(force: bool = False) -> dict:
    global _foods_cache
    try:
        st = os.stat(FOODS_JSON)
    except FileNotFoundError:
        _foods_cache.update({"mtime": None, "data": {}})
        return _foods_cache["data"]
    if force or _foods_cache["mtime"] != st.st_mtime:
        try:
            with open(FOODS_JSON, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            data = json.loads(raw) if raw else {}
        except (FileNotFoundError, JSONDecodeError):
            data = {}
        _foods_cache["data"] = data
        _foods_cache["mtime"] = st.st_mtime
    return _foods_cache["data"]

# ── 記憶體資料 ─────────────────────────────────────────────────────
likes_store    = _load_json(LIKES_JSON,    {})
comments_store = _load_json(COMMENTS_JSON, {})
ratings_store  = _load_json(RATINGS_JSON,  {})

# ── IP 限速 ────────────────────────────────────────────────────────
_rate_ts: dict[str, float] = defaultdict(float)
_RATE_WINDOW = {
    "like":         2,
    "comment_anon": 30,   # 匿名留言：30 秒冷卻
    "comment_auth": 5,    # 登入留言：5 秒冷卻
    "comment_like": 2,
}

def _rate_ok(action: str, extra: str = "") -> tuple[bool, int]:
    """回傳 (是否允許, 需等待秒數)"""
    ip  = request.remote_addr or "unknown"
    key = f"{action}:{ip}:{extra}"
    now = time()
    window = _RATE_WINDOW.get(action, 2)
    elapsed = now - _rate_ts[key]
    if elapsed < window:
        return False, int(window - elapsed) + 1
    _rate_ts[key] = now
    return True, 0

# ── 驗證碼暫存 ─────────────────────────────────────────────────────
# ip -> (正確答案, 過期時間)
_captcha_store: dict[str, tuple[int, float]] = {}

# ── 垃圾留言過濾 ───────────────────────────────────────────────────
def _is_spam(text: str) -> bool:
    if re.search(r"(.)\1{6,}", text):          # 連續重複字元 7 次以上
        return True
    ascii_alpha = [c for c in text if c.isascii() and c.isalpha()]
    if len(ascii_alpha) > 8 and sum(c.isupper() for c in ascii_alpha) / len(ascii_alpha) > 0.7:
        return True                            # 全大寫英文超過 70%
    return False

# ── 國碼對照 ───────────────────────────────────────────────────────
COUNTRY_MAP = {
    "JP": "Japan",
    "TW": "Taiwan",
    "KR": "Korea",
    "US": "United States",
    "CA": "Canada",
}

def _kstr(code: str, name: str) -> str:
    return f"{code.upper()}|||{unquote(name)}"

def _resolve_country_block(code: str, data: dict):
    cu = code.upper()
    name = COUNTRY_MAP.get(cu)
    if name and name in data:
        return cu, name, data[name]
    if cu in data:
        return cu, cu, data[cu]
    return cu, None, None

# ── 評分輔助 ───────────────────────────────────────────────────────
def _rater_key(u: User | None) -> str:
    return f"user:{u.id}" if u else f"ip:{request.remote_addr or 'unknown'}"

def _rating_stats(key: str) -> dict:
    vals = list((ratings_store.get(key) or {}).get("user_ratings", {}).values())
    if not vals:
        return {"avg": 0.0, "count": 0}
    return {"avg": round(sum(vals) / len(vals), 1), "count": len(vals)}

# ═══════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════

# ── 健康 & 開發 ────────────────────────────────────────────────────
@app.route("/api/ping")
def ping():
    return jsonify({"ok": True, "ts": int(time())})

@app.route("/api/_reload", methods=["POST"])
def force_reload():
    _load_foods_json(force=True)
    return jsonify({"reloaded": True})

# ── 認證 ───────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    body         = request.get_json(silent=True) or {}
    email        = (body.get("email") or "").strip().lower()
    password     = (body.get("password") or "")
    display_name = (body.get("display_name") or "").strip()
    if not email or not password or not display_name:
        return jsonify({"error": "請填寫所有欄位"}), 400
    if len(password) < 6:
        return jsonify({"error": "密碼至少需要 6 個字元"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "此 Email 已被使用"}), 409
    u = User(email=email, password_hash=generate_password_hash(password),
             display_name=display_name)
    db.session.add(u)
    db.session.commit()
    return jsonify({"token": _make_token(u.id), "user": u.to_dict()}), 201

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    body     = request.get_json(silent=True) or {}
    email    = (body.get("email") or "").strip().lower()
    password = (body.get("password") or "")
    u = User.query.filter_by(email=email).first()
    if not u or not check_password_hash(u.password_hash, password):
        return jsonify({"error": "帳號或密碼錯誤"}), 401
    return jsonify({"token": _make_token(u.id), "user": u.to_dict()})

@app.route("/api/auth/me")
def auth_me():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    return jsonify({"user": u.to_dict()})

@app.route("/api/auth/profile", methods=["PUT"])
def auth_profile():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    body         = request.get_json(silent=True) or {}
    display_name = (body.get("display_name") or "").strip()
    if display_name:
        if len(display_name) > 30:
            return jsonify({"error": "名稱最長 30 個字"}), 400
        u.display_name = display_name
    current_pw = body.get("current_password", "")
    new_pw     = body.get("new_password", "")
    if current_pw or new_pw:
        if not check_password_hash(u.password_hash, current_pw):
            return jsonify({"error": "目前密碼不正確"}), 400
        if len(new_pw) < 6:
            return jsonify({"error": "新密碼至少需要 6 個字元"}), 400
        u.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return jsonify({"user": u.to_dict()})

@app.route("/api/auth/my-comments")
def auth_my_comments():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    results = []
    for key, lst in comments_store.items():
        parts = key.split("|||", 1)
        if len(parts) != 2:
            continue
        code, food_name = parts
        for c in lst:
            if c.get("user_id") == u.id:
                results.append({
                    "id":           c["id"],
                    "country_code": code,
                    "food_name":    food_name,
                    "text":         c["text"],
                    "ts":           c["ts"],
                })
    results.sort(key=lambda x: x["ts"], reverse=True)
    return jsonify({"comments": results})

# ── 收藏 ───────────────────────────────────────────────────────────
@app.route("/api/favorites")
def get_favorites():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    return jsonify({"favorites": [f.to_dict() for f in Favorite.query.filter_by(user_id=u.id)]})

@app.route("/api/favorites", methods=["POST"])
def add_favorite():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    body = request.get_json(silent=True) or {}
    code = (body.get("country_code") or "").upper().strip()
    name = (body.get("food_name") or "").strip()
    if not code or not name:
        return jsonify({"error": "country_code 和 food_name 為必填"}), 400
    if Favorite.query.filter_by(user_id=u.id, country_code=code, food_name=name).first():
        return jsonify({"error": "已收藏"}), 409
    fav = Favorite(user_id=u.id, country_code=code, food_name=name)
    db.session.add(fav)
    db.session.commit()
    return jsonify(fav.to_dict()), 201

@app.route("/api/favorites", methods=["DELETE"])
def remove_favorite():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    body = request.get_json(silent=True) or {}
    code = (body.get("country_code") or "").upper().strip()
    name = (body.get("food_name") or "").strip()
    fav  = Favorite.query.filter_by(user_id=u.id, country_code=code, food_name=name).first()
    if not fav:
        return jsonify({"error": "未找到"}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/favorites/batch", methods=["POST"])
def batch_favorites():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    items = (request.get_json(silent=True) or {}).get("items", [])
    added = 0
    for item in items:
        code = (item.get("country_code") or "").upper().strip()
        name = (item.get("food_name") or "").strip()
        if code and name and not Favorite.query.filter_by(
                user_id=u.id, country_code=code, food_name=name).first():
            db.session.add(Favorite(user_id=u.id, country_code=code, food_name=name))
            added += 1
    db.session.commit()
    return jsonify({"added": added})

@app.route("/api/favorites/move", methods=["PUT"])
def move_favorite():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    body    = request.get_json(silent=True) or {}
    fav_id  = body.get("favorite_id")
    list_id = body.get("list_id")
    fav = Favorite.query.filter_by(id=fav_id, user_id=u.id).first()
    if not fav:
        return jsonify({"error": "未找到"}), 404
    if list_id is not None:
        if not FavoriteList.query.filter_by(id=list_id, user_id=u.id).first():
            return jsonify({"error": "清單不存在"}), 404
    fav.list_id = list_id
    db.session.commit()
    return jsonify(fav.to_dict())

# ── 收藏清單 ───────────────────────────────────────────────────────
@app.route("/api/favorite-lists")
def get_fav_lists():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    lists = FavoriteList.query.filter_by(user_id=u.id).all()
    return jsonify({"lists": [{"id": l.id, "name": l.name} for l in lists]})

@app.route("/api/favorite-lists", methods=["POST"])
def create_fav_list():
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    name = ((request.get_json(silent=True) or {}).get("name") or "").strip()
    if not name:
        return jsonify({"error": "name 為必填"}), 400
    fl = FavoriteList(user_id=u.id, name=name)
    db.session.add(fl)
    db.session.commit()
    return jsonify({"id": fl.id, "name": fl.name}), 201

@app.route("/api/favorite-lists/<int:list_id>", methods=["PUT"])
def rename_fav_list(list_id):
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    fl = FavoriteList.query.filter_by(id=list_id, user_id=u.id).first()
    if not fl:
        return jsonify({"error": "未找到"}), 404
    name = ((request.get_json(silent=True) or {}).get("name") or "").strip()
    if not name:
        return jsonify({"error": "name 為必填"}), 400
    fl.name = name
    db.session.commit()
    return jsonify({"id": fl.id, "name": fl.name})

@app.route("/api/favorite-lists/<int:list_id>", methods=["DELETE"])
def delete_fav_list(list_id):
    u = _current_user()
    if not u:
        return jsonify({"error": "未授權"}), 401
    fl = FavoriteList.query.filter_by(id=list_id, user_id=u.id).first()
    if not fl:
        return jsonify({"error": "未找到"}), 404
    Favorite.query.filter_by(user_id=u.id, list_id=list_id).update({"list_id": None})
    db.session.delete(fl)
    db.session.commit()
    return jsonify({"ok": True})

# ── 料理清單 & 詳情 ────────────────────────────────────────────────
@app.route("/api/foods/<code>")
def get_country_foods(code):
    data = _load_foods_json()
    code_up, country_name, block = _resolve_country_block(code, data)
    if not country_name:
        return jsonify({"error": "Country not found"}), 404
    enriched = []
    for f in block.get("foods", []):
        fname = f.get("name", "")
        key   = _kstr(code_up, fname)
        stats = _rating_stats(key)
        enriched.append({
            "name":         fname,
            "img":          f.get("img"),
            "likes":        int(likes_store.get(key, 0)),
            "tags":         f.get("tags", []),
            "avg_rating":   stats["avg"],
            "rating_count": stats["count"],
        })
    enriched.sort(key=lambda x: x["likes"], reverse=True)
    return jsonify({"foods": enriched})

@app.route("/api/food/<code>/<name>")
def get_food_detail(code, name):
    data = _load_foods_json()
    code_up, country_name, block = _resolve_country_block(code, data)
    if not country_name:
        return jsonify({"error": "Country not found"}), 404
    target = unquote(name).strip()
    for f in block.get("foods", []):
        if f.get("name") == target:
            return jsonify(f)
    return jsonify({"error": "Food not found"}), 404

# ── 按讚 ───────────────────────────────────────────────────────────
@app.route("/api/food/<code>/<name>/likes")
def get_likes(code, name):
    key = _kstr(code, name)
    return jsonify({"likes": int(likes_store.get(key, 0))})

@app.route("/api/food/<code>/<name>/like", methods=["POST"])
def post_like(code, name):
    key = _kstr(code, name)
    ok, retry = _rate_ok("like", key)
    if not ok:
        return jsonify({"error": "操作太頻繁，請稍後再試",
                        "retry_after": retry,
                        "likes": int(likes_store.get(key, 0))}), 429
    likes_store[key] = int(likes_store.get(key, 0)) + 1
    _save_json(LIKES_JSON, likes_store)
    return jsonify({"likes": likes_store[key]})

# ── 評分（1-5 星） ─────────────────────────────────────────────────
@app.route("/api/food/<code>/<name>/rating")
def get_rating(code, name):
    key       = _kstr(code, name)
    u         = _current_user()
    rk        = _rater_key(u)
    entry     = ratings_store.get(key) or {}
    ur        = entry.get("user_ratings", {})
    stats     = _rating_stats(key)
    stats["my_rating"] = ur.get(rk, 0)
    return jsonify(stats)

@app.route("/api/food/<code>/<name>/rate", methods=["POST"])
def post_rating(code, name):
    key = _kstr(code, name)
    try:
        stars = int((request.get_json(silent=True) or {}).get("rating", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "rating 需為 1-5 的整數"}), 400
    if not (1 <= stars <= 5):
        return jsonify({"error": "rating 需為 1-5 的整數"}), 400
    u  = _current_user()
    rk = _rater_key(u)
    ratings_store.setdefault(key, {"user_ratings": {}})
    ratings_store[key].setdefault("user_ratings", {})[rk] = stars
    _save_json(RATINGS_JSON, ratings_store)
    stats = _rating_stats(key)
    stats["my_rating"] = stars
    return jsonify(stats)

# ── 留言 ───────────────────────────────────────────────────────────
@app.route("/api/food/<code>/<name>/comments")
def get_comments(code, name):
    key = _kstr(code, name)
    lst = sorted(comments_store.get(key, []), key=lambda x: x.get("id", 0), reverse=True)
    return jsonify({"comments": lst})

@app.route("/api/food/<code>/<name>/comments", methods=["POST"])
def post_comment(code, name):
    key  = _kstr(code, name)
    u    = _current_user()
    anon = u is None

    # 速率限制
    if anon:
        ok, retry = _rate_ok("comment_anon", key)
    else:
        ok, retry = _rate_ok("comment_auth", f"{key}:u{u.id}")
    if not ok:
        return jsonify({"error": f"留言太頻繁，請等待 {retry} 秒後再試",
                        "retry_after": retry}), 429

    body = request.get_json(silent=True) or {}

    # 匿名用戶驗證碼檢查
    if anon:
        ip    = request.remote_addr or "unknown"
        entry = _captcha_store.get(ip)
        if not entry:
            return jsonify({"error": "請先取得驗證碼", "need_captcha": True}), 400
        expected, expires = entry
        if time() > expires:
            _captcha_store.pop(ip, None)
            return jsonify({"error": "驗證碼已過期，請重新取得", "need_captcha": True}), 400
        try:
            given = int(body.get("captcha_answer", -999))
        except (ValueError, TypeError):
            given = -999
        if given != expected:
            return jsonify({"error": "驗證碼錯誤"}), 400
        _captcha_store.pop(ip, None)   # 一次性

    display_name = u.display_name if u else (body.get("user") or "匿名").strip()[:30]
    text = (body.get("text") or "").strip()[:300]

    if not text:
        return jsonify({"error": "text is required"}), 400
    if len(text) < 2:
        return jsonify({"error": "留言至少需要 2 個字"}), 400
    if _is_spam(text):
        return jsonify({"error": "留言內容不符合規範"}), 400

    item: dict = {
        "id":      int(time() * 1000),
        "user":    display_name,
        "text":    text,
        "ts":      int(time()),
        "likes":   0,
        "user_id": u.id if u else None,
    }
    if anon:
        item["delete_token"] = secrets.token_hex(16)

    comments_store.setdefault(key, []).append(item)
    _save_json(COMMENTS_JSON, comments_store)
    return jsonify(item), 201

@app.route("/api/food/<code>/<name>/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(code, name, comment_id):
    key = _kstr(code, name)
    lst = comments_store.get(key, [])
    idx = next((i for i, c in enumerate(lst) if c.get("id") == comment_id), None)
    if idx is None:
        return jsonify({"error": "留言不存在"}), 404
    comment = lst[idx]
    u = _current_user()
    if u and comment.get("user_id") == u.id:
        pass  # 本人刪除
    else:
        token = (request.get_json(silent=True) or {}).get("token", "")
        if not token or token != comment.get("delete_token"):
            return jsonify({"error": "無權刪除"}), 403
    lst.pop(idx)
    _save_json(COMMENTS_JSON, comments_store)
    return jsonify({"ok": True})

@app.route("/api/food/<code>/<name>/comments/<int:comment_id>/like", methods=["POST"])
def like_comment(code, name, comment_id):
    key = _kstr(code, name)
    ok, retry = _rate_ok("comment_like", f"{key}:{comment_id}")
    if not ok:
        return jsonify({"error": "操作太頻繁", "retry_after": retry}), 429
    for c in comments_store.get(key, []):
        if c.get("id") == comment_id:
            c["likes"] = c.get("likes", 0) + 1
            _save_json(COMMENTS_JSON, comments_store)
            return jsonify({"likes": c["likes"]})
    return jsonify({"error": "留言不存在"}), 404

# ── 驗證碼 ─────────────────────────────────────────────────────────
@app.route("/api/captcha")
def get_captcha():
    ip   = request.remote_addr or "unknown"
    a, b = random.randint(1, 9), random.randint(1, 9)
    _captcha_store[ip] = (a + b, time() + 120)
    return jsonify({"question": f"{a} + {b} = ?", "expires_in": 120})

# ── 搜尋 ───────────────────────────────────────────────────────────
@app.route("/api/search")
def search():
    q              = (request.args.get("q") or "").strip().lower()
    filter_country = (request.args.get("country") or "").upper().strip()
    try:
        min_rating = float(request.args.get("min_rating", 0))
    except ValueError:
        min_rating = 0.0
    sort_by = request.args.get("sort", "likes")   # likes | rating | name

    data    = _load_foods_json()
    results = []

    for code, country_name in COUNTRY_MAP.items():
        if filter_country and filter_country != code:
            continue
        block = data.get(country_name) or data.get(code)
        if not block:
            continue
        for f in block.get("foods", []):
            fname = f.get("name", "")
            fdesc = f.get("desc", "")
            ftags = f.get("tags", [])
            if q and not any([
                q in fname.lower(),
                q in fdesc.lower(),
                any(q in t.lower() for t in ftags),
            ]):
                continue
            key   = _kstr(code, fname)
            likes = int(likes_store.get(key, 0))
            stats = _rating_stats(key)
            if min_rating > 0 and stats["avg"] < min_rating:
                continue
            results.append({
                "code":         code,
                "countryName":  country_name,
                "name":         fname,
                "img":          f.get("img"),
                "tags":         ftags,
                "likes":        likes,
                "avg_rating":   stats["avg"],
                "rating_count": stats["count"],
            })

    if sort_by == "rating":
        results.sort(key=lambda x: (-x["avg_rating"], -x["likes"]))
    elif sort_by == "name":
        results.sort(key=lambda x: x["name"])
    else:
        results.sort(key=lambda x: (-x["likes"], -x["avg_rating"]))

    return jsonify({"results": results})

# ── 標籤 ───────────────────────────────────────────────────────────
@app.route("/api/tags")
def get_tags():
    data = _load_foods_json()
    tags: set = set()
    for country_name in COUNTRY_MAP.values():
        block = data.get(country_name) or {}
        for f in block.get("foods", []):
            tags.update(f.get("tags", []))
    return jsonify({"tags": sorted(tags)})

# ── 熱門美食 ───────────────────────────────────────────────────────
@app.route("/api/top-foods")
def get_top_foods():
    data  = _load_foods_json()
    items = []
    for code, country_name in COUNTRY_MAP.items():
        block = data.get(country_name) or data.get(code)
        if not block:
            continue
        for f in block.get("foods", []):
            fname = f.get("name")
            if not fname:
                continue
            key   = _kstr(code, fname)
            likes = int(likes_store.get(key, 0))
            stats = _rating_stats(key)
            score = likes + (stats["avg"] * stats["count"] * 1.5)
            if likes <= 0 and stats["count"] == 0:
                continue
            items.append({
                "code":         code,
                "countryName":  country_name,
                "name":         fname,
                "img":          f.get("img"),
                "likes":        likes,
                "avg_rating":   stats["avg"],
                "rating_count": stats["count"],
                "score":        round(score, 2),
            })
    items.sort(key=lambda x: (-x["score"], -x["likes"]))
    try:
        limit = max(1, int(request.args.get("limit", 5)))
    except ValueError:
        limit = 5
    return jsonify({"foods": items[:limit]})

# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")
    app.run(host="127.0.0.1", port=5000, debug=debug)
