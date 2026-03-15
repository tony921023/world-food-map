from flask import Blueprint, request, jsonify
from models import User, Favorite, FavoriteList, db
from helpers import current_user, err

favorites_bp = Blueprint("favorites", __name__)


@favorites_bp.route("/api/favorites")
def get_favorites():
    u = current_user()
    if not u:
        return err("未授權", 401)
    return jsonify({"favorites": [f.to_dict() for f in Favorite.query.filter_by(user_id=u.id)]})


@favorites_bp.route("/api/favorites", methods=["POST"])
def add_favorite():
    u = current_user()
    if not u:
        return err("未授權", 401)
    body = request.get_json(silent=True) or {}
    code = (body.get("country_code") or "").upper().strip()
    name = (body.get("food_name") or "").strip()
    if not code or not name:
        return err("country_code 和 food_name 為必填")
    if Favorite.query.filter_by(user_id=u.id, country_code=code, food_name=name).first():
        return err("已收藏", 409)
    fav = Favorite(user_id=u.id, country_code=code, food_name=name)
    db.session.add(fav)
    db.session.commit()
    return jsonify(fav.to_dict()), 201


@favorites_bp.route("/api/favorites", methods=["DELETE"])
def remove_favorite():
    u = current_user()
    if not u:
        return err("未授權", 401)
    body = request.get_json(silent=True) or {}
    code = (body.get("country_code") or "").upper().strip()
    name = (body.get("food_name") or "").strip()
    fav  = Favorite.query.filter_by(user_id=u.id, country_code=code, food_name=name).first()
    if not fav:
        return err("未找到", 404)
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"ok": True})


@favorites_bp.route("/api/favorites/batch", methods=["POST"])
def batch_favorites():
    u = current_user()
    if not u:
        return err("未授權", 401)
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


@favorites_bp.route("/api/favorites/move", methods=["PUT"])
def move_favorite():
    u = current_user()
    if not u:
        return err("未授權", 401)
    body    = request.get_json(silent=True) or {}
    fav_id  = body.get("favorite_id")
    list_id = body.get("list_id")
    fav = Favorite.query.filter_by(id=fav_id, user_id=u.id).first()
    if not fav:
        return err("未找到", 404)
    if list_id is not None:
        if not FavoriteList.query.filter_by(id=list_id, user_id=u.id).first():
            return err("清單不存在", 404)
    fav.list_id = list_id
    db.session.commit()
    return jsonify(fav.to_dict())


@favorites_bp.route("/api/favorite-lists")
def get_fav_lists():
    u = current_user()
    if not u:
        return err("未授權", 401)
    lists = FavoriteList.query.filter_by(user_id=u.id).all()
    return jsonify({"lists": [{"id": l.id, "name": l.name} for l in lists]})


@favorites_bp.route("/api/favorite-lists", methods=["POST"])
def create_fav_list():
    u = current_user()
    if not u:
        return err("未授權", 401)
    name = ((request.get_json(silent=True) or {}).get("name") or "").strip()
    if not name:
        return err("name 為必填")
    fl = FavoriteList(user_id=u.id, name=name)
    db.session.add(fl)
    db.session.commit()
    return jsonify({"id": fl.id, "name": fl.name}), 201


@favorites_bp.route("/api/favorite-lists/<int:list_id>", methods=["PUT"])
def rename_fav_list(list_id):
    u = current_user()
    if not u:
        return err("未授權", 401)
    fl = FavoriteList.query.filter_by(id=list_id, user_id=u.id).first()
    if not fl:
        return err("未找到", 404)
    name = ((request.get_json(silent=True) or {}).get("name") or "").strip()
    if not name:
        return err("name 為必填")
    fl.name = name
    db.session.commit()
    return jsonify({"id": fl.id, "name": fl.name})


@favorites_bp.route("/api/favorite-lists/<int:list_id>", methods=["DELETE"])
def delete_fav_list(list_id):
    u = current_user()
    if not u:
        return err("未授權", 401)
    fl = FavoriteList.query.filter_by(id=list_id, user_id=u.id).first()
    if not fl:
        return err("未找到", 404)
    Favorite.query.filter_by(user_id=u.id, list_id=list_id).update({"list_id": None})
    db.session.delete(fl)
    db.session.commit()
    return jsonify({"ok": True})
