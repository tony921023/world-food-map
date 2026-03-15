from flask import Blueprint, request, jsonify
from urllib.parse import unquote
from store import likes_store, ratings_store, save_json, load_foods_json
from config import LIKES_JSON, RATINGS_JSON, COUNTRY_MAP
from helpers import (
    current_user, err,
    kstr, resolve_country_block,
    like_entry, liker_id, like_count,
    rater_key, rating_stats,
)

foods_bp = Blueprint("foods", __name__)


@foods_bp.route("/api/foods/<code>")
def get_country_foods(code):
    data = load_foods_json()
    code_up, country_name, block = resolve_country_block(code, data)
    if not country_name:
        return err("Country not found", 404)
    enriched = []
    for f in block.get("foods", []):
        fname = f.get("name", "")
        key   = kstr(code_up, fname)
        stats = rating_stats(key)
        enriched.append({
            "name":         fname,
            "img":          f.get("img"),
            "likes":        like_count(key),
            "tags":         f.get("tags", []),
            "avg_rating":   stats["avg"],
            "rating_count": stats["count"],
        })
    enriched.sort(key=lambda x: x["likes"], reverse=True)
    return jsonify({"foods": enriched})


@foods_bp.route("/api/food/<code>/<name>")
def get_food_detail(code, name):
    data = load_foods_json()
    code_up, country_name, block = resolve_country_block(code, data)
    if not country_name:
        return err("Country not found", 404)
    target = unquote(name).strip()
    for f in block.get("foods", []):
        if f.get("name") == target:
            return jsonify(f)
    return err("Food not found", 404)


@foods_bp.route("/api/food/<code>/<name>/likes")
def get_likes(code, name):
    key   = kstr(code, name)
    entry = like_entry(key)
    u     = current_user()
    liked = liker_id(u) in entry.get("liked_by", [])
    return jsonify({"likes": int(entry.get("count", 0)), "liked": liked})


@foods_bp.route("/api/food/<code>/<name>/like", methods=["POST"])
def post_like(code, name):
    key      = kstr(code, name)
    u        = current_user()
    lk       = liker_id(u)
    entry    = like_entry(key)
    liked_by = list(entry.get("liked_by", []))
    count    = int(entry.get("count", 0))
    if lk in liked_by:
        liked_by.remove(lk)
        count = max(0, count - 1)
        liked = False
    else:
        liked_by.append(lk)
        count += 1
        liked = True
    likes_store[key] = {"count": count, "liked_by": liked_by}
    save_json(LIKES_JSON, likes_store)
    return jsonify({"likes": count, "liked": liked})


@foods_bp.route("/api/food/<code>/<name>/rating")
def get_rating(code, name):
    key   = kstr(code, name)
    u     = current_user()
    rk    = rater_key(u)
    entry = ratings_store.get(key) or {}
    ur    = entry.get("user_ratings", {})
    stats = rating_stats(key)
    stats["my_rating"] = ur.get(rk, 0)
    return jsonify(stats)


@foods_bp.route("/api/food/<code>/<name>/rate", methods=["POST"])
def post_rating(code, name):
    key = kstr(code, name)
    try:
        stars = int((request.get_json(silent=True) or {}).get("rating", 0))
    except (ValueError, TypeError):
        return err("rating 需為 1-5 的整數")
    if not (1 <= stars <= 5):
        return err("rating 需為 1-5 的整數")
    u  = current_user()
    rk = rater_key(u)
    ratings_store.setdefault(key, {"user_ratings": {}})
    ratings_store[key].setdefault("user_ratings", {})[rk] = stars
    save_json(RATINGS_JSON, ratings_store)
    stats = rating_stats(key)
    stats["my_rating"] = stars
    return jsonify(stats)


@foods_bp.route("/api/food/<code>/<name>/related")
def get_related_foods(code, name):
    data = load_foods_json()
    code_up, country_name, block = resolve_country_block(code, data)
    target = unquote(name).strip()
    current_tags = set()
    if block:
        for f in block.get("foods", []):
            if f.get("name") == target:
                current_tags = set(f.get("tags", []))
                break
    results = []
    for c, cn in COUNTRY_MAP.items():
        b = data.get(cn) or data.get(c)
        if not b:
            continue
        for f in b.get("foods", []):
            if c == code_up and f.get("name") == target:
                continue
            ftags = set(f.get("tags", []))
            common = len(current_tags & ftags)
            if common == 0 and current_tags:
                continue
            key = kstr(c, f["name"])
            stats = rating_stats(key)
            results.append({
                "code":        c,
                "countryName": cn,
                "name":        f["name"],
                "img":         f.get("img"),
                "tags":        f.get("tags", []),
                "likes":       like_count(key),
                "avg_rating":  stats["avg"],
                "common_tags": common,
            })
    results.sort(key=lambda x: (-x["common_tags"], -x["likes"]))
    return jsonify({"related": results[:4]})
