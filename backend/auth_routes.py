from time import time
from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db
from helpers import make_token, current_user, set_auth_cookie, clear_auth_cookie, err
from store import comments_store

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/register", methods=["POST"])
def auth_register():
    body         = request.get_json(silent=True) or {}
    email        = (body.get("email") or "").strip().lower()
    password     = (body.get("password") or "")
    display_name = (body.get("display_name") or "").strip()
    if not email or not password or not display_name:
        return err("請填寫所有欄位")
    if len(password) < 6:
        return err("密碼至少需要 6 個字元")
    if User.query.filter_by(email=email).first():
        return err("此 Email 已被使用", 409)
    u = User(email=email, password_hash=generate_password_hash(password),
             display_name=display_name)
    db.session.add(u)
    db.session.commit()
    token = make_token(u.id)
    resp = make_response(jsonify({"token": token, "user": u.to_dict()}), 201)
    set_auth_cookie(resp, token)
    return resp


@auth_bp.route("/api/auth/login", methods=["POST"])
def auth_login():
    body     = request.get_json(silent=True) or {}
    email    = (body.get("email") or "").strip().lower()
    password = (body.get("password") or "")
    u = User.query.filter_by(email=email).first()
    if not u or not check_password_hash(u.password_hash, password):
        return err("帳號或密碼錯誤", 401)
    token = make_token(u.id)
    resp = make_response(jsonify({"token": token, "user": u.to_dict()}))
    set_auth_cookie(resp, token)
    return resp


@auth_bp.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    resp = make_response(jsonify({"ok": True}))
    clear_auth_cookie(resp)
    return resp


@auth_bp.route("/api/auth/me")
def auth_me():
    u = current_user()
    if not u:
        return err("未授權", 401)
    return jsonify({"user": u.to_dict()})


@auth_bp.route("/api/auth/profile", methods=["PUT"])
def auth_profile():
    u = current_user()
    if not u:
        return err("未授權", 401)
    body         = request.get_json(silent=True) or {}
    display_name = (body.get("display_name") or "").strip()
    if display_name:
        if len(display_name) > 30:
            return err("名稱最長 30 個字")
        u.display_name = display_name
    current_pw = body.get("current_password", "")
    new_pw     = body.get("new_password", "")
    if current_pw or new_pw:
        if not check_password_hash(u.password_hash, current_pw):
            return err("目前密碼不正確")
        if len(new_pw) < 6:
            return err("新密碼至少需要 6 個字元")
        u.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return jsonify({"user": u.to_dict()})


@auth_bp.route("/api/auth/my-comments")
def auth_my_comments():
    u = current_user()
    if not u:
        return err("未授權", 401)
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
