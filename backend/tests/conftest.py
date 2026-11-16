import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.main import app
from app.models import User
from app.security import passwords

HEADERS = {"Origin": "http://localhost:3000", "X-CSRF-Protection": "1"}
PASSWORD = "Test-only-passphrase-123!"


@pytest.fixture
def database():
    url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    if not url.startswith("sqlite") and not url.split("?")[0].endswith("_test"):
        raise ValueError("TEST_DATABASE_URL deve puntare a un database dedicato con suffisso _test")
    options = (
        {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    )
    engine = create_engine(url, **options)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)

    def override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override
    with factory() as db:
        db.add_all(
            [
                User(email="first@example.test", password_hash=passwords.hash(PASSWORD)),
                User(email="second@example.test", password_hash=passwords.hash(PASSWORD)),
            ]
        )
        db.commit()
    yield factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(database):
    with TestClient(app, headers=HEADERS) as client:
        yield client


@pytest.fixture
def logged(client):
    assert (
        client.post("/api/v1/auth/login", json={"email": "first@example.test", "password": PASSWORD}).status_code == 200
    )
    return client
