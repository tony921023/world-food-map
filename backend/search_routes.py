from flask import Blueprint, request, jsonify
from store import load_foods_json
from config import COUNTRY_MAP
from helpers import kstr, like_count, rating_stats

search_bp = Blueprint("search", __name__)


@search_bp.route("/api/search")
def search():
    q              = (request.args.get("q") or "").strip().lower()
    filter_country = (request.args.get("country") or "").upper().strip()
    filter_tag     = (request.args.get("tag") or "").strip()
    try:
        min_rating = float(request.args.get("min_rating", 0))
    except ValueError:
        min_rating = 0.0
    sort_by = request.args.get("sort", "likes")

    data    = load_foods_json()
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
            if filter_tag and filter_tag not in ftags:
                continue
            if q and not any([
                q in fname.lower(),
                q in fdesc.lower(),
                any(q in t.lower() for t in ftags),
            ]):
                continue
            key   = kstr(code, fname)
            likes = like_count(key)
            stats = rating_stats(key)
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


@search_bp.route("/api/tags")
def get_tags():
    data = load_foods_json()
    tags: set = set()
    for country_name in COUNTRY_MAP.values():
        block = data.get(country_name) or {}
        for f in block.get("foods", []):
            tags.update(f.get("tags", []))
    return jsonify({"tags": sorted(tags)})


@search_bp.route("/api/top-foods")
def get_top_foods():
    data  = load_foods_json()
    items = []
    for code, country_name in COUNTRY_MAP.items():
        block = data.get(country_name) or data.get(code)
        if not block:
            continue
        for f in block.get("foods", []):
            fname = f.get("name")
            if not fname:
                continue
            key   = kstr(code, fname)
            likes = like_count(key)
            stats = rating_stats(key)
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
