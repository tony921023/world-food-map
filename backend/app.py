from __future__ import annotations
import os, json, tempfile, threading, secrets, hashlib
from collections import defaultdict
from pathlib import Path
from time import time
from urllib.parse import unquote
from json import JSONDecodeError
from flask import Flask, jsonify, request
from flask_cors import CORS

# ---------------- 路徑設定 ----------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FOODS_JSON          = DATA_DIR / "foods.json"
LIKES_JSON          = DATA_DIR / "likes.json"
COMMENTS_JSON       = DATA_DIR / "comments.json"
COMMENT_LIKES_JSON  = DATA_DIR / "comment_likes.json"

# ---------------- Flask ----------------
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['JSON_AS_ASCII'] = False
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ---------------- 共用工具 ----------------
def _atomic_write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8",
                                     dir=str(path.parent)) as tmp:
        json.dump(obj, tmp, ensure_ascii=False, separators=(",", ":"))
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name
    os.replace(tmp_path, path)

_lock = threading.Lock()

def _save_json(path: Path, obj):
    with _lock:
        _atomic_write(path, obj)

# ---------------- 簡易 IP 限速 ----------------
_rate_ts: dict[str, float] = defaultdict(float)
_RATE_WINDOW = {
    "like": 2,
    "comment": 5,
    "comment_like": 2,
}

def _rate_ok(action: str, extra: str = "") -> bool:
    ip = request.remote_addr or "unknown"
    key = f"{action}:{ip}:{extra}"
    now = time()
    window = _RATE_WINDOW.get(action, 2)
    if now - _rate_ts[key] < window:
        return False
    _rate_ts[key] = now
    return True

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

# ---------------- 敏感詞過濾 ----------------
_BLOCKED_WORDS = [
    "幹", "靠北", "媽的", "他媽", "垃圾", "白癡", "廢物", "去死",
    "fuck", "shit", "damn", "bitch", "asshole", "dick", "pussy",
]

def _content_ok(text: str) -> bool:
    lower = text.lower()
    for w in _BLOCKED_WORDS:
        if w.lower() in lower:
            return False
    return True

# ---------------- foods.json：快取 + 自動重載 ----------------
_foods_cache = {"mtime": None, "data": {}}
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

# 啟動時讀進記憶體
likes_store          = _load_json(LIKES_JSON, {})
comments_store       = _load_json(COMMENTS_JSON, {})
comment_likes_store  = _load_json(COMMENT_LIKES_JSON, {})

# ---------------- 國碼對照 ----------------
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
    name_from_map = COUNTRY_MAP.get(cu)
    if name_from_map and name_from_map in data:
        return cu, name_from_map, data[name_from_map]
    if cu in data:
        return cu, cu, data[cu]
    return cu, None, None

# ---------------- 健康檢查 & 開發工具 ----------------
@app.route('/api/ping')
def ping():
    return jsonify({"ok": True, "ts": int(time())})

@app.route('/api/_reload', methods=['POST'])
def force_reload():
    _load_foods_json(force=True)
    return jsonify({"reloaded": True, "ts": int(time())})

# ---------------- 業務 API ----------------
@app.route('/api/foods/<code>')
def get_country_foods(code):
    data = _load_foods_json()
    code_up, country_name, country_block = _resolve_country_block(code, data)
    if not country_name or not country_block:
        return jsonify({"error": "Country not found"}), 404

    foods = country_block.get("foods", [])

    enriched = []
    for f in foods:
        fname = f.get("name", "")
        key = _kstr(code_up, fname)
        likes = int(likes_store.get(key, 0))
        enriched.append({
            "name": fname,
            "img": f.get("img"),
            "likes": likes,
            "tags": f.get("tags", []),
        })
    enriched.sort(key=lambda x: x["likes"], reverse=True)

    return jsonify({"foods": enriched})

@app.route('/api/food/<code>/<name>')
def get_food_detail(code, name):
    data = _load_foods_json()
    code_up, country_name, country_block = _resolve_country_block(code, data)
    if not country_name or not country_block:
        return jsonify({"error": "Country not found"}), 404

    target = unquote(name).strip()
    for f in country_block.get("foods", []):
        if f.get("name") == target:
            return jsonify(f)
    return jsonify({"error": "Food not found"}), 404

# ====== Tags ======
@app.route('/api/tags')
def get_all_tags():
    data = _load_foods_json()
    tag_set = set()
    for country_block in data.values():
        for f in country_block.get("foods", []):
            for t in f.get("tags", []):
                tag_set.add(t)
    return jsonify({"tags": sorted(tag_set)})

# ====== Search ======
@app.route('/api/search')
def search_foods():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"results": []})

    data = _load_foods_json()
    results = []

    for code, country_name in COUNTRY_MAP.items():
        country_block = data.get(country_name) or data.get(code)
        if not country_block:
            continue

        for f in country_block.get("foods", []):
            fname = f.get("name", "")
            tags = f.get("tags", [])
            desc = f.get("desc", "")

            # Scoring: exact name match > name contains > tag/desc contains
            score = 0
            if fname == q:
                score = 100
            elif q in fname:
                score = 50
            elif any(q in t for t in tags):
                score = 30
            elif q in desc:
                score = 10

            if score > 0:
                results.append({
                    "code": code,
                    "countryName": country_name,
                    "name": fname,
                    "img": f.get("img"),
                    "tags": tags,
                    "_score": score,
                })

    results.sort(key=lambda x: -x["_score"])
    # Strip internal score
    for r in results:
        del r["_score"]

    return jsonify({"results": results})

# ====== Likes ======
@app.route('/api/food/<code>/<name>/likes', methods=['GET'])
def get_likes(code, name):
    key = _kstr(code, name)
    return jsonify({"likes": int(likes_store.get(key, 0))})

@app.route('/api/food/<code>/<name>/like', methods=['POST'])
def post_like(code, name):
    key = _kstr(code, name)
    if not _rate_ok("like", key):
        return jsonify({"error": "操作太頻繁，請稍後再試", "likes": int(likes_store.get(key, 0))}), 429
    likes_store[key] = int(likes_store.get(key, 0)) + 1
    _save_json(LIKES_JSON, likes_store)
    return jsonify({"likes": likes_store[key]})

# ====== Comments ======
@app.route('/api/food/<code>/<name>/comments', methods=['GET'])
def get_comments(code, name):
    key = _kstr(code, name)
    lst = comments_store.get(key, [])
    lst_sorted = sorted(lst, key=lambda x: x.get("id", 0), reverse=True)
    # Strip token_hash and attach likes count
    safe = []
    for c in lst_sorted:
        item = {k: v for k, v in c.items() if k != "token_hash"}
        cid = str(c.get("id", ""))
        item["likes"] = int(comment_likes_store.get(cid, 0))
        safe.append(item)
    return jsonify({"comments": safe})

@app.route('/api/food/<code>/<name>/comments', methods=['POST'])
def post_comment(code, name):
    key = _kstr(code, name)
    if not _rate_ok("comment", key):
        return jsonify({"error": "留言太頻繁，請稍後再試"}), 429

    body = request.get_json(silent=True) or {}
    user = (body.get("user") or "匿名").strip()[:30]
    text = (body.get("text") or "").strip()[:500]
    if not text:
        return jsonify({"error": "text is required"}), 400
    if len(text) < 2:
        return jsonify({"error": "留言至少需要 2 個字"}), 400

    if not _content_ok(text) or not _content_ok(user):
        return jsonify({"error": "留言包含不當內容，請修改後重試"}), 400

    # Generate delete token
    delete_token = secrets.token_urlsafe(16)
    token_hash = hashlib.sha256(delete_token.encode()).hexdigest()

    item = {
        "id": int(time() * 1000),
        "user": user,
        "text": text,
        "ts": int(time()),
        "token_hash": token_hash,
    }
    comments_store.setdefault(key, []).append(item)
    _save_json(COMMENTS_JSON, comments_store)

    # Return item without token_hash, but with delete_token (one-time)
    resp = {k: v for k, v in item.items() if k != "token_hash"}
    resp["delete_token"] = delete_token
    resp["likes"] = 0
    return jsonify(resp), 201

# ====== Delete Comment ======
@app.route('/api/food/<code>/<name>/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(code, name, comment_id):
    key = _kstr(code, name)
    body = request.get_json(silent=True) or {}
    token = (body.get("token") or "").strip()
    if not token:
        return jsonify({"error": "需要提供 delete token"}), 400

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    lst = comments_store.get(key, [])
    for i, c in enumerate(lst):
        if c.get("id") == comment_id:
            if c.get("token_hash") != token_hash:
                return jsonify({"error": "token 不正確，無法刪除"}), 403
            lst.pop(i)
            _save_json(COMMENTS_JSON, comments_store)
            return jsonify({"ok": True})
    return jsonify({"error": "留言不存在"}), 404

# ====== Comment Like ======
@app.route('/api/food/<code>/<name>/comments/<int:comment_id>/like', methods=['POST'])
def like_comment(code, name, comment_id):
    cid = str(comment_id)
    if not _rate_ok("comment_like", cid):
        return jsonify({"error": "操作太頻繁", "likes": int(comment_likes_store.get(cid, 0))}), 429
    comment_likes_store[cid] = int(comment_likes_store.get(cid, 0)) + 1
    _save_json(COMMENT_LIKES_JSON, comment_likes_store)
    return jsonify({"likes": comment_likes_store[cid]})

# ====== TOP 5 人氣美食（依讚數） ======
@app.route('/api/top-foods')
def get_top_foods():
    data = _load_foods_json()
    items = []

    for code, country_name in COUNTRY_MAP.items():
        country_block = data.get(country_name) or data.get(code)
        if not country_block:
            continue

        foods = country_block.get("foods", [])
        for f in foods:
            name = f.get("name")
            if not name:
                continue
            img = f.get("img")
            key = _kstr(code, name)
            likes = int(likes_store.get(key, 0))

            if likes <= 0:
                continue

            score = float(likes)

            items.append({
                "code": code,
                "countryName": country_name,
                "name": name,
                "img": img,
                "likes": likes,
                "score": score
            })

    items.sort(key=lambda x: (-x["score"], -x["likes"], x["countryName"], x["name"]))

    try:
        limit = int(request.args.get("limit", 5))
    except ValueError:
        limit = 5
    if limit <= 0:
        limit = 5

    return jsonify({"foods": items[:limit]})

if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")
    app.run(host='127.0.0.1', port=5000, debug=debug)
