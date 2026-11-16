"""Comandi amministrativi locali. Nessuna registrazione pubblica."""

import argparse
import getpass
import re
import time
from sqlalchemy import delete, select
from .db import SessionLocal
from .models import LoginAttempt, Session as AuthSession, User
from .security import passwords


def main():
    parser = argparse.ArgumentParser(description="Amministrazione Inventory DSS")
    parser.add_argument("command", choices=["create-user", "reset-password", "cleanup"])
    parser.add_argument("--email")
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.command == "cleanup":
            db.execute(delete(AuthSession).where(AuthSession.expires_at <= time.time()))
            db.execute(delete(LoginAttempt).where(LoginAttempt.reset_at <= time.time()))
            db.commit()
            print("Sessioni e contatori scaduti rimossi.")
            return
        email = (args.email or input("Email: ")).strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
            parser.error("Inserisci una email valida")
        user = db.scalar(select(User).where(User.email == email))
        if args.command == "create-user" and user:
            parser.error("Account già esistente")
        if args.command == "reset-password" and not user:
            parser.error("Account non trovato")
        password = getpass.getpass("Password (almeno 12 caratteri): ")
        if not 12 <= len(password) <= 128:
            parser.error("La password deve avere da 12 a 128 caratteri")
        if password != getpass.getpass("Ripeti password: "):
            parser.error("Le password non coincidono")
        if user:
            user.password_hash = passwords.hash(password)
            db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
        else:
            db.add(User(email=email, password_hash=passwords.hash(password)))
        db.commit()
        print("Account pronto. Le password non vengono salvate in chiaro.")


if __name__ == "__main__":
    main()
