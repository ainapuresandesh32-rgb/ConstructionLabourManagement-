import hashlib, secrets
from fastapi import Request
from sqlalchemy.orm import Session
from .models import User

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def login_user(request: Request, user_id: int): request.session["user_id"] = user_id
def logout_user(request: Request): request.session.clear()
def current_user(request: Request, db: Session):
    uid=request.session.get("user_id")
    return db.get(User, uid) if uid else None
