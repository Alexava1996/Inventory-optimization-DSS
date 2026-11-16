import hashlib
import secrets
import time
from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import get_db
from .models import LoginAttempt, Session as AuthSession, User

passwords = PasswordHash.recommended()
DUMMY_HASH = passwords.hash(secrets.token_urlsafe(32))
COOKIE = "inventory_session"


def token_hash(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE, "")
    session = db.get(AuthSession, token_hash(token)) if token and len(token) < 256 else None
    if session is None or session.expires_at <= time.time():
        raise HTTPException(401, "Accedi per continuare")
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(401, "Sessione non valida")
    return user


def throttle(db: Session, identifier: str, limit: int):
    """Contatore persistente e atomico, condiviso da tutti i processi API."""
    key = token_hash(identifier)
    now = time.time()
    for _ in range(3):
        db.execute(delete(LoginAttempt).where(LoginAttempt.key == key, LoginAttempt.reset_at <= now))
        result = db.execute(update(LoginAttempt).where(LoginAttempt.key == key).values(count=LoginAttempt.count + 1))
        if result.rowcount == 0:
            db.add(LoginAttempt(key=key, count=1, reset_at=now + 900))
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
    attempt = db.scalar(select(LoginAttempt).where(LoginAttempt.key == key))
    if attempt is None or attempt.count > limit:
        raise HTTPException(429, "Troppi tentativi. Riprova tra 15 minuti.", headers={"Retry-After": "900"})
