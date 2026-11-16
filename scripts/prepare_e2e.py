"""Create a disposable account in a CI / E2E database. Never run on production."""
import os
from app.config import settings
from app.db import SessionLocal
from app.models import User
from app.security import passwords

if settings().app_env != 'test':
    raise SystemExit('APP_ENV=test richiesto')
with SessionLocal() as db:
    db.add(User(email=os.environ['E2E_EMAIL'], password_hash=passwords.hash(os.environ['E2E_PASSWORD'])))
    db.commit()
print('Account E2E creato.')
