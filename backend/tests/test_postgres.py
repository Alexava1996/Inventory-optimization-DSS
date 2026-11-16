import concurrent.futures
import pytest
from fastapi.testclient import TestClient
from app.main import app
from conftest import HEADERS
from test_api import create


def test_concurrent_movements_cannot_oversell(logged, database):
    with database() as db:
        if db.bind.dialect.name != "postgresql":
            pytest.skip("Concurrency test requires PostgreSQL")
    p = create(logged, stock=10)
    token = logged.cookies.get("inventory_session")

    def withdraw(index):
        import uuid

        with TestClient(app, headers={**HEADERS, "Cookie": f"inventory_session={token}"}) as client:
            return client.post(
                f"/api/v1/products/{p['id']}/movements",
                json={
                    "delta": -8,
                    "reason": f"Ordine concorrente {index}",
                    "version": 1,
                    "idempotency_key": str(uuid.uuid4()),
                },
            ).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(withdraw, range(2)))
    assert sorted(statuses) == [201, 409]
    assert logged.get("/api/v1/products?year=2026").json()["items"][0]["stock"] == 2
