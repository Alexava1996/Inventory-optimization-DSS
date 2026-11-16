import json
import time
import uuid
from pathlib import Path
import pytest
from sqlalchemy import select
from app.models import Session as AuthSession
from conftest import PASSWORD


def create(client, sku="TEST-001", stock=20, name="Articolo prova"):
    r = client.post("/api/v1/products", json={"sku": sku, "name": name, "stock": stock})
    assert r.status_code == 201, r.text
    return r.json()


def observation(client, p, version=0, **changes):
    data = dict(annual_demand=3650, order_cost=50, holding_cost=5, lead_time_days=7, safety_stock=None, version=version)
    data.update(changes)
    return client.put(f"/api/v1/products/{p['id']}/observations/2026", json=data)


def movement(client, p, delta, key=None, **changes):
    data = dict(
        delta=delta, reason="Movimento di prova", version=p["version"], idempotency_key=key or str(uuid.uuid4())
    )
    data.update(changes)
    return client.post(f"/api/v1/products/{p['id']}/movements", json=data)


def test_auth_revocation_and_csrf(client, database):
    assert client.get("/api/v1/products?year=2026").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "first@example.test", "password": PASSWORD},
            headers={"Origin": "https://evil.test"},
        ).status_code
        == 403
    )
    assert (
        client.post("/api/v1/auth/login", json={"email": "first@example.test", "password": "wrong"}).status_code == 401
    )
    r = client.post("/api/v1/auth/login", json={"email": "first@example.test", "password": PASSWORD})
    assert r.status_code == 200 and "HttpOnly" in r.headers["set-cookie"] and "SameSite=lax" in r.headers["set-cookie"]
    token = client.cookies.get("inventory_session")
    with database() as db:
        session = db.scalar(select(AuthSession))
        assert session.token_hash != token and len(session.token_hash) == 64
    assert client.post("/api/v1/auth/logout").status_code == 204
    client.cookies.set("inventory_session", token)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_session_expiry(logged, database):
    with database() as db:
        session = db.scalar(select(AuthSession))
        session.expires_at = time.time() - 1
        db.commit()
    assert logged.get("/api/v1/auth/me").status_code == 401


def test_login_rate_limit(client):
    for _ in range(10):
        assert (
            client.post("/api/v1/auth/login", json={"email": "absent@example.test", "password": "no"}).status_code
            == 401
        )
    r = client.post("/api/v1/auth/login", json={"email": "absent@example.test", "password": "no"})
    assert r.status_code == 429 and r.headers["retry-after"] == "900"


def test_forecast_versions_seasonality_and_missing_year(logged):
    p = create(logged)
    r = observation(logged, p)
    assert r.status_code == 200 and r.json()["forecast"]["punto_riordino"] == 140
    assert r.json()["needs_reorder"] is True
    assert observation(logged, p).status_code == 409
    assert observation(logged, p, version=1, lead_time_days=8).status_code == 200
    assert observation(logged, p, version=1).status_code == 409
    result = logged.get("/api/v1/products?year=2026&factor=2").json()["items"][0]
    assert result["forecast"]["punto_riordino"] == 320
    assert result["observation"]["annual_demand"] == 3650
    assert logged.get("/api/v1/products?year=2027").json()["items"][0]["forecast"] is None


def test_tenant_isolation_on_all_resources(logged):
    p = create(logged)
    observation(logged, p)
    logged.post("/api/v1/auth/login", json={"email": "second@example.test", "password": PASSWORD})
    assert logged.get("/api/v1/products?year=2026").json()["total"] == 0
    assert logged.get("/api/v1/export/legacy").json() == {}
    assert "Articolo prova" not in logged.get("/api/v1/export/csv?year=2026").text
    assert logged.get(f"/api/v1/products/{p['id']}/observations").status_code == 404
    assert logged.get(f"/api/v1/products/{p['id']}/movements").status_code == 404
    assert observation(logged, p).status_code == 404
    assert movement(logged, p, 2).status_code == 404
    assert (
        logged.patch(f"/api/v1/products/{p['id']}", json={"name": "Stolen", "archived": True, "version": 1}).status_code
        == 404
    )
    assert create(logged)["sku"] == p["sku"]


def test_movement_idempotency_negative_stock_and_conflicts(logged):
    p = create(logged, stock=10)
    key = str(uuid.uuid4())
    r = movement(logged, p, -4, key)
    assert r.status_code == 201 and r.json()["stock"] == 6
    assert movement(logged, p, -4, key).json()["replayed"] is True
    assert movement(logged, p, -3, key).status_code == 409
    assert movement(logged, p, 1).status_code == 409
    p["version"] = 2
    assert movement(logged, p, -7).status_code == 409
    assert movement(logged, p, -6).json()["stock"] == 0
    history = logged.get(f"/api/v1/products/{p['id']}/movements").json()
    assert len(history) == 3 and history[0]["resulting_stock"] == 0


def test_archiving_is_reversible_and_preserves_history(logged):
    p = create(logged)
    observation(logged, p)
    path = f"/api/v1/products/{p['id']}"
    assert logged.patch(path, json={"name": p["name"], "archived": True, "version": 1}).status_code == 200
    assert logged.get("/api/v1/products?year=2026").json()["total"] == 0
    assert len(logged.get(path + "/observations").json()) == 1
    assert logged.get("/api/v1/products?year=2026&archived=true").json()["total"] == 1
    assert movement(logged, {**p, "version": 2}, 2).status_code == 409
    assert logged.patch(path, json={"name": p["name"], "archived": False, "version": 2}).status_code == 200
    assert logged.get("/api/v1/products?year=2026").json()["total"] == 1


def test_legacy_import_is_atomic_and_stock_unknown(logged):
    data = json.loads((Path(__file__).resolve().parents[2] / "Dizionario.txt").read_text())
    assert logged.post("/api/v1/import/legacy", json=data).json()["observations"] == 6
    p = logged.get("/api/v1/products?year=2026").json()["items"][0]
    assert p["stock_known"] is False and p["needs_reorder"] is False
    duplicate = {"NEW-SKU": data["IPH"], **data}
    assert logged.post("/api/v1/import/legacy", json=duplicate).status_code == 409
    assert logged.get("/api/v1/products?year=2026").json()["total"] == 2
    assert logged.post("/api/v1/import/legacy", json={"bad code": data["IPH"]}).status_code == 422
    assert logged.get("/api/v1/export/legacy").json() == data
    assert movement(logged, p, 0).status_code == 201
    assert logged.get("/api/v1/products?year=2026").json()["items"][0]["stock_known"] is True


@pytest.mark.parametrize(
    "changes",
    [{"stock": -1}, {"stock": 1.2}, {"stock": True}, {"sku": "space code"}, {"name": " "}, {"extra": "unknown"}],
)
def test_product_validation(logged, changes):
    data = {"sku": "TEST", "name": "Name", "stock": 0, **changes}
    assert logged.post("/api/v1/products", json=data).status_code == 422


@pytest.mark.parametrize(
    "changes",
    [{"holding_cost": 0}, {"annual_demand": -1}, {"lead_time_days": 1.5}, {"safety_stock": -1}, {"order_cost": True}],
)
def test_forecast_validation(logged, changes):
    p = create(logged)
    assert observation(logged, p, **changes).status_code == 422


def test_filter_pagination_and_csv_formula_safety(logged):
    create(logged, "SKU_1", name='=HYPERLINK("evil")')
    create(logged, "SKU-2")
    assert logged.get("/api/v1/products?year=2026&limit=1&offset=1").json()["total"] == 2
    assert logged.get("/api/v1/products?year=2026&q=_").json()["total"] == 1
    assert logged.get("/api/v1/products?year=2026&q=%25").json()["total"] == 0
    assert "'=HYPERLINK" in logged.get("/api/v1/export/csv?year=2026").text
    assert logged.get("/api/v1/products?year=2026&factor=nan").status_code == 422
    assert logged.post("/api/v1/auth/login", content="x" * 1_048_577).status_code == 413


def test_errors_do_not_echo_password_or_database(logged):
    r = logged.post("/api/v1/auth/login", json={"email": "name", "password": "PRIVATE", "unexpected": "PRIVATE"})
    assert r.status_code == 422 and "PRIVATE" not in r.text
    create(logged)
    r = logged.post("/api/v1/products", json={"sku": "TEST-001", "name": "Other", "stock": 0})
    assert r.status_code == 409 and "INSERT" not in r.text and "sqlalchemy" not in r.text
