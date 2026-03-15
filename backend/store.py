from __future__ import annotations
import json, os, tempfile, threading
from json import JSONDecodeError
from pathlib import Path
from config import FOODS_JSON, LIKES_JSON, COMMENTS_JSON, RATINGS_JSON

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


def save_json(path: Path, obj):
    with _lock:
        _atomic_write(path, obj)


def load_json(path: Path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            save_json(path, default)
            return default
        return json.loads(raw)
    except FileNotFoundError:
        save_json(path, default)
        return default
    except JSONDecodeError:
        save_json(path, default)
        return default


_foods_cache: dict = {"mtime": None, "data": {}}


def load_foods_json(force: bool = False) -> dict:
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


likes_store    = load_json(LIKES_JSON,    {})
comments_store = load_json(COMMENTS_JSON, {})
ratings_store  = load_json(RATINGS_JSON,  {})
