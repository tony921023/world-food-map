from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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
