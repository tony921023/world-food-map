import secrets
from time import time
from flask import Blueprint, request, jsonify
from store import comments_store, save_json
from config import COMMENTS_JSON
from helpers import (
    current_user, err,
    kstr, rate_ok,
    get_captcha, verify_captcha,
    is_spam,
)

comments_bp = Blueprint("comments", __name__)


@comments_bp.route("/api/captcha")
def get_captcha_route():
    ip = request.remote_addr or "unknown"
    return jsonify(get_captcha(ip))


@comments_bp.route("/api/food/<code>/<name>/comments")
def get_comments(code, name):
    key = kstr(code, name)
    all_cmts = comments_store.get(key, [])
    reply_map = {}
    top_level = []
    for c in all_cmts:
        c_out = {k: v for k, v in c.items() if k != "delete_token"}
        c_out.setdefault("replies", [])
        pid = c.get("parent_id")
        if pid:
            reply_map.setdefault(pid, []).append(c_out)
        else:
            top_level.append(c_out)
    for c in top_level:
        c["replies"] = sorted(reply_map.get(c["id"], []), key=lambda x: x.get("id", 0))
    top_level.sort(key=lambda x: x.get("id", 0), reverse=True)
    return jsonify({"comments": top_level})


@comments_bp.route("/api/food/<code>/<name>/comments", methods=["POST"])
def post_comment(code, name):
    key  = kstr(code, name)
    u    = current_user()
    anon = u is None

    if anon:
        ok_rate, retry = rate_ok("comment_anon", key)
    else:
        ok_rate, retry = rate_ok("comment_auth", f"{key}:u{u.id}")
    if not ok_rate:
        return err(f"留言太頻繁，請等待 {retry} 秒後再試", 429, retry_after=retry)

    body = request.get_json(silent=True) or {}

    if anon:
        ip = request.remote_addr or "unknown"
        try:
            given = int(body.get("captcha_answer", -999))
        except (ValueError, TypeError):
            given = -999
        captcha_err = verify_captcha(ip, given)
        if captcha_err == "驗證碼錯誤":
            return err(captcha_err, 400)
        elif captcha_err:
            return err(captcha_err, 400, need_captcha=True)

    display_name = u.display_name if u else (body.get("user") or "匿名").strip()[:30]
    text = (body.get("text") or "").strip()[:300]

    if not text:
        return err("text is required")
    if len(text) < 2:
        return err("留言至少需要 2 個字")
    if is_spam(text):
        return err("留言內容不符合規範")

    item: dict = {
        "id":      int(time() * 1000),
        "user":    display_name,
        "text":    text,
        "ts":      int(time()),
        "likes":   0,
        "user_id": u.id if u else None,
    }
    parent_id = body.get("parent_id")
    if parent_id is not None:
        item["parent_id"] = int(parent_id)
    if anon:
        item["delete_token"] = secrets.token_hex(16)

    comments_store.setdefault(key, []).append(item)
    save_json(COMMENTS_JSON, comments_store)
    return jsonify(item), 201


@comments_bp.route("/api/food/<code>/<name>/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(code, name, comment_id):
    key = kstr(code, name)
    lst = comments_store.get(key, [])
    idx = next((i for i, c in enumerate(lst) if c.get("id") == comment_id), None)
    if idx is None:
        return err("留言不存在", 404)
    comment = lst[idx]
    u = current_user()
    if u and comment.get("user_id") == u.id:
        pass
    else:
        token = (request.get_json(silent=True) or {}).get("token", "")
        if not token or token != comment.get("delete_token"):
            return err("無權刪除", 403)
    lst.pop(idx)
    save_json(COMMENTS_JSON, comments_store)
    return jsonify({"ok": True})


@comments_bp.route("/api/food/<code>/<name>/comments/<int:comment_id>/like", methods=["POST"])
def like_comment(code, name, comment_id):
    key = kstr(code, name)
    ok_rate, retry = rate_ok("comment_like", f"{key}:{comment_id}")
    if not ok_rate:
        return err("操作太頻繁", 429, retry_after=retry)
    for c in comments_store.get(key, []):
        if c.get("id") == comment_id:
            c["likes"] = c.get("likes", 0) + 1
            save_json(COMMENTS_JSON, comments_store)
            return jsonify({"likes": c["likes"]})
    return err("留言不存在", 404)
