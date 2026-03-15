from __future__ import annotations
import os
from time import time
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text as _text

from config import CORS_ORIGIN
from models import db
from auth_routes import auth_bp
from favorites_routes import favorites_bp
from foods_routes import foods_bp
from comments_routes import comments_bp
from search_routes import search_bp

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["JSON_AS_ASCII"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql://webfinal:webfinal@localhost:5433/webfinal"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app, resources={r"/api/*": {"origins": CORS_ORIGIN}}, supports_credentials=True)

db.init_app(app)

with app.app_context():
    db.create_all()
    with db.engine.connect() as conn:
        conn.execute(_text(
            "ALTER TABLE favorites ADD COLUMN IF NOT EXISTS "
            "list_id INTEGER REFERENCES favorite_lists(id) ON DELETE SET NULL"
        ))
        conn.commit()

app.register_blueprint(auth_bp)
app.register_blueprint(favorites_bp)
app.register_blueprint(foods_bp)
app.register_blueprint(comments_bp)
app.register_blueprint(search_bp)


@app.route("/api/ping")
def ping():
    return jsonify({"ok": True, "ts": int(time())})


@app.route("/api/_reload", methods=["POST"])
def force_reload():
    from store import load_foods_json
    load_foods_json(force=True)
    return jsonify({"reloaded": True})


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")
    app.run(host="127.0.0.1", port=5000, debug=debug)
