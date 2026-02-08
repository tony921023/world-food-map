from __future__ import annotations
import os, json, tempfile, threading
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

FOODS_JSON     = DATA_DIR / "foods.json"      # 主資料（國家/料理/圖片/描述）
LIKES_JSON     = DATA_DIR / "likes.json"      # 讚數持久化
COMMENTS_JSON  = DATA_DIR / "comments.json"   # 留言持久化

# ---------------- Flask ----------------
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['JSON_AS_ASCII'] = False
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ---------------- 共用工具 ----------------
def _atomic_write(path: Path, obj):
    # 安全寫檔，避免中途中斷壞檔
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        json.dump(obj, tmp, ensure_ascii=False, separators=(",", ":"))
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name
    os.replace(tmp_path, path)

_lock = threading.Lock()

def _save_json(path: Path, obj):
    with _lock:
        _atomic_write(path, obj)

def _load_json(path: Path, default):
    """容錯讀檔：不存在、空白或壞檔一律回預設並自動修復"""
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

# ---------------- foods.json：快取 + 自動重載（含容錯） ----------------
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

# 啟動時讀進記憶體（容錯）
likes_store    = _load_json(LIKES_JSON, {})       # {"JP|||壽司": 12, ...}
comments_store = _load_json(COMMENTS_JSON, {})    # {"JP|||壽司": [ {...}, ... ]}

# ---------------- 國碼對照 ----------------
# 左邊：API 使用的 code；右邊：foods.json 內可能使用的「國家名稱」
COUNTRY_MAP = {
    "JP": "Japan",
    "TW": "Taiwan",
    "KR": "Korea",
    "US": "United States",
    "CA": "Canada",
}

def _kstr(code: str, name: str) -> str:
    # 把 (code,name) 轉成 JSON key
    return f"{code.upper()}|||{unquote(name)}"

def _resolve_country_block(code: str, data: dict):
    """
    根據 code 從 foods.json 找到對應區塊。
    先用 COUNTRY_MAP[code] 當 key，找不到再用 code 本身當 key。
    回傳 (code_upper, country_name, block or None)
    """
    cu = code.upper()
    # 1) 先用 map 的名稱找（例如 "United States"）
    name_from_map = COUNTRY_MAP.get(cu)
    if name_from_map and name_from_map in data:
        return cu, name_from_map, data[name_from_map]
    # 2) 再用 code 當 key 找（例如 "US"）
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
    """
    回傳該國料理清單，並依讚數由高到低排序。
    回傳欄位與舊版相容：name / img（另外加 likes 讓前端可顯示徽章）
    """
    data = _load_foods_json()
    code_up, country_name, country_block = _resolve_country_block(code, data)
    if not country_name or not country_block:
        return jsonify({"error": "Country not found"}), 404

    foods = country_block.get("foods", [])

    # 把讚數併進清單並排序（高→低；同讚數保持原列順）
    enriched = []
    for f in foods:
        fname = f.get("name", "")
        key = _kstr(code_up, fname)
        likes = int(likes_store.get(key, 0))
        enriched.append({
            "name": fname,
            "img": f.get("img"),
            "likes": likes
        })
    enriched.sort(key=lambda x: x["likes"], reverse=True)

    return jsonify({"foods": enriched})

@app.route('/api/food/<code>/<name>')
def get_food_detail(code, name):
    """回傳該料理完整資料（含 desc/…）"""
    data = _load_foods_json()
    code_up, country_name, country_block = _resolve_country_block(code, data)
    if not country_name or not country_block:
        return jsonify({"error": "Country not found"}), 404

    target = unquote(name).strip()
    for f in country_block.get("foods", []):
        if f.get("name") == target:
            return jsonify(f)
    return jsonify({"error": "Food not found"}), 404

# ====== Likes ======
@app.route('/api/food/<code>/<name>/likes', methods=['GET'])
def get_likes(code, name):
    key = _kstr(code, name)
    return jsonify({"likes": int(likes_store.get(key, 0))})

@app.route('/api/food/<code>/<name>/like', methods=['POST'])
def post_like(code, name):
    key = _kstr(code, name)
    likes_store[key] = int(likes_store.get(key, 0)) + 1
    _save_json(LIKES_JSON, likes_store)        # 寫回 JSON
    return jsonify({"likes": likes_store[key]})

# ====== Comments ======
@app.route('/api/food/<code>/<name>/comments', methods=['GET'])
def get_comments(code, name):
    key = _kstr(code, name)
    lst = comments_store.get(key, [])
    # 依時間新→舊
    lst_sorted = sorted(lst, key=lambda x: x.get("id", 0), reverse=True)
    return jsonify({"comments": lst_sorted})

@app.route('/api/food/<code>/<name>/comments', methods=['POST'])
def post_comment(code, name):
    key = _kstr(code, name)
    body = request.get_json(silent=True) or {}
    user = (body.get("user") or "匿名").strip()[:30]
    text = (body.get("text") or "").strip()[:500]
    if not text:
        return jsonify({"error": "text is required"}), 400

    item = {
        "id": int(time() * 1000),     # 前端可拿來排序
        "user": user,
        "text": text,
        "ts": int(time())
    }
    comments_store.setdefault(key, []).append(item)
    _save_json(COMMENTS_JSON, comments_store)   # 寫回 JSON
    return jsonify(item), 201

# ====== TOP 5 人氣美食（依讚數） ======
@app.route('/api/top-foods')
def get_top_foods():
    """
    回傳全站「人氣美食 TOP N」。
    目前先用 likes 當 score，之後如果有 rating，可以在這裡一起加權。

    回傳格式：
    {
      "foods": [
        {
          "code": "TW",
          "countryName": "Taiwan",
          "name": "牛肉麵",
          "img": "/static/foods/beef.jpg",
          "likes": 10,
          "score": 10.0
        },
        ...
      ]
    }
    """
    data = _load_foods_json()
    items = []

    for code, country_name in COUNTRY_MAP.items():
        # 支援兩種寫法：用名稱當 key 或直接用國碼當 key
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

            # 如果完全沒人按讚，可以選擇略過
            if likes <= 0:
                continue

            # 目前先直接用 likes 當作人氣 score
            score = float(likes)

            items.append({
                "code": code,
                "countryName": country_name,
                "name": name,
                "img": img,
                "likes": likes,
                "score": score
            })

    # 依 score 由大到小排序，同分再看 likes
    items.sort(key=lambda x: (-x["score"], -x["likes"], x["countryName"], x["name"]))

    # 可用 query string 自訂 limit，預設 5
    try:
        limit = int(request.args.get("limit", 5))
    except ValueError:
        limit = 5
    if limit <= 0:
        limit = 5

    return jsonify({"foods": items[:limit]})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
